from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from apps.cms.models import AboutSection, StaticPage


@admin.register(StaticPage)
class StaticPageAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'slug', 'show_in_menu', 'show_in_footer', 'order', 'is_active')
    list_editable = ('show_in_menu', 'show_in_footer', 'order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'cover', 'content'),
        }),
        (_('Отображение'), {
            'fields': ('show_in_menu', 'show_in_footer', 'order', 'is_active'),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )


@admin.register(AboutSection)
class AboutSectionAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'image_position', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'content')
