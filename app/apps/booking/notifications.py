"""
Уведомления по броням (п. 5.1 ТЗ): письмо гостю и письмо администратору.

Письма не должны ронять оплату: любая ошибка отправки логируется, но не
пробрасывается наверх — деньги уже приняты, бронь уже создана.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext as _

logger = logging.getLogger('baitur.booking')


def _send(subject, template, context, recipients):
    if not recipients:
        return False

    try:
        html = render_to_string(template, context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=_strip_tags(html),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html, 'text/html')
        message.send(fail_silently=False)
        return True
    except Exception as exc:  # noqa: BLE001 — письмо не должно ломать сценарий оплаты
        logger.error('Не удалось отправить письмо «%s» на %s: %s', subject, recipients, exc)
        return False


def _strip_tags(html):
    from django.utils.html import strip_tags
    return strip_tags(html)


def notify_booking_confirmed(booking):
    """Подтверждение брони гостю + копия администратору."""
    from apps.base.models import SiteSettings

    context = {
        'booking': booking,
        'site': SiteSettings.get_solo(),
        'site_url': settings.SITE_URL,
    }

    with translation.override(booking.language or settings.LANGUAGE_CODE):
        guest_subject = _('Бронирование %(number)s подтверждено — Baytur Resort & Spa') % {
            'number': booking.number,
        }
        _send(guest_subject, 'emails/booking_confirmed.html', context, [booking.guest_email])

    with translation.override(settings.LANGUAGE_CODE):
        admin_subject = _('Новая бронь %(number)s (%(category)s)') % {
            'number': booking.number,
            'category': booking.room_category_name,
        }
        _send(admin_subject, 'emails/booking_admin.html', context, settings.BOOKING_ADMIN_EMAILS)

    notify_telegram(
        f'🏨 Новая бронь {booking.number}\n'
        f'{booking.room_category_name} × {booking.rooms_count}\n'
        f'{booking.check_in:%d.%m.%Y} — {booking.check_out:%d.%m.%Y} ({booking.nights} ноч.)\n'
        f'Гость: {booking.guest_full_name}, {booking.guest_phone}\n'
        f'Оплачено: {booking.paid_amount} {booking.currency}'
    )


def notify_shelter_sync_failed(booking):
    """Критично: бронь оплачена, но не попала в PMS — нужен ручной ввод."""
    from apps.base.models import SiteSettings

    context = {
        'booking': booking,
        'site': SiteSettings.get_solo(),
        'site_url': settings.SITE_URL,
    }
    subject = _('⚠️ Бронь %(number)s оплачена, но НЕ записана в Shelter') % {'number': booking.number}
    _send(subject, 'emails/booking_sync_failed.html', context, settings.BOOKING_ADMIN_EMAILS)

    notify_telegram(
        f'⚠️ Бронь {booking.number} оплачена, но НЕ попала в Shelter.\n'
        f'Ошибка: {booking.shelter_error}\n'
        f'Заведите бронь в PMS вручную.'
    )


def notify_request(instance, title):
    """Уведомление о заявке из формы обратной связи / на мероприятие."""
    from apps.base.models import SiteSettings

    context = {
        'obj': instance,
        'title': title,
        'site': SiteSettings.get_solo(),
        'site_url': settings.SITE_URL,
    }
    _send(title, 'emails/request_admin.html', context, settings.BOOKING_ADMIN_EMAILS)
    notify_telegram(f'📩 {title}\n{instance}')


def notify_telegram(text):
    """Дублирование в Telegram, если бот настроен."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return False

    import requests
    try:
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            data={'chat_id': chat_id, 'text': text},
            timeout=10,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error('Не удалось отправить сообщение в Telegram: %s', exc)
        return False
