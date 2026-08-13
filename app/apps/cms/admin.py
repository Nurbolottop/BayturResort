from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from modeltranslation.admin import TranslationStackedInline

from apps.cms.models import AboutSection, Mission, MissionGoal, StaticPage


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


class MissionGoalInline(TranslationStackedInline):
    model = MissionGoal
    extra = 1
    fields = ('title', 'description', 'order', 'is_active')


@admin.register(Mission)
class MissionAdmin(TabbedTranslationAdmin):
    """Блок открывает страницу «О нас», поэтому запись всегда одна."""

    inlines = (MissionGoalInline,)
    fieldsets = (
        (None, {
            'fields': ('is_active', 'eyebrow', 'title', 'statement', 'content', 'image'),
            'description': _('Первый блок страницы «О нас». Миссия выводится крупно, '
                             'цели — карточками под ней.'),
        }),
    )

    def has_add_permission(self, request):
        return not Mission.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AboutSection)
class AboutSectionAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'image_position', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'content')
