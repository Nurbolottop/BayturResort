"""Единый способ отдавать мета-теги в шаблон (п. 9 ТЗ)."""

from dataclasses import dataclass

from django.conf import settings


@dataclass
class PageMeta:
    title: str = ''
    description: str = ''
    keywords: str = ''
    image: str = ''
    canonical: str = ''
    robots: str = 'index, follow'


class SEOMixin:
    """
    Подмешивается в любую CBV. Берёт мета-теги из объекта (если он есть
    и наследует SEOModel), иначе — из `meta_title` / `meta_description` вью.
    """

    meta_title = ''
    meta_description = ''
    meta_keywords = ''
    meta_robots = 'index, follow'

    def get_meta_object(self):
        return getattr(self, 'object', None)

    @staticmethod
    def absolute(url):
        """Ссылка на основной домен, а не на тот, через который зашли."""
        return settings.SITE_URL.rstrip('/') + url

    def get_page_meta(self, context):
        obj = self.get_meta_object()
        request = self.request

        title = self.meta_title
        description = self.meta_description
        keywords = self.meta_keywords
        image = ''

        if obj is not None:
            title = getattr(obj, 'seo_title', '') or getattr(obj, 'get_seo_title', lambda: '')() or title
            description = getattr(obj, 'seo_description', '') or description
            keywords = getattr(obj, 'seo_keywords', '') or keywords
            og_image = getattr(obj, 'og_image', None) or getattr(obj, 'cover', None)
            if og_image:
                image = self.absolute(og_image.url)

        if not image:
            # Настройки берём напрямую: context-процессоры добавляются к контексту
            # только при отрисовке, а здесь мы ещё внутри get_context_data —
            # из-за этого запасная картинка для соцсетей не подставлялась вовсе.
            from apps.base.models import SiteSettings

            site = SiteSettings.get_solo()
            if site.og_image:
                image = self.absolute(site.og_image.url)

        return PageMeta(
            title=str(title),
            description=str(description),
            keywords=str(keywords),
            image=image,
            # Домен берём из настроек, а не из запроса: сайт отвечает на
            # нескольких именах (baytur.kg, www-варианты, служебный поддомен),
            # и build_absolute_uri подставлял тот, через который зашли. Каждый
            # домен объявлял оригиналом себя, поисковик видел четыре копии
            # сайта и выбирал главный сам — вразрез с hreflang, который всегда
            # указывает на resort.baytur.kg.
            canonical=self.absolute(request.path),
            robots=self.meta_robots,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta'] = self.get_page_meta(context)
        context['site_url'] = settings.SITE_URL
        return context
