from modeltranslation.translator import TranslationOptions, register

from apps.base.translation import SEOTranslationOptions
from apps.blog.models import Guest, Post


@register(Post)
class PostTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('title', 'excerpt', 'content')


# Отзывы гостей не переводим: это пользовательский контент, он показывается как есть.


@register(Guest)
class GuestTranslationOptions(TranslationOptions):
    """Имя не переводим — переводим только подпись и цитату."""

    fields = ('role', 'quote')
