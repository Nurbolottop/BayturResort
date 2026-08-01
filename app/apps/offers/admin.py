from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from apps.offers.models import PromoCode, SpecialOffer


@admin.register(SpecialOffer)
class SpecialOfferAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'price', 'old_price', 'valid_from', 'valid_to', 'is_running', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'show_on_home')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'subtitle')
    filter_horizontal = ('room_categories',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'subtitle', 'cover', 'description'),
        }),
        (_('Цена и период'), {
            'fields': ('price', 'old_price', 'valid_from', 'valid_to'),
        }),
        (_('Связи'), {
            'fields': ('room_categories', 'promo_code'),
        }),
        (_('Отображение'), {
            'fields': ('show_on_home', 'order', 'is_active'),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Идёт сейчас'), boolean=True)
    def is_running(self, obj):
        return obj.is_running


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'value', 'valid_from', 'valid_to',
        'used_count', 'max_uses', 'is_active',
    )
    list_editable = ('is_active',)
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'comment')
    filter_horizontal = ('room_categories',)
    readonly_fields = ('used_count', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('code', 'comment', 'is_active'),
        }),
        (_('Скидка'), {
            'fields': ('discount_type', 'value'),
        }),
        (_('Условия применения'), {
            'fields': ('valid_from', 'valid_to', 'min_nights', 'min_amount', 'max_uses', 'room_categories'),
        }),
        (_('Служебное'), {
            'fields': ('used_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
