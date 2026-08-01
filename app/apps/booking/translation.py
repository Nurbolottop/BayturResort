from modeltranslation.translator import TranslationOptions, register

from apps.booking.models import Addon


@register(Addon)
class AddonTranslationOptions(TranslationOptions):
    fields = ('name', 'description')
