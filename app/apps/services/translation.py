from modeltranslation.translator import TranslationOptions, register

from apps.base.translation import SEOTranslationOptions
from apps.services.models import ConferenceHall, Service, ServiceCategory, ServiceImage


@register(ServiceCategory)
class ServiceCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Service)
class ServiceTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + (
        'name', 'short_description', 'description', 'price_note', 'duration',
    )


@register(ServiceImage)
class ServiceImageTranslationOptions(TranslationOptions):
    fields = ('alt',)


@register(ConferenceHall)
class ConferenceHallTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('name', 'description', 'equipment')
