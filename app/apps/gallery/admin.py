from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from apps.gallery.models import GalleryAlbum, GalleryImage, Video, VirtualTour


class GalleryImageInline(TranslationTabularInline):
    model = GalleryImage
    extra = 1
    fields = ('image', 'title', 'alt', 'order', 'is_active')


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(TabbedTranslationAdmin):
    list_display = ('preview', 'title', 'images_count', 'order', 'is_active')
    list_display_links = ('preview', 'title')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    inlines = (GalleryImageInline,)

    @admin.display(description=_('Обложка'))
    def preview(self, obj):
        if obj.cover:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', obj.cover.url)
        return '—'

    @admin.display(description=_('Фото'))
    def images_count(self, obj):
        return obj.images.count()


@admin.register(Video)
class VideoAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title',)


@admin.register(VirtualTour)
class VirtualTourAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'embed_url', 'show_on_home', 'order', 'is_active')
    list_editable = ('order', 'is_active', 'show_on_home')
    search_fields = ('title',)
