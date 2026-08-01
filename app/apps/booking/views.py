"""
Вьюхи модуля бронирования (п. 5.1 и 6.1 ТЗ).

Состояние между шагами не храним в сессии: параметры поиска идут в query
string, а цена и наличие пересчитываются из Shelter на каждом шаге. Так гость
не сможет оплатить устаревшую цену или занятый номер.
"""

import logging

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, TemplateView

from apps.base.seo import SEOMixin
from apps.booking.forms import AvailabilitySearchForm, BookingGuestForm
from apps.booking.integrations.freedompay import FreedomPayClient, verify_signature
from apps.booking.models import Addon, Booking, Payment
from apps.booking.services import (
    BookingError,
    build_quote,
    create_booking,
    handle_failed_payment,
    handle_successful_payment,
    resolve_addons,
    resolve_promo_code,
    search_availability,
    start_payment,
)
from apps.rooms.models import RoomCategory
from django.conf import settings

logger = logging.getLogger('baitur.booking')


def _search_params(request):
    """Разбирает параметры поиска из query string."""
    form = AvailabilitySearchForm(request.GET or None)
    if not request.GET or not form.is_valid():
        return form, None
    return form, form.cleaned_data


class BookingSearchView(SEOMixin, TemplateView):
    """Шаг 1–3: выбор дат → список доступных категорий с ценами из Shelter."""

    template_name = 'pages/booking/search.html'
    meta_title = _('Бронирование номера — Baytur Resort & Spa')
    meta_description = _('Онлайн-бронирование номеров Baytur Resort & Spa: выберите даты, '
                         'категорию и оплатите картой. Подтверждение приходит на e-mail.')
    meta_robots = 'noindex, follow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form, params = _search_params(self.request)
        context['search_form'] = form
        context['addons'] = Addon.objects.filter(is_active=True)

        if params:
            try:
                context['results'] = search_availability(
                    params['check_in'], params['check_out'],
                    params['adults'], params['children'],
                )
                context['params'] = params
            except BookingError as exc:
                context['search_error'] = str(exc)
        return context


