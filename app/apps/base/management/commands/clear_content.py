"""
Полная очистка сайта перед загрузкой реальных данных.

Удаляет весь демонстрационный контент — тексты и фотографии. Остаётся
только то, что просил Заказчик: баннер на первом экране, логотип и
название курорта, а также настоящие контакты (телефон и WhatsApp).

Заявки на бронирование не трогаем: это не контент, а рабочие записи.
Для них отдельный флаг --with-requests.
"""

import shutil
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

# Что удаляем целиком. Порядок важен: сначала зависимые записи.
CONTENT_MODELS = [
    'base.Advantage',
    'rooms.RoomImage', 'rooms.RoomCategory', 'rooms.Amenity',
    'services.ServiceImage', 'services.Service', 'services.ServiceCategory',
    'services.ConferenceHall',
    'offers.SpecialOffer', 'offers.PromoCode',
    'gallery.GalleryImage', 'gallery.GalleryAlbum', 'gallery.Video', 'gallery.VirtualTour',
    'blog.Post', 'blog.Review', 'blog.Guest',
    'cms.MissionGoal', 'cms.Mission', 'cms.AboutSection', 'cms.StaticPage',
    'booking.Addon',
    'contacts.ContactRequest', 'contacts.EventRequest', 'contacts.Subscriber',
]

# Поля настроек сайта с демо-текстами. Название, логотип, телефон
# и WhatsApp в список не входят — они остаются.
SETTINGS_TEXT_FIELDS = [
    'tagline', 'email', 'address', 'working_hours',
    'legal_name', 'requisites', 'booking_rules',
    'seo_title', 'seo_description', 'seo_keywords',
    'map_embed', 'map_google_url', 'map_2gis_url',
    'instagram', 'facebook', 'youtube', 'tiktok', 'telegram',
    'tour_url', 'popup_title', 'popup_text',
    'google_analytics_id', 'google_site_verification', 'yandex_metrika_id',
]

# Папки медиа под удаление. site/ (логотип) и home/ (баннер) остаются,
# import/ — архив исходников со старого сайта, на сайте не показывается.
MEDIA_DIRS_TO_CLEAR = [
    'rooms', 'services', 'halls', 'offers', 'gallery',
    'blog', 'guests', 'about', 'booking', 'seo', 'pages',
]


class Command(BaseCommand):
    help = 'Удаляет весь демо-контент. Остаются баннер, логотип, название и контакты.'

    def add_arguments(self, parser):
        parser.add_argument('--with-requests', action='store_true',
                            help='Удалить также заявки на бронирование')
        parser.add_argument('--keep-media', action='store_true',
                            help='Не удалять файлы с диска, только записи в базе')
        parser.add_argument('--yes', action='store_true',
                            help='Подтверждение: без него команда ничего не делает')

    def handle(self, *args, **options):
        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                'Команда удаляет весь контент безвозвратно. Запустите с --yes.'
            ))
            return

        with transaction.atomic():
            self.clear_models(options['with_requests'])
            self.clear_site_settings()
            self.clear_slide_texts()

        if not options['keep_media']:
            self.clear_media()

        self.stdout.write(self.style.SUCCESS('Сайт очищен.'))
        self.stdout.write('Остались: баннер, логотип, название курорта, телефон и WhatsApp.')

    def clear_models(self, with_requests):
        labels = list(CONTENT_MODELS)
        if with_requests:
            labels += ['booking.Payment', 'booking.Booking', 'booking.BookingRequest']

        for label in labels:
            try:
                model = apps.get_model(label)
            except LookupError:
                continue
            count = model.objects.count()
            if count:
                model.objects.all().delete()
                self.stdout.write('  удалено: %-28s %s' % (model._meta.verbose_name_plural, count))

    def clear_site_settings(self):
        """Чистим тексты, оставляя название, логотип и реальные контакты."""
        from apps.base.models import SiteSettings

        site = SiteSettings.get_solo()
        languages = [code for code, _name in settings.LANGUAGES]

        for field in SETTINGS_TEXT_FIELDS:
            if not hasattr(site, field):
                continue
            setattr(site, field, '')
            # У переводимых полей своя копия на каждый язык
            for code in languages:
                attr = '%s_%s' % (field, code)
                if hasattr(site, attr):
                    setattr(site, attr, '')

        if site.og_image:
            site.og_image.delete(save=False)

        site.popup_enabled = False
        site.save()
        self.stdout.write('  настройки сайта очищены (название, логотип и телефоны сохранены)')

    def clear_slide_texts(self):
        """Баннер остаётся картинкой — подписи к нему пишет Заказчик."""
        from apps.base.models import HomeSlide

        languages = [code for code, _name in settings.LANGUAGES]
        for slide in HomeSlide.objects.all():
            for field in ('title', 'subtitle', 'button_text'):
                setattr(slide, field, '')
                for code in languages:
                    attr = '%s_%s' % (field, code)
                    if hasattr(slide, attr):
                        setattr(slide, attr, '')
            slide.button_url = ''
            slide.save()
        self.stdout.write('  тексты на баннере очищены, фотографии оставлены')

    def clear_media(self):
        root = Path(settings.MEDIA_ROOT)
        removed = 0
        for name in MEDIA_DIRS_TO_CLEAR:
            path = root / name
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
                removed += 1
        self.stdout.write('  удалено папок с файлами: %s' % removed)
