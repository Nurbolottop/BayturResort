from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from apps.blog.models import Post, Review


@admin.register(Post)
class PostAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'published_at', 'views', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'published_at')
    date_hierarchy = 'published_at'
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'excerpt')
    readonly_fields = ('views',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'cover', 'excerpt', 'content'),
        }),
        (_('Публикация'), {
            'fields': ('published_at', 'order', 'is_active', 'views'),
        }),
        (_('SEO'), {
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'og_image'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'rating', 'source', 'is_approved', 'show_on_home', 'created_at')
    list_editable = ('is_approved', 'show_on_home')
    list_filter = ('is_approved', 'show_on_home', 'source', 'rating')
    search_fields = ('author_name', 'text')
    actions = ('approve_selected',)

    @admin.action(description=_('Одобрить выбранные отзывы'))
    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, _('Одобрено отзывов: %(n)s') % {'n': updated})
