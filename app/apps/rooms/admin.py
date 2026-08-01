from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from apps.rooms.models import Amenity, RoomCategory, RoomImage


@admin.register(Amenity)
class AmenityAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


class RoomImageInline(TranslationTabularInline):
    model = RoomImage
    extra = 1
    fields = ('image', 'alt', 'order', 'is_active')


@admin.register(RoomCategory)
class RoomCategoryAdmin(TabbedTranslationAdmin):
    list_display = (
        'preview', 'name', 'kind', 'capacity_adults', 'base_price',
        'shelter_code', 'is_bookable', 'order', 'is_active',
    )
    list_display_links = ('preview', 'name')
    list_editable = ('order', 'is_active', 'is_bookable')
    list_filter = ('kind', 'is_active', 'is_bookable', 'show_on_home')
    search_fields = ('name', 'slug', 'shelter_code')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('amenities',)
    inlines = (RoomImageInline,)

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'kind', 'cover', 'short_description', 'description'),
        }),
        (_('Вместимость и параметры'), {
            'fields': ('capacity_adults', 'capacity_children', 'area', 'beds', 'rooms_count', 'amenities'),
        }),
        (_('Цена и бронирование'), {
            'fields': ('base_price', 'is_bookable', 'shelter_code', 'total_rooms'),
        }),
        (_('Отображение'), {
            'fields': ('show_on_home', 'order', 'is_active'),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Фото'))
    def preview(self, obj):
        if obj.cover:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', obj.cover.url)
        return '—'
