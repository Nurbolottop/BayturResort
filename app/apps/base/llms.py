"""
Файл /llms.txt — краткая выжимка о курорте для языковых моделей.

Складывающийся стандарт: ИИ-поисковики забирают его вместо того, чтобы
разбирать вёрстку страниц. Разметка Schema.org отвечает на вопрос «что это
за объект», а здесь — связный текст, который модель может процитировать:
цены, вместимость, контакты, адреса разделов.

Собирается из базы, а не пишется руками, чтобы цены и список номеров
не разъезжались с сайтом.
"""

from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.views import View

from apps.base.models import SiteSettings


class LLMsTxtView(View):
    """Отдаёт выжимку обычным текстом."""

    def get(self, request, *args, **kwargs):
        from apps.rooms.models import RoomCategory
        from apps.services.models import ConferenceHall, Service

        # Файл один на весь сайт, поэтому язык фиксируем: русская версия
        # полная, и именно на неё указывают canonical и hreflang x-default.
        with translation.override('ru'):
            site = SiteSettings.get_solo()
            base = request.build_absolute_uri('/').rstrip('/')

            out = ['# %s' % site.site_name, '']
            if site.seo_description:
                out += ['> %s' % site.seo_description, '']

            out += ['## О курорте', '']
            if site.legal_name:
                out.append('- Юридическое лицо: %s' % site.legal_name)
            if site.address:
                out.append('- Адрес: %s' % site.address)
            if site.latitude and site.longitude:
                out.append('- Координаты: %s, %s' % (site.latitude, site.longitude))
            for label, value in (('Телефон', site.phone),
                                 ('Дополнительный телефон', site.phone_extra),
                                 ('E-mail', site.email),
                                 ('WhatsApp для брони', site.booking_whatsapp or site.whatsapp)):
                if value:
                    out.append('- %s: %s' % (label, value))
            out.append('- Заезд с %s, выезд до %s' % (site.check_in_time, site.check_out_time))
            if site.star_rating:
                out.append('- Категория: %s звёзд' % site.star_rating)
            if site.rooms_total:
                out.append('- Всего номеров: %s' % site.rooms_total)
            out.append('- Языки сайта: русский, английский, кыргызский')
            out.append('')

            amenities = [l.strip() for l in (site.amenities or '').splitlines() if l.strip()]
            if amenities:
                out += ['## Удобства', ''] + ['- %s' % a for a in amenities] + ['']

            rooms = RoomCategory.objects.filter(is_active=True).order_by('base_price')
            if rooms:
                out += ['## Номера и цены', '']
                for r in rooms:
                    parts = ['%s сом за ночь' % int(r.base_price)] if r.base_price else []
                    if r.area:
                        parts.append('%s м²' % r.area.normalize())
                    guests = (r.capacity_adults or 0) + (r.capacity_children or 0)
                    if guests:
                        parts.append('до %s гостей' % guests)
                    out.append('- [%s](%s%s)%s' % (
                        r.name, base, r.get_absolute_url(),
                        (' — ' + ', '.join(parts)) if parts else ''))
                out.append('')

            halls = ConferenceHall.objects.filter(is_active=True)
            if halls:
                out += ['## Конференц-залы', '']
                for h in halls:
                    parts = []
                    if h.capacity_max:
                        parts.append('до %s человек' % h.capacity_max)
                    if h.price_day:
                        parts.append('%s сом за день' % int(h.price_day))
                    out.append('- [%s](%s%s)%s' % (
                        h.name, base, h.get_absolute_url(),
                        (' — ' + ', '.join(parts)) if parts else ''))
                out.append('')

            services = Service.objects.filter(is_active=True)[:30]
            if services:
                out += ['## Услуги', '']
                out += ['- %s' % s.name for s in services]
                out.append('')

            out += ['## Разделы сайта', '']
            for name, route in (('Главная', 'base:home'), ('О нас', 'base:about'),
                                ('Номера', 'rooms:list'), ('Услуги', 'services:list'),
                                ('Конференц-залы', 'services:halls'),
                                ('Спецпредложения', 'offers:list'),
                                ('Галерея', 'gallery:index'), ('Блог', 'blog:list'),
                                ('Отзывы', 'blog:reviews'), ('Контакты', 'contacts:index')):
                try:
                    out.append('- [%s](%s%s)' % (name, base, reverse(route)))
                except Exception:
                    continue
            out.append('')

            links = [u for u in (site.instagram, site.facebook, site.youtube,
                                 site.tiktok, site.map_google_url, site.map_2gis_url) if u]
            if links:
                out += ['## Профили и карты', ''] + ['- %s' % u for u in links] + ['']

        return HttpResponse('\n'.join(out), content_type='text/plain; charset=utf-8')
