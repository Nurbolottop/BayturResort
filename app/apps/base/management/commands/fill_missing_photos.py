"""
Дозаполняет фотографии там, где их не хватило после основной раскладки.

Снимки берутся со старого сайта resort.baytur.kg: у отдельных процедур SPA,
залов и блоков «О нас» на Диске своих папок нет, а на старом сайте у каждой
позиции есть иллюстрация рядом с текстом.

Файлы кладутся в media/legacy/, команда разносит их по объектам.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.cms.models import AboutSection, Mission
from apps.services.models import ConferenceHall, Service

SOURCE_DIR = Path(settings.MEDIA_ROOT) / 'legacy'

# Услуга (slug) → файл со старого сайта
SERVICE_PHOTOS = {
    'spa-0': '60.jpg',                    # Процедурный кабинет
    'spa-1': '62.jpg',                    # Парафинолечение
    'spa-2': '61.jpg',                    # Кедровая бочка
    'spa-3': '63.jpg',                    # Лечебные ванны
    'spa-4': '64.jpg',                    # Инфракрасная кабинка
    'spa-5': '65.jpg',                    # Солевая комната
    'spa-6': '58.jpg',                    # Сауна
    'spa-7': 'paraffin-therapy-1.jpg',    # Релакс-кабинет
    'spa-8': '59.jpg',                    # Пантовые ванны
    'restaurants-5': '22.jpg',            # Splash Bar
    'sport-1': '6.jpg',                   # Тренажёрный зал
    'leisure-0': '32.jpg',                # Детская площадка
}

HALL_PHOTOS = {
    'suusamyr-too-ashuu': '53.jpg',
    'business-center': '57.jpg',
}

ABOUT_PHOTO = 'spazone.jpg'
MISSION_PHOTO = 'lobby.jpg'


class Command(BaseCommand):
    help = 'Дозаполняет фото услуг, залов и блоков «О нас» из media/legacy.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать уже привязанные фотографии')

    def handle(self, *args, **options):
        self.force = options['force']

        if not SOURCE_DIR.exists():
            self.stderr.write('Нет папки с файлами: %s' % SOURCE_DIR)
            return

        self.missing = []
        self.fill_services()
        self.fill_halls()
        self.fill_about()

        if self.missing:
            self.stdout.write(self.style.WARNING(
                'Не нашлось файлов: %s' % ', '.join(sorted(set(self.missing)))))
        self.stdout.write(self.style.SUCCESS('Недостающие фотографии добавлены.'))

    def attach(self, obj, field, filename, label):
        if getattr(obj, field) and not self.force:
            return
        path = SOURCE_DIR / filename
        if not path.exists():
            self.missing.append(filename)
            return
        with path.open('rb') as fh:
            getattr(obj, field).save(path.name, File(fh), save=True)
        self.stdout.write('  %-34s %s' % (label, filename))

    def fill_services(self):
        for slug, filename in SERVICE_PHOTOS.items():
            service = Service.objects.filter(slug=slug).first()
            if service:
                self.attach(service, 'cover', filename, str(service.name))

    def fill_halls(self):
        for slug, filename in HALL_PHOTOS.items():
            hall = ConferenceHall.objects.filter(slug=slug).first()
            if hall:
                self.attach(hall, 'cover', filename, str(hall.name))

    def fill_about(self):
        section = AboutSection.objects.first()
        if section:
            self.attach(section, 'image', ABOUT_PHOTO, 'Блок «О нас»')

        mission = Mission.get_solo()
        self.attach(mission, 'image', MISSION_PHOTO, 'Миссия и цели')
