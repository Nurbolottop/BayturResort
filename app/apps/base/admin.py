from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from apps.base.models import Advantage, HomeSlide, SiteSettings

admin.site.site_header = 'Baytur Resort & Spa'
admin.site.site_title = 'Baytur Resort & Spa'
admin.site.index_title = _('Управление сайтом')


class PreviewMixin:
    @admin.display(description=_('Превью'))
    def preview(self, obj):
        image = getattr(obj, 'image', None) or getattr(obj, 'cover', None)
        if image:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', image.url)
        return '—'


@admin.register(SiteSettings)
class SiteSettingsAdmin(TabbedTranslationAdmin):
    fieldsets = (
        (_('Идентичность'), {
            'fields': ('site_name', 'tagline', 'logo', 'logo_light', 'favicon'),
        }),
        (_('Контакты'), {
            'fields': ('phone', 'phone_extra', 'email', 'address', 'working_hours',
                       'map_embed', 'map_google_url', 'map_2gis_url'),
            'description': _('Если заданы обе ссылки на карты, по клику на адрес гость '
                             'выбирает, где открыть — Google Maps или 2ГИС.'),
        }),
        (_('Соцсети и мессенджеры'), {
            'fields': ('whatsapp', 'booking_whatsapp', 'telegram', 'instagram', 'facebook', 'youtube', 'tiktok'),
        }),
        (_('Бронирование'), {
            'fields': ('check_in_time', 'check_out_time', 'booking_rules'),
        }),
        (_('3D-тур'), {
            'fields': ('tour_url',),
            'description': _('Кнопка «3D-тур» в шапке, подвале и галерее появляется, '
                             'когда поле заполнено.'),
        }),
        (_('Окно с акциями'), {
            'fields': ('popup_enabled', 'popup_title', 'popup_text',
                       'popup_delay', 'popup_repeat_days', 'popup_limit'),
            'description': _('Всплывающее окно при входе на сайт. Показывается только '
                             'при наличии действующих акций и не появляется на самих '
                             'страницах спецпредложений.'),
        }),
        (_('Реквизиты'), {
            'fields': ('legal_name', 'requisites'),
            'classes': ('collapse',),
        }),
        (_('Аналитика'), {
            'fields': ('google_analytics_id', 'google_site_verification', 'yandex_metrika_id'),
            'classes': ('collapse',),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """Единственная запись — сразу открываем её на редактирование."""
        from django.shortcuts import redirect
        from django.urls import reverse

        obj = SiteSettings.get_solo()
        return redirect(reverse('admin:base_sitesettings_change', args=[obj.pk]))


@admin.register(HomeSlide)
class HomeSlideAdmin(PreviewMixin, TabbedTranslationAdmin):
    list_display = ('preview', 'title', 'order', 'is_active')
    list_display_links = ('preview', 'title')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'subtitle')


@admin.register(Advantage)
class AdvantageAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')
