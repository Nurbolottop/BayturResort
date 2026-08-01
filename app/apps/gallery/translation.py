from modeltranslation.translator import TranslationOptions, register

from apps.base.translation import SEOTranslationOptions
from apps.gallery.models import GalleryAlbum, GalleryImage, Video, VirtualTour


@register(GalleryAlbum)
class GalleryAlbumTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('title', 'description')


@register(GalleryImage)
class GalleryImageTranslationOptions(TranslationOptions):
    fields = ('title', 'alt')


@register(Video)
class VideoTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(VirtualTour)
class VirtualTourTranslationOptions(TranslationOptions):
    fields = ('title',)