class BookingCheckoutView(SEOMixin, View):
    """Шаг 4–5: данные гостя, пересчёт цены и переход к оплате."""

    template_name = 'pages/booking/checkout.html'
    meta_robots = 'noindex, nofollow'

    def get_category(self, slug):
        return get_object_or_404(RoomCategory, slug=slug, is_active=True, is_bookable=True)

    def build(self, request, category):
        """Собирает расчёт стоимости из параметров запроса."""
        source = request.POST if request.method == 'POST' else request.GET
        form = AvailabilitySearchForm(source)
        if not form.is_valid():
            raise BookingError(_('Проверьте даты и количество гостей.'))

        data = form.cleaned_data
        rooms_count = int(source.get('rooms_count') or 1)
        addon_ids = source.getlist('addons')
        promo = resolve_promo_code(source.get('promo_code'))

        quote = build_quote(
            category=category,
            check_in=data['check_in'],
            check_out=data['check_out'],
            adults=data['adults'],
            children=data['children'],
            rooms_count=rooms_count,
            addons=resolve_addons(addon_ids),
            promo_code=promo,
        )
        return form, quote

    def render_page(self, request, category, form, quote, guest_form, error=''):
        context = {
            'category': category,
            'search_form': form,
            'quote': quote,
            'form': guest_form,
            'addons': Addon.objects.filter(is_active=True),
            'error': error,
            'meta': None,
        }
        # SEOMixin рассчитан на CBV с get_context_data — здесь мета проще задать явно
        from apps.base.seo import PageMeta
        context['meta'] = PageMeta(
            title=str(_('Оформление брони — %(name)s')) % {'name': category.name},
            robots=self.meta_robots,
            canonical=request.build_absolute_uri(request.path),
        )
        return render(request, self.template_name, context)

    def get(self, request, slug):
        category = self.get_category(slug)
        try:
            form, quote = self.build(request, category)
        except BookingError as exc:
            messages.error(request, str(exc))
            return redirect('booking:search')
        return self.render_page(request, category, form, quote, BookingGuestForm())

    def post(self, request, slug):
        category = self.get_category(slug)

        try:
            form, quote = self.build(request, category)
        except BookingError as exc:
            messages.error(request, str(exc))
            return redirect('booking:search')

        guest_form = BookingGuestForm(request.POST)
        if not guest_form.is_valid():
            return self.render_page(request, category, form, quote, guest_form)

        booking = create_booking(
            quote=quote,
            guest=guest_form.guest_data(),
            language=request.LANGUAGE_CODE,
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        try:
            payment_url = start_payment(booking, request)
        except BookingError as exc:
            messages.error(request, str(exc))
            return redirect('booking:detail', number=booking.number)

        if payment_url:
            return redirect(payment_url)

        # Оплата отключена — бронь принята как заявка, менеджер подтвердит вручную
        messages.info(request, _('Бронь принята. Менеджер свяжется с вами для подтверждения оплаты.'))
        return redirect('booking:detail', number=booking.number)


class BookingDetailView(SEOMixin, DetailView):
    """Статус брони по её номеру — ссылка отправляется гостю на e-mail."""

    model = Booking
    template_name = 'pages/booking/detail.html'
    context_object_name = 'booking'
    slug_field = 'number'
    slug_url_kwarg = 'number'
    meta_robots = 'noindex, nofollow'

    def get_meta_object(self):
        return None


class PaymentSuccessView(SEOMixin, DetailView):
    """
    Страница возврата после оплаты. Носит информационный характер:
    подтверждением считается только серверный колбэк FreedomPay.
    """

    model = Booking
    template_name = 'pages/booking/success.html'
    context_object_name = 'booking'
    slug_field = 'number'
    slug_url_kwarg = 'number'
    meta_robots = 'noindex, nofollow'

    def get_meta_object(self):
        return None


class PaymentFailureView(SEOMixin, DetailView):
    model = Booking
    template_name = 'pages/booking/failure.html'
    context_object_name = 'booking'
    slug_field = 'number'
    slug_url_kwarg = 'number'
    meta_robots = 'noindex, nofollow'

    def get_meta_object(self):
        return None


@method_decorator(csrf_exempt, name='dispatch')
class PaymentResultView(View):
    """
    Серверный колбэк FreedomPay — единственный источник правды об оплате.

    CSRF отключён намеренно: запрос приходит не от браузера гостя. Вместо него
    проверяется подпись pg_sig, без валидной подписи запрос отклоняется.
    """

    def post(self, request):
        data = request.POST.dict()
        secret = settings.FREEDOMPAY['SECRET_KEY']
        script_name = request.path.rstrip('/').rsplit('/', 1)[-1]

        if not verify_signature(script_name, data, secret):
            logger.warning('FreedomPay: колбэк с неверной подписью, order_id=%s', data.get('pg_order_id'))
            return HttpResponse(
                FreedomPayClient.build_callback_response(
                    script_name, status='error',
                    description='Invalid signature', secret_key=secret,
                ),
                content_type='application/xml', status=400,
            )

        payment = Payment.objects.filter(order_id=data.get('pg_order_id', '')).first()
        if payment is None:
            logger.error('FreedomPay: колбэк по неизвестному заказу %s', data.get('pg_order_id'))
            return HttpResponse(
                FreedomPayClient.build_callback_response(
                    script_name, status='error',
                    description='Order not found', secret_key=secret,
                ),
                content_type='application/xml', status=404,
            )

        if data.get('pg_result') == '1':
            payment.external_id = data.get('pg_payment_id', payment.external_id)
            payment.save(update_fields=['external_id', 'updated_at'])
            handle_successful_payment(payment, callback_data=data)
        else:
            handle_failed_payment(
                payment, callback_data=data,
                message=data.get('pg_failure_description', ''),
            )

        return HttpResponse(
            FreedomPayClient.build_callback_response(
                script_name, status='ok', description='Accepted',
                secret_key=secret, salt=data.get('pg_salt', ''),
            ),
            content_type='application/xml',
        )


def availability_api(request):
    """
    JSON-эндпоинт для виджета бронирования: наличие и цены на выбранные даты.
    Используется фронтендом, чтобы обновлять список номеров без перезагрузки.
    """
    form = AvailabilitySearchForm(request.GET or None)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

    data = form.cleaned_data
    try:
        results = search_availability(
            data['check_in'], data['check_out'], data['adults'], data['children'],
        )
    except BookingError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

    return JsonResponse({
        'ok': True,
        'nights': (data['check_out'] - data['check_in']).days,
        'rooms': [
            {
                'slug': r.category.slug,
                'name': str(r.category.name),
                'url': r.category.get_absolute_url(),
                'cover': r.category.cover.url if r.category.cover else '',
                'available_rooms': r.available_rooms,
                'price_per_night': str(r.price_per_night),
                'total_price': str(r.total_price),
                'currency': r.currency,
                'capacity': r.category.max_guests,
            }
            for r in results
        ],
    })
