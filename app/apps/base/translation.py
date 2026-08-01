from modeltranslation.translator import TranslationOptions, register

from apps.base.models import Advantage, HomeSlide, SiteSettings


class SEOTranslationOptions(TranslationOptions):
    """Базовый набор SEO-полей — переводится для каждой языковой версии (п. 9 ТЗ)."""

    fields = ('seo_title', 'seo_description', 'seo_keywords')


@register(SiteSettings)
class SiteSettingsTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + (
        'site_name', 'tagline', 'address', 'working_hours', 'legal_name', 'requisites', 'booking_rules',
    )


@register(HomeSlide)
class HomeSlideTranslationOptions(TranslationOptions):
    fields = ('title', 'subtitle', 'button_text')


@register(Advantage)
class AdvantageTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
