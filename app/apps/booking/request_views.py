"""
Заявка на бронирование через WhatsApp.

Онлайн-оплата и связка с PMS отложены: Заказчик сначала измеряет спрос.
Поэтому гость с сайта уходит в WhatsApp ресепшена с готовым текстом,
а мы сохраняем запрос — по этим записям считается количество обращений.
"""

import re
from datetime import date
from decimal import Decimal

from django.shortcuts import redirect
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.views import View

from apps.base.models import SiteSettings
from apps.booking.models import BookingRequest
from apps.rooms.models import RoomCategory


def whatsapp_number(site):
    """Только цифры: wa.me не принимает плюс, пробелы и скобки."""
    raw = site.booking_whatsapp or site.whatsapp or ''
    return re.sub(r'\D', '', raw)


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def parse_int(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


class BookingRequestView(View):
    """Сохраняет заявку и уводит гостя в WhatsApp с заполненным сообщением."""

    def post(self, request, *args, **kwargs):
        return self.handle(request)

    # Часть кнопок — обычные ссылки, поэтому GET тоже обрабатываем
    def get(self, request, *args, **kwargs):
        return self.handle(request)

    def handle(self, request):
        data = request.POST if request.method == 'POST' else request.GET
        site = SiteSettings.get_solo()

        category = RoomCategory.objects.filter(slug=data.get('category'), is_active=True).first()
        check_in = parse_date(data.get('check_in'))
        check_out = parse_date(data.get('check_out'))
        adults = parse_int(data.get('adults'), 2)
        children = parse_int(data.get('children'), 0)

        nights = (check_out - check_in).days if check_in and check_out and check_out > check_in else 0

        total = Decimal('0')
        if category and nights:
            total = category.base_price * nights

        BookingRequest.objects.create(
            room_category=category,
            room_category_name=str(category.name) if category else '',
            check_in=check_in,
            check_out=check_out,
            nights=nights,
            adults=adults,
            children=children,
            estimated_total=total,
            source_page=data.get('source', '')[:255],
            language=translation.get_language() or '',
            ip_address=self.client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        )

        number = whatsapp_number(site)
        if not number:
            # Номер не задан — возвращаем гостя на контакты, а не в пустоту
            return redirect('contacts:index')

        # Гость мог прийти прямо из шапки, ничего не выбрав. Тогда в письме
        # незачем перечислять подставленные по умолчанию цифры.
        has_details = bool(category) or bool(check_in and check_out)
        text = self.build_message(site, category, check_in, check_out,
                                  nights, adults, children, has_details)
        return redirect('https://wa.me/%s?text=%s' % (number, text))

    @staticmethod
    def client_ip(request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def build_message(site, category, check_in, check_out, nights, adults, children, has_details):
        from urllib.parse import quote

        lines = [_('Здравствуйте! Хочу забронировать номер в %(name)s.') % {'name': site.site_name}]

        if not has_details:
            # Ничего не выбрано — короткое сообщение, дальше подскажет ресепшен
            lines.append('')
            lines.append(_('Подскажите, пожалуйста, свободные даты и цены.'))
            return quote('\n'.join(lines))

        lines.append('')

        if category:
            lines.append(_('Категория: %(name)s') % {'name': category.name})

        if check_in and check_out:
            lines.append(_('Заезд: %(date)s') % {'date': check_in.strftime('%d.%m.%Y')})
            lines.append(_('Выезд: %(date)s') % {'date': check_out.strftime('%d.%m.%Y')})
            if nights:
                lines.append(_('Ночей: %(n)s') % {'n': nights})

            guests = _('Взрослых: %(a)s') % {'a': adults}
            if children:
                guests += ', ' + _('детей: %(c)s') % {'c': children}
            lines.append(guests)

        lines.append('')
        if check_in and check_out:
            lines.append(_('Подскажите, пожалуйста, свободно ли на эти даты?'))
        else:
            lines.append(_('Подскажите, пожалуйста, свободные даты и цены.'))

        return quote('\n'.join(lines))
