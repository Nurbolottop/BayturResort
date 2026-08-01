"""
Раскладывает фотографии курорта по объектам сайта.

Исходники лежат в `media/import/` (выгружены с текущего сайта resort.baytur.kg
с разрешения Заказчика). Команда идемпотентна: повторный запуск не плодит
дубли, а `--force` перезаписывает уже назначенные изображения.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.base.models import HomeSlide, SiteSettings
from apps.blog.models import Post
from apps.booking.models import Addon
from apps.cms.models import AboutSection
from apps.gallery.models import GalleryAlbum, GalleryImage
from apps.offers.models import SpecialOffer
from apps.rooms.models import RoomCategory, RoomImage
from apps.services.models import ConferenceHall, Service, ServiceCategory

IMPORT_DIR = Path(settings.MEDIA_ROOT) / 'import'

# Слайды первого экрана: файл → (заголовок, подзаголовок)
SLIDES = [
    ('1.jpg', 'Baytur Resort & Spa',
     'Премиальный семейный курорт на северном берегу Иссык-Куля'),
    ('49.jpg', 'Юрточный городок',
     'Национальный колорит и комфорт отеля на одной территории'),
    ('11.jpg', 'Бассейны и пляжный отдых',
     'Открытые и крытый бассейны, шезлонги, свой выход к озеру'),
]

# Обложка категории номера и дополнительные фото
ROOM_PHOTOS = {
    'standard': ('1333.jpg', ['1333.jpg', '4.jpg', '60.jpg', '11.jpg']),
    'semi-lux': ('polulux.webp', ['polulux.webp', '4.jpg', '60.jpg', '1.jpg']),
    'lux': ('lux.webp', ['lux.webp', 'delux.jpg', '4.jpg', '60.jpg']),
    'family': ('16.jpg', ['16.jpg', 'delux.jpg', '4.jpg', '11.jpg']),
    'cottage': ('50.jpg', ['50.jpg', '2.jpg', '33.jpg', '49.jpg']),
    'yurt': ('48.jpg', ['48.jpg', '54.jpg', '55.jpg', '49.jpg']),
}

SERVICE_CATEGORY_PHOTOS = {
    'spa': '61.jpg',
    'pools': 'swim.webp',
    'restaurants': '22.jpg',
    'sport': '5.jpg',
    'kids': '26.jpg',
}

SERVICE_PHOTOS = {
    'spa-0': '61.jpg',
    'spa-1': '61.jpg',
    'pools-0': '11.jpg',
    'restaurants-0': 'рест.JPEG.jpg',
    'sport-0': '6.jpg',
    'kids-0': '26.jpg',
}

HALL_PHOTOS = {
    'grand-hall': 'konverens.webp',
    'small-hall': '57.jpg',
}

OFFER_PHOTOS = {
    'spa-package': '61.jpg',
    'early-booking': '1.jpg',
}

ALBUM_PHOTOS = {
    'territory': ('49.jpg', ['48.jpg', '50.jpg', '11.jpg', '26.jpg', '15.jpg', '12.jpg', '1.jpg', '33.jpg']),
    'rooms': ('1333.jpg', ['lux.webp', 'polulux.webp', 'delux.jpg', '16.jpg', '4.jpg', '2.jpg']),
    'spa': ('swim.webp', ['61.jpg', '5.jpg', '6.jpg', '7.jpg', '12.jpg', '11.jpg']),
}

ADDON_PHOTOS = {
    'Завтрак': '22.jpg',
    'SPA-программа': '61.jpg',
}


class Command(BaseCommand):
    help = 'Привязывает фото из media/import/ к объектам сайта.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать уже назначенные изображения')

    def handle(self, *args, **options):
        self.force = options['force']

        if not IMPORT_DIR.exists():
            self.stderr.write(f'Нет папки с исходниками: {IMPORT_DIR}')
            return

        self.missing = set()

        self.import_logo()
        self.import_slides()
        self.import_rooms()
        self.import_services()
        self.import_halls()
        self.import_offers()
        self.import_albums()
        self.import_misc()

        if self.missing:
            self.stdout.write(self.style.WARNING(
                'Не найдены файлы: ' + ', '.join(sorted(self.missing))
            ))
        self.stdout.write(self.style.SUCCESS('Фотографии привязаны.'))

    # ------------------------------------------------------------- helpers

    def attach(self, obj, field_name, filename, save=True):
        """Кладёт файл из media/import в указанное поле объекта."""
        field = getattr(obj, field_name)
        if field and not self.force:
            return False

        path = IMPORT_DIR / filename
        if not path.exists():
            self.missing.add(filename)
            return False

        with path.open('rb') as fh:
            field.save(path.name, File(fh), save=save)
        return True

    # -------------------------------------------------------------- import

    def import_logo(self):
        logo = Path(settings.MEDIA_ROOT) / 'logo.png'
        if not logo.exists():
            return
        site = SiteSettings.get_solo()
        if site.logo and not self.force:
            return
        with logo.open('rb') as fh:
            site.logo.save('logo.png', File(fh), save=False)
        with logo.open('rb') as fh:
            site.logo_light.save('logo-light.png', File(fh), save=False)
        with logo.open('rb') as fh:
            site.favicon.save('favicon.png', File(fh), save=False)
        site.save()
        self.stdout.write('Логотип установлен.')

    def import_slides(self):
        for order, (filename, title, subtitle) in enumerate(SLIDES):
            slide, _ = HomeSlide.objects.get_or_create(title=title, defaults={
                'subtitle': subtitle, 'order': order,
                'button_text': 'Забронировать', 'button_url': '/booking/',
            })
            self.attach(slide, 'image', filename)
        self.stdout.write(f'Слайдов на главной: {HomeSlide.objects.count()}')

    def import_rooms(self):
        for slug, (cover, gallery) in ROOM_PHOTOS.items():
            room = RoomCategory.objects.filter(slug=slug).first()
            if not room:
                continue
            self.attach(room, 'cover', cover)

            if room.images.exists() and not self.force:
                continue
            for order, filename in enumerate(gallery):
                path = IMPORT_DIR / filename
                if not path.exists():
                    self.missing.add(filename)
                    continue
                image = RoomImage(category=room, alt=str(room.name), order=order)
                with path.open('rb') as fh:
                    image.image.save(path.name, File(fh), save=False)
                image.save()
        self.stdout.write('Фото номеров привязаны.')

    def import_services(self):
        for slug, filename in SERVICE_CATEGORY_PHOTOS.items():
            category = ServiceCategory.objects.filter(slug=slug).first()
            if category:
                self.attach(category, 'cover', filename)

        for slug, filename in SERVICE_PHOTOS.items():
            service = Service.objects.filter(slug=slug).first()
            if service:
                self.attach(service, 'cover', filename)
        self.stdout.write('Фото услуг привязаны.')

    def import_halls(self):
        for slug, filename in HALL_PHOTOS.items():
            hall = ConferenceHall.objects.filter(slug=slug).first()
            if hall:
                self.attach(hall, 'cover', filename)
        self.stdout.write('Фото залов привязаны.')

    def import_offers(self):
        for slug, filename in OFFER_PHOTOS.items():
            offer = SpecialOffer.objects.filter(slug=slug).first()
            if offer:
                self.attach(offer, 'cover', filename)
        self.stdout.write('Фото спецпредложений привязаны.')

    def import_albums(self):
        for slug, (cover, images) in ALBUM_PHOTOS.items():
            album = GalleryAlbum.objects.filter(slug=slug).first()
            if not album:
                continue
            self.attach(album, 'cover', cover)

            if album.images.exists() and not self.force:
                continue
            for order, filename in enumerate(images):
                path = IMPORT_DIR / filename
                if not path.exists():
                    self.missing.add(filename)
                    continue
                item = GalleryImage(album=album, alt=str(album.title), order=order)
                with path.open('rb') as fh:
                    item.image.save(path.name, File(fh), save=False)
                item.save()
        self.stdout.write('Галерея наполнена.')

    def import_misc(self):
        section = AboutSection.objects.filter(title='О курорте').first()
        if section:
            self.attach(section, 'image', '49.jpg')

        post = Post.objects.filter(slug='otkrytie-sezona').first()
        if post:
            self.attach(post, 'cover', '1.jpg')

        for name, filename in ADDON_PHOTOS.items():
            addon = Addon.objects.filter(name=name).first()
            if addon:
                self.attach(addon, 'image', filename)

        site = SiteSettings.get_solo()
        self.attach(site, 'og_image', '1.jpg')
