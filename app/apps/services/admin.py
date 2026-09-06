from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from apps.services.models import ConferenceHall, Service, ServiceCategory, ServiceImage


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'slug', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class ServiceImageInline(TranslationTabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'alt', 'order', 'is_active')


@admin.register(Service)
class ServiceAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'category', 'price', 'show_on_home', 'order', 'is_active')
    list_editable = ('order', 'is_active', 'show_on_home')
    list_filter = ('category', 'is_active', 'show_on_home')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'short_description')
    inlines = (ServiceImageInline,)

    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'cover', 'short_description', 'description'),
        }),
        (_('Цена'), {
            'fields': ('price', 'price_note', 'duration'),
        }),
        (_('Отображение'), {
            'fields': ('show_on_home', 'order', 'is_active'),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ConferenceHall)
class ConferenceHallAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'area', 'capacity_min', 'capacity_max', 'price_day', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'cover', 'description', 'equipment'),
        }),
        (_('Стоимость аренды'), {
            'fields': ('price_day', 'price_half_day', 'price_hour',
                       'price_from', 'included', 'is_year_round'),
        }),
        (_('Вместимость'), {
            'fields': (
                'area', 'capacity_min', 'capacity_max',
                'capacity_theatre', 'capacity_classroom', 'capacity_banquet',
                'capacity_ushape', 'capacity_conference', 'capacity_square',
                'capacity_amphitheatre', 'capacity_cabaret',
            ),
        }),
        (_('Отображение'), {
            'fields': ('order', 'is_active'),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )
