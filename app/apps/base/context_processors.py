from django.conf import settings
from django.db.models import Q
from django.utils import timezone


def site_settings(request):
    """Настройки сайта, меню подвала и языки — доступны во всех шаблонах."""

    from apps.base.models import SiteSettings
    from apps.cms.models import StaticPage

    site = SiteSettings.get_solo()

    return {
        'site': site,
        'site_url': settings.SITE_URL,
        'footer_pages': StaticPage.objects.filter(is_active=True, show_in_footer=True),
        'menu_pages': StaticPage.objects.filter(is_active=True, show_in_menu=True),
        'popup_offers': _popup_offers(request, site),
        'schema_rating': _rating(),
        'price_range': _price_range(),
    }


def _rating():
    """
    Средняя оценка по опубликованным отзывам — свойство aggregateRating.

    Отдаём только то, что гость видит на странице отзывов: выдуманный или
    скрытый от посетителя рейтинг Google считает нарушением и снимает
    расширенный сниппет целиком.
    """
    from django.db.models import Avg, Count

    from apps.blog.models import Review

    agg = (Review.objects
           .filter(is_approved=True, rating__isnull=False)
           .aggregate(value=Avg('rating'), count=Count('id')))
    if not agg['count']:
        return None
    return {'value': round(agg['value'], 1), 'count': agg['count']}


def _price_range():
    """Вилка цен значками валюты — как её ожидает Schema.org."""
    from apps.rooms.models import RoomCategory

    prices = list(RoomCategory.objects
                  .filter(is_active=True, base_price__gt=0)
                  .values_list('base_price', flat=True))
    if not prices:
        return '$$'
    # Ориентир по минимальной цене за ночь в сомах: до 10 000 — недорого,
    # до 30 000 — средний уровень, выше — премиальный.
    low = min(prices)
    if low < 10000:
        return '$'
    if low < 30000:
        return '$$'
    return '$$$'


def _popup_offers(request, site):
    """Акции для всплывающего окна.

    Пустой список = окно не рисуется вовсе. Скрываем его в админке,
    на самих страницах акций (там оно бессмысленно) и когда действующих
    предложений нет.
    """
    if not site.popup_enabled:
        return []

    # На страницах акций окно бессмысленно, а на бронировании — вредно:
    # гость уже оформляет заказ, и перекрывать ему форму нельзя.
    path = request.path or ''
    if path.startswith('/admin') or '/offers/' in path or '/booking/' in path:
        return []

    from apps.offers.models import SpecialOffer

    today = timezone.localdate()
    offers = (
        SpecialOffer.objects
        .filter(is_active=True)
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=today))
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=today))
        .order_by('order', '-id')[:site.popup_limit or 3]
    )
    return list(offers)
