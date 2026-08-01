"""
Интеграция с PMS Shelter (п. 5.2 и 6.2 ТЗ).

Единый источник наличия и цен — Shelter. Сайт не ведёт параллельный учёт
номеров: при каждом запросе доступности мы спрашиваем PMS, а подтверждённые
(оплаченные) брони записываем обратно.

ВАЖНО: точные URL эндпоинтов и формат полей нужно сверить с документацией
Shelter — её предоставляет команда Shelter (контакт по ТЗ: директор Shelter).
Всё, что зависит от их контракта, вынесено в методы `_parse_*` и константы
`ENDPOINT_*`, чтобы правка была точечной.

Пока `SHELTER_ENABLED=0`, работает локальный резервный расчёт наличия
(LocalAvailabilityClient) — по данным сайта. Это режим разработки и аварийный
режим: реальные продажи должны идти только при включённом Shelter.
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('baitur.shelter')


class ShelterError(Exception):
    """Ошибка обращения к PMS Shelter."""


@dataclass
class RoomAvailability:
    """Доступность одной категории номеров на выбранные даты."""

    code: str
    available_rooms: int
    price_per_night: Decimal
    total_price: Decimal
    currency: str = 'KGS'
    name: str = ''
    rate_plan: str = ''
    extra: dict = field(default_factory=dict)

    @property
    def is_available(self):
        return self.available_rooms > 0


class BaseShelterClient:
    """Контракт, на который опирается сайт. Меняется источник — не логика сайта."""

    def get_availability(self, check_in: date, check_out: date, adults: int = 2, children: int = 0):
        raise NotImplementedError

    def create_reservation(self, booking):
        raise NotImplementedError

    def cancel_reservation(self, reservation_id: str):
        raise NotImplementedError


class ShelterClient(BaseShelterClient):
    """HTTP-клиент Shelter."""

    ENDPOINT_AVAILABILITY = '/api/availability'
    ENDPOINT_RESERVATION = '/api/reservations'

    def __init__(self, config=None):
        config = config or settings.SHELTER
        self.base_url = config['BASE_URL']
        self.api_key = config['API_KEY']
        self.hotel_id = config['HOTEL_ID']
        self.timeout = config['TIMEOUT']

        if not self.base_url or not self.api_key:
            raise ShelterError(_('Не заданы SHELTER_BASE_URL / SHELTER_API_KEY.'))

    # ------------------------------------------------------------------ HTTP

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _request(self, method, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.request(
                method, url, headers=self._headers(), timeout=self.timeout, **kwargs,
            )
        except requests.RequestException as exc:
            logger.error('Shelter %s %s — сеть недоступна: %s', method, url, exc)
            raise ShelterError(_('PMS Shelter недоступна. Попробуйте позже.')) from exc

        if response.status_code >= 400:
            logger.error('Shelter %s %s — HTTP %s: %s', method, url, response.status_code, response.text[:500])
            raise ShelterError(_('PMS Shelter вернула ошибку %(code)s.') % {'code': response.status_code})

        try:
            return response.json()
        except ValueError as exc:
            logger.error('Shelter %s %s — ответ не JSON: %s', method, url, response.text[:500])
            raise ShelterError(_('Некорректный ответ PMS Shelter.')) from exc

    # ------------------------------------------------------------- Доступность

    def get_availability(self, check_in, check_out, adults=2, children=0):
        payload = {
            'hotel_id': self.hotel_id,
            'date_from': check_in.isoformat(),
            'date_to': check_out.isoformat(),
            'adults': adults,
            'children': children,
        }
        data = self._request('GET', self.ENDPOINT_AVAILABILITY, params=payload)
        return self._parse_availability(data, nights=(check_out - check_in).days)

    def _parse_availability(self, data, nights):
        """Разбор ответа Shelter. Правится под фактический формат их API."""
        rows = data.get('rooms') or data.get('data') or []
        result = []
        for row in rows:
            price_per_night = Decimal(str(row.get('price') or row.get('rate') or 0))
            total = row.get('total_price')
            total_price = Decimal(str(total)) if total is not None else price_per_night * nights
            result.append(RoomAvailability(
                code=str(row.get('code') or row.get('room_type_code') or ''),
                name=row.get('name', ''),
                available_rooms=int(row.get('available') or row.get('rooms_available') or 0),
                price_per_night=price_per_night,
                total_price=total_price,
                currency=row.get('currency', 'KGS'),
                rate_plan=str(row.get('rate_plan') or ''),
                extra=row,
            ))
        return result

    # ---------------------------------------------------------------- Брони

    def create_reservation(self, booking):
        """Записывает оплаченную бронь в Shelter. Возвращает ID брони в PMS."""
        payload = {
            'hotel_id': self.hotel_id,
            'external_id': booking.number,
            'room_type_code': booking.shelter_room_code,
            'rooms': booking.rooms_count,
            'date_from': booking.check_in.isoformat(),
            'date_to': booking.check_out.isoformat(),
            'adults': booking.adults,
            'children': booking.children,
            'guest': {
                'first_name': booking.guest_first_name,
                'last_name': booking.guest_last_name,
                'phone': booking.guest_phone,
                'email': booking.guest_email,
                'country': booking.guest_country,
            },
            'total_amount': str(booking.total_amount),
            'paid_amount': str(booking.paid_amount),
            'currency': booking.currency,
            'comment': booking.comment,
            'source': 'website',
        }
        data = self._request('POST', self.ENDPOINT_RESERVATION, json=payload)
        reservation_id = data.get('reservation_id') or data.get('id')
        if not reservation_id:
            raise ShelterError(_('Shelter не вернула идентификатор брони.'))
        return str(reservation_id)

    def cancel_reservation(self, reservation_id):
        self._request('DELETE', f'{self.ENDPOINT_RESERVATION}/{reservation_id}')
        return True


class LocalAvailabilityClient(BaseShelterClient):
    """
    Резервный расчёт наличия по данным сайта — работает, пока Shelter выключена.

    Считает свободные номера как `total_rooms` категории минус пересекающиеся
    по датам оплаченные/подтверждённые брони. Цена берётся из `base_price`.
    """

    def get_availability(self, check_in, check_out, adults=2, children=0):
        from apps.booking.models import Booking
        from apps.rooms.models import RoomCategory

        nights = max((check_out - check_in).days, 1)
        guests = adults + children
        result = []

        categories = RoomCategory.objects.filter(is_active=True, is_bookable=True)
        for category in categories:
            if category.max_guests < guests:
                continue

            booked = Booking.objects.filter(
                room_category=category,
                status__in=(
                    Booking.Status.AWAITING_PAYMENT,
                    Booking.Status.PAID,
                    Booking.Status.CONFIRMED,
                ),
                check_in__lt=check_out,
                check_out__gt=check_in,
            ).aggregate(total=Sum('rooms_count'))['total'] or 0

            available = max(category.total_rooms - booked, 0)
            result.append(RoomAvailability(
                code=category.shelter_code or category.slug,
                name=str(category.name),
                available_rooms=available,
                price_per_night=category.base_price,
                total_price=category.base_price * nights,
                currency='KGS',
            ))
        return result

    def create_reservation(self, booking):
        """Локально брони в PMS не создаём — возвращаем пустой ID."""
        logger.warning(
            'Shelter выключена: бронь %s не записана в PMS, требуется ручной ввод на ресепшене.',
            booking.number,
        )
        return ''

    def cancel_reservation(self, reservation_id):
        return True


def get_shelter_client():
    """Клиент по текущим настройкам: реальная PMS или локальный резерв."""
    if settings.SHELTER['ENABLED']:
        return ShelterClient()
    return LocalAvailabilityClient()
