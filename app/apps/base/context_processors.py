from django.conf import settings


def site_settings(request):
    """Настройки сайта, меню подвала и языки — доступны во всех шаблонах."""

    from apps.base.models import SiteSettings
    from apps.cms.models import StaticPage

    return {
        'site': SiteSettings.get_solo(),
        'site_url': settings.SITE_URL,
        'footer_pages': StaticPage.objects.filter(is_active=True, show_in_footer=True),
        'menu_pages': StaticPage.objects.filter(is_active=True, show_in_menu=True),
    }
