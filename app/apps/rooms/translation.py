from modeltranslation.translator import TranslationOptions, register

from apps.base.translation import SEOTranslationOptions
from apps.rooms.models import Amenity, RoomCategory, RoomImage


@register(Amenity)
class AmenityTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(RoomCategory)
class RoomCategoryTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('name', 'short_description', 'description', 'beds')


@register(RoomImage)
class RoomImageTranslationOptions(TranslationOptions):
    fields = ('alt',)
