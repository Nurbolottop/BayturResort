"""
Раскладывает фотографии из выгрузки Google Диска по объектам сайта.

Файлы кладутся в `media/drive/<папка с Диска>/...`, а команда разносит их
по категориям номеров, услугам, залам и галерее. Соответствие папок и
разделов задано ниже — Заказчик присылает фото папками, а не по одной.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.gallery.models import GalleryAlbum, GalleryImage
from apps.rooms.models import RoomCategory, RoomImage
from apps.services.models import Service, ServiceCategory, ServiceImage
from apps.services.models import ConferenceHall

SOURCE_DIR = Path(settings.MEDIA_ROOT) / 'drive'

# Папка с Диска → категория номера на сайте
ROOM_FOLDERS = {
    'Номера/Стандарт': 'standard',
    'Номера/Делюкс': 'deluxe',
    'Номера/Полулюкс': 'semi-lux',
    'Номера/Люкс': 'lux',
    'Номера/Семейный': 'family',
    'Номера/Президентский': 'presidential',
    'Коттеджи/Стандарт': 'cottage-standard',
    'Коттеджи/Люкс': 'cottage-lux',
    'Вилла/вилла без джпт': 'villa',
    'Вилла': 'villa',
}

# Папка → категория услуг
SERVICE_FOLDERS = {
    'СПА': 'spa',
    'Рестораны/Давинчи': 'restaurants',
    'Открытые и закрытые объекты/Бассейн крытый': 'sport',
    'Пляж': 'leisure',
}

# Отдельные услуги внутри категорий: папка → slug услуги
SERVICE_ITEM_FOLDERS = {
    'сауна бельведер 5 этаж': 'spa-9',
    'Вип сауна(на улице)': 'spa-10',
    'Рестораны/Давинчи': 'restaurants-0',
    'Рестораны/Фреш': 'restaurants-1',
    'коколоко': 'restaurants-2',
    'Рестораны/Нисса': 'restaurants-3',
    'Рестораны/Спорт бар': 'restaurants-4',
    'Открытые и закрытые объекты/Бассейн крытый': 'sport-0',
    'Открытые и закрытые объекты/Футбольное/Теннисное поле': 'sport-2',
    'Пляж': 'leisure-1',
}

# Папка → конференц-зал
HALL_FOLDERS = {
    'конференц зал без джпт': 'grand-baytur',
    'Юрты': 'yurt-village',
}

# Папка → альбом галереи (название альбома создаётся, если его нет)
ALBUM_FOLDERS = {
    'Общий вид': 'Территория курорта',
    'Входная зона': 'Территория курорта',
    'Лобби': 'Интерьеры',
    'Пляж': 'Пляж и озеро',
    'Юрты': 'Юрточный городок',
    'Рестораны/Давинчи': 'Рестораны',
    'СПА': 'SPA-комплекс',
    'Открытые и закрытые объекты/Бассейн открытый': 'Бассейны',
}

IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}


class Command(BaseCommand):
    help = 'Раскладывает фото из media/drive по номерам, услугам, залам и галерее.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать уже привязанные фотографии')
        parser.add_argument('--limit', type=int, default=12,
                            help='Сколько фото брать из одной папки (по умолчанию 12)')

    def handle(self, *args, **options):
        self.force = options['force']
        self.limit = options['limit']

        if not SOURCE_DIR.exists():
            self.stderr.write('Нет папки с выгрузкой: %s' % SOURCE_DIR)
            return

        self.attach_rooms()
        self.attach_services()
        self.attach_service_items()
        self.attach_halls()
        self.attach_albums()
        self.stdout.write(self.style.SUCCESS('Фотографии разложены.'))

    # ------------------------------------------------------------ helpers

    def photos(self, folder):
        """Файлы-картинки из папки выгрузки, по порядку имени."""
        path = SOURCE_DIR / folder
        if not path.exists():
            return []
        files = [p for p in sorted(path.iterdir())
                 if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
        return files[:self.limit]

    @staticmethod
    def save_to(obj, field_name, path):
        with path.open('rb') as fh:
            getattr(obj, field_name).save(path.name, File(fh), save=True)

    # ------------------------------------------------------------- attach

    def attach_rooms(self):
        for folder, slug in ROOM_FOLDERS.items():
            files = self.photos(folder)
            if not files:
                continue
            room = RoomCategory.objects.filter(slug=slug).first()
            if not room:
                continue

            if room.cover and not self.force:
                continue

            self.save_to(room, 'cover', files[0])
            room.images.all().delete()
            for order, path in enumerate(files):
                image = RoomImage(category=room, alt=str(room.name), order=order)
                with path.open('rb') as fh:
                    image.image.save(path.name, File(fh), save=False)
                image.save()
            self.stdout.write('  %-26s %s фото' % (room.name, len(files)))

    def attach_services(self):
        for folder, slug in SERVICE_FOLDERS.items():
            files = self.photos(folder)
            if not files:
                continue
            category = ServiceCategory.objects.filter(slug=slug).first()
            if not category:
                continue
            if not category.cover or self.force:
                self.save_to(category, 'cover', files[0])
                self.stdout.write('  услуги: %-18s обложка' % category.name)

            # Остальные снимки — в галерею первой услуги категории
            service = category.services.first()
            if service and files[1:]:
                if service.images.exists() and not self.force:
                    continue
                service.images.all().delete()
                for order, path in enumerate(files[1:]):
                    image = ServiceImage(service=service, alt=str(service.name), order=order)
                    with path.open('rb') as fh:
                        image.image.save(path.name, File(fh), save=False)
                    image.save()

    def attach_service_items(self):
        """Обложки конкретным услугам: ресторанам, саунам, бассейну."""
        for folder, slug in SERVICE_ITEM_FOLDERS.items():
            files = self.photos(folder)
            if not files:
                continue
            service = Service.objects.filter(slug=slug).first()
            if not service or (service.cover and not self.force):
                continue
            self.save_to(service, 'cover', files[0])
            self.stdout.write('  услуга: %-24s обложка' % service.name)

    def attach_halls(self):
        for folder, slug in HALL_FOLDERS.items():
            files = self.photos(folder)
            if not files:
                continue
            hall = ConferenceHall.objects.filter(slug=slug).first()
            if not hall or (hall.cover and not self.force):
                continue
            self.save_to(hall, 'cover', files[0])
            self.stdout.write('  зал: %-22s обложка' % hall.name)

    def attach_albums(self):
        for folder, title in ALBUM_FOLDERS.items():
            files = self.photos(folder)
            if not files:
                continue
            album, _ = GalleryAlbum.objects.get_or_create(
                slug=self.slug_for(title), defaults={'title': title},
            )
            if not album.cover or self.force:
                self.save_to(album, 'cover', files[0])
            for order, path in enumerate(files):
                if album.images.filter(alt=path.name).exists():
                    continue
                image = GalleryImage(album=album, alt=path.name, order=order)
                with path.open('rb') as fh:
                    image.image.save(path.name, File(fh), save=False)
                image.save()
            self.stdout.write('  альбом: %-20s %s фото' % (title, len(files)))

    @staticmethod
    def slug_for(title):
        table = {
            'Территория курорта': 'territory', 'Интерьеры': 'interiors',
            'Пляж и озеро': 'beach', 'Юрточный городок': 'yurts',
            'Рестораны': 'restaurants', 'SPA-комплекс': 'spa',
            'Номера': 'rooms', 'Бассейны': 'pools',
        }
        return table.get(title, 'album')
