from modeltranslation.translator import register

from apps.base.translation import SEOTranslationOptions
from apps.offers.models import SpecialOffer


@register(SpecialOffer)
class SpecialOfferTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('title', 'subtitle', 'description')
