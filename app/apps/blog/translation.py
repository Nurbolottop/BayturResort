from modeltranslation.translator import register

from apps.base.translation import SEOTranslationOptions
from apps.blog.models import Post


@register(Post)
class PostTranslationOptions(SEOTranslationOptions):
    fields = SEOTranslationOptions.fields + ('title', 'excerpt', 'content')


# Отзывы гостей не переводим: это пользовательский контент, он показывается как есть.
