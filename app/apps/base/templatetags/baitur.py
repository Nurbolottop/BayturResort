from decimal import Decimal, InvalidOperation

from django import template
from django.urls import translate_url as django_translate_url
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag(takes_context=True)
def switch_lang_url(context, language_code):
    """URL текущей страницы на другом языке — для переключателя и hreflang."""
    request = context.get('request')
    if request is None:
        return '/'
    return django_translate_url(request.get_full_path(), language_code)


@register.filter
def money(value):
    """1234.00 → «1 234». Дробную часть показываем только если она есть."""
    try:
        amount = Decimal(value)
    except (TypeError, ValueError, InvalidOperation):
        return value

    quantized = amount.quantize(Decimal('0.01'))
    whole = int(quantized)
    cents = int((quantized - whole) * 100)
    formatted = f'{whole:,}'.replace(',', ' ')
    return formatted if cents == 0 else f'{formatted},{cents:02d}'


@register.filter
def nights_label(count):
    """Правильное склонение слова «ночь» для русской версии."""
    try:
        count = int(count)
    except (TypeError, ValueError):
        return ''

    if 11 <= count % 100 <= 14:
        return _('ночей')
    remainder = count % 10
    if remainder == 1:
        return _('ночь')
    if remainder in (2, 3, 4):
        return _('ночи')
    return _('ночей')


@register.filter
def guests_label(count):
    try:
        count = int(count)
    except (TypeError, ValueError):
        return ''

    if 11 <= count % 100 <= 14:
        return _('гостей')
    remainder = count % 10
    if remainder == 1:
        return _('гость')
    if remainder in (2, 3, 4):
        return _('гостя')
    return _('гостей')


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Меняет параметры в текущей query string — для пагинации и фильтров."""
    request = context.get('request')
    params = request.GET.copy() if request else {}
    for key, value in kwargs.items():
        if value in (None, ''):
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()
