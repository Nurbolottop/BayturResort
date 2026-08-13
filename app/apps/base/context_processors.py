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
    }


def _popup_offers(request, site):
    """Акции для всплывающего окна.

    Пустой список = окно не рисуется вовсе. Скрываем его в админке,
    на самих страницах акций (там оно бессмысленно) и когда действующих
    предложений нет.
    """
    if not site.popup_enabled:
        return []

    path = request.path or ''
    if path.startswith('/admin') or '/offers/' in path:
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
