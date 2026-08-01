"""
Бизнес-логика бронирования (п. 6.1 ТЗ).

Поток: поиск в Shelter → расчёт стоимости → создание брони → оплата
FreedomPay → запись брони в Shelter → письма гостю и администратору.
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.booking.integrations.freedompay import (
    FreedomPayError,
    calculate_prepay_amount,
    get_freedompay_client,
)
from apps.booking.integrations.shelter import ShelterError, get_shelter_client
from apps.booking.models import Addon, Booking, BookingAddon, Payment
from apps.offers.models import PromoCode
from apps.rooms.models import RoomCategory

logger = logging.getLogger('baitur.booking')

MAX_NIGHTS = 60
MAX_BOOKING_HORIZON_DAYS = 540


class BookingError(Exception):
    """Ошибка сценария бронирования, которую можно показать гостю."""


# =============================================================================
# ПОИСК ДОСТУПНОСТИ
# =============================================================================

@dataclass
class SearchResult:
    """Категория сайта, сопоставленная с наличием из Shelter."""

    category: RoomCategory
    available_rooms: int
    price_per_night: Decimal
    total_price: Decimal
    currency: str = 'KGS'


def validate_search(check_in, check_out, adults, children):
    """Проверяет параметры поиска. Бросает BookingError с текстом для гостя."""
    today = timezone.localdate()

    if not check_in or not check_out:
        raise BookingError(_('Укажите даты заезда и выезда.'))
    if check_in < today:
        raise BookingError(_('Дата заезда не может быть в прошлом.'))
    if check_out <= check_in:
        raise BookingError(_('Дата выезда должна быть позже даты заезда.'))
    if (check_out - check_in).days > MAX_NIGHTS:
        raise BookingError(_('Максимальный срок бронирования — %(n)s ночей.') % {'n': MAX_NIGHTS})
    if check_in > today + timedelta(days=MAX_BOOKING_HORIZON_DAYS):
        raise BookingError(_('Бронирование открыто не более чем на 18 месяцев вперёд.'))
    if adults < 1:
        raise BookingError(_('Укажите хотя бы одного взрослого гостя.'))
    if children < 0:
        raise BookingError(_('Некорректное количество детей.'))


def search_availability(check_in, check_out, adults=2, children=0):
    """
    Возвращает список SearchResult. Источник наличия — Shelter (п. 6.2 ТЗ):
    сайт не ведёт собственный учёт номеров.
    """
    validate_search(check_in, check_out, adults, children)

    client = get_shelter_client()
    try:
        availability = client.get_availability(check_in, check_out, adults, children)
    except ShelterError as exc:
        logger.error('Не удалось получить наличие из Shelter: %s', exc)
        raise BookingError(str(exc)) from exc

    by_code = {row.code: row for row in availability if row.code}
    nights = (check_out - check_in).days
    guests = adults + children

    results = []
    categories = RoomCategory.objects.filter(
        is_active=True, is_bookable=True,
    ).prefetch_related('amenities', 'images')

    for category in categories:
        if category.max_guests < guests:
            continue

        row = by_code.get(category.shelter_code) or by_code.get(category.slug)
        if row is None:
            # Категории нет в ответе PMS — считаем, что на эти даты её не продают.
            continue

        results.append(SearchResult(
            category=category,
            available_rooms=row.available_rooms,
            price_per_night=row.price_per_night or category.base_price,
            total_price=row.total_price or (category.base_price * nights),
            currency=row.currency,
        ))

    return results


def get_search_result(category, check_in, check_out, adults, children):
    """Наличие по одной конкретной категории."""
    for result in search_availability(check_in, check_out, adults, children):
        if result.category.pk == category.pk:
            return result
    raise BookingError(_('На выбранные даты этот номер недоступен.'))


# =============================================================================
# РАСЧЁТ СТОИМОСТИ
# =============================================================================

@dataclass
class Quote:
    category: RoomCategory
    check_in: object
    check_out: object
    adults: int
    children: int
    rooms_count: int
    nights: int
    price_per_night: Decimal
    room_total: Decimal
    addons_total: Decimal = Decimal('0')
    discount_amount: Decimal = Decimal('0')
    total_amount: Decimal = Decimal('0')
    prepay_amount: Decimal = Decimal('0')
    currency: str = 'KGS'
    promo_code: object = None
    promo_error: str = ''
    addon_items: list = field(default_factory=list)


def build_quote(*, category, check_in, check_out, adults, children,
                rooms_count=1, addons=None, promo_code=None):
    """Считает стоимость брони: проживание + допуслуги − скидка."""
    result = get_search_result(category, check_in, check_out, adults, children)

    if rooms_count < 1:
        raise BookingError(_('Укажите количество номеров.'))
    if result.available_rooms < rooms_count:
        raise BookingError(
            _('На выбранные даты свободно номеров: %(n)s.') % {'n': result.available_rooms},
        )

    nights = (check_out - check_in).days
    guests = adults + children
    room_total = (result.total_price * rooms_count).quantize(Decimal('0.01'))

    quote = Quote(
        category=category,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        rooms_count=rooms_count,
        nights=nights,
        price_per_night=result.price_per_night,
        room_total=room_total,
        currency=result.currency,
    )

    # Допродажи: трансфер, завтрак, SPA (п. 5.6 ТЗ)
    for addon, quantity in (addons or []):
        total = addon.calculate_total(quantity=quantity, nights=nights, guests=guests)
        quote.addon_items.append({'addon': addon, 'quantity': quantity, 'total': total})
        quote.addons_total += total

    subtotal = quote.room_total + quote.addons_total

    # Промокод
    if promo_code:
        ok, error = promo_code.check_availability(
            amount=subtotal, nights=nights, room_category=category,
        )
        if ok:
            quote.promo_code = promo_code
            quote.discount_amount = promo_code.calculate_discount(subtotal)
        else:
            quote.promo_error = str(error)

    quote.total_amount = max(subtotal - quote.discount_amount, Decimal('0')).quantize(Decimal('0.01'))
    quote.prepay_amount = calculate_prepay_amount(quote.total_amount)
    return quote


def resolve_promo_code(code):
    """Ищет активный промокод по строке. Возвращает объект или None."""
    if not code:
        return None
    return PromoCode.objects.filter(code=code.strip().upper(), is_active=True).first()


def resolve_addons(addon_ids):
    """Преобразует список ID в пары (Addon, quantity=1)."""
    if not addon_ids:
        return []
    addons = Addon.objects.filter(pk__in=addon_ids, is_active=True)
    return [(addon, 1) for addon in addons]


# =============================================================================
# СОЗДАНИЕ БРОНИ
# =============================================================================

@transaction.atomic
def create_booking(*, quote, guest, language='ru', ip_address=None):
    """Создаёт бронь в статусе «ожидает оплаты». В Shelter пока не пишем."""
    booking = Booking.objects.create(
        status=Booking.Status.AWAITING_PAYMENT,
        room_category=quote.category,
        rooms_count=quote.rooms_count,
        check_in=quote.check_in,
        check_out=quote.check_out,
        adults=quote.adults,
        children=quote.children,
        children_ages=guest.get('children_ages', ''),
        guest_first_name=guest['first_name'],
        guest_last_name=guest.get('last_name', ''),
        guest_phone=guest['phone'],
        guest_email=guest['email'],
        guest_country=guest.get('country', ''),
        comment=guest.get('comment', ''),
        currency=quote.currency,
        room_total=quote.room_total,
        addons_total=quote.addons_total,
        discount_amount=quote.discount_amount,
        total_amount=quote.total_amount,
        prepay_amount=quote.prepay_amount,
        promo_code=quote.promo_code,
        language=language,
        ip_address=ip_address,
    )

    for item in quote.addon_items:
        BookingAddon.objects.create(
            booking=booking,
            addon=item['addon'],
            quantity=item['quantity'],
            price=item['addon'].price,
            total=item['total'],
        )

    if quote.promo_code:
        PromoCode.objects.filter(pk=quote.promo_code.pk).update(used_count=F('used_count') + 1)

    return booking


# =============================================================================
# ОПЛАТА
# =============================================================================

def start_payment(booking, request):
    """
    Создаёт платёж в FreedomPay и возвращает URL, куда нужно отправить гостя.

    Если оплата отключена (нет договора эквайринга), бронь остаётся в статусе
    «ожидает оплаты» и обрабатывается менеджером вручную.
    """
    if not settings.FREEDOMPAY['ENABLED']:
        logger.warning('FreedomPay выключен: бронь %s ждёт ручного подтверждения.', booking.number)
        return None

    amount = booking.prepay_amount or booking.total_amount
    payment = Payment.objects.create(
        booking=booking,
        order_id=booking.number,
        amount=amount,
        currency=booking.currency,
        status=Payment.Status.CREATED,
    )

    base = request.build_absolute_uri('/').rstrip('/') if request else settings.SITE_URL
    client = get_freedompay_client()

    try:
        result = client.init_payment(
            order_id=payment.order_id,
            amount=amount,
            description=_('Бронирование %(number)s, Baytur Resort & Spa') % {'number': booking.number},
            success_url=f'{base}{reverse("booking:payment_success", args=[booking.number])}',
            failure_url=f'{base}{reverse("booking:payment_failure", args=[booking.number])}',
            result_url=f'{base}{reverse("booking:payment_result")}',
            phone=booking.guest_phone,
            email=booking.guest_email,
            language=booking.language or 'ru',
        )
    except FreedomPayError as exc:
        payment.status = Payment.Status.FAILED
        payment.error_message = str(exc)[:500]
        payment.save(update_fields=['status', 'error_message', 'updated_at'])
        raise BookingError(str(exc)) from exc

    payment.external_id = result['payment_id']
    payment.payment_url = result['redirect_url']
    payment.request_data = result['request']
    payment.response_data = result['raw']
    payment.status = Payment.Status.PENDING
    payment.save()

    return payment.payment_url


@transaction.atomic
def handle_successful_payment(payment, callback_data=None):
    """
    Колбэк об успешной оплате: фиксируем платёж, пишем бронь в Shelter,
    уведомляем гостя и администратора (п. 6.1 ТЗ, шаги 6–7).
    """
    from apps.booking.notifications import notify_booking_confirmed

    if payment.status == Payment.Status.SUCCESS:
        return payment.booking  # повторный колбэк — обрабатываем идемпотентно

    payment.status = Payment.Status.SUCCESS
    payment.paid_at = timezone.now()
    payment.callback_data = callback_data
    payment.save()

    booking = payment.booking
    booking.paid_amount = payment.amount
    booking.status = Booking.Status.PAID
    booking.save(update_fields=['paid_amount', 'status', 'updated_at'])

    push_booking_to_shelter(booking)
    notify_booking_confirmed(booking)
    return booking


def handle_failed_payment(payment, callback_data=None, message=''):
    """Оплата не прошла — номер остаётся свободным, гостю предлагаем повтор (п. 6.3 ТЗ)."""
    payment.status = Payment.Status.FAILED
    payment.callback_data = callback_data
    payment.error_message = message[:500]
    payment.save()

    booking = payment.booking
    if not booking.is_paid:
        booking.status = Booking.Status.PAYMENT_FAILED
        booking.save(update_fields=['status', 'updated_at'])
    return booking


def push_booking_to_shelter(booking):
    """
    Записывает оплаченную бронь в PMS. Ошибка здесь не отменяет оплату:
    бронь остаётся в статусе «оплачена» с текстом ошибки, чтобы менеджер
    завёл её вручную и деньги гостя не потерялись.
    """
    from apps.booking.notifications import notify_shelter_sync_failed

    client = get_shelter_client()
    try:
        reservation_id = client.create_reservation(booking)
    except ShelterError as exc:
        logger.error('Бронь %s оплачена, но не записана в Shelter: %s', booking.number, exc)
        booking.shelter_error = str(exc)[:1000]
        booking.save(update_fields=['shelter_error', 'updated_at'])
        notify_shelter_sync_failed(booking)
        return False

    booking.shelter_reservation_id = reservation_id
    booking.shelter_synced_at = timezone.now()
    booking.shelter_error = ''
    booking.status = Booking.Status.CONFIRMED
    booking.confirmed_at = timezone.now()
    booking.save(update_fields=[
        'shelter_reservation_id', 'shelter_synced_at', 'shelter_error',
        'status', 'confirmed_at', 'updated_at',
    ])
    return True
