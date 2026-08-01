from modeltranslation.translator import TranslationOptions, register

from apps.base.translation import SEOTranslationOptions
from apps.cms.models import AboutSection, StaticPage


@register(StaticPage)
class StaticPageTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('title', 'content')


@register(AboutSection)
class AboutSectionTranslationOptions(TranslationOptions):
    fields = ('title', 'subtitle', 'content')
