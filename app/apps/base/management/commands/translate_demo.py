"""
Заполняет английскую и кыргызскую версии демо-контента.

Интерфейс переводится через .po-файлы, а тексты в базе — через
django-modeltranslation (поля вида `name_en`, `name_ky`). Реальные переводы
даёт Заказчик (п. 8 ТЗ); эта команда нужна, чтобы языковые версии не
выглядели наполовину русскими на этапе демонстрации.
"""

from django.core.management.base import BaseCommand

from apps.base.models import Advantage, HomeSlide, SiteSettings
from apps.blog.models import Post
from apps.booking.models import Addon
from apps.cms.models import AboutSection, StaticPage
from apps.gallery.models import GalleryAlbum
from apps.offers.models import SpecialOffer
from apps.rooms.models import Amenity, RoomCategory
from apps.services.models import ConferenceHall, Service, ServiceCategory

# ru → (en, ky)
TEXTS = {
    # Слайды
    'Baytur Resort & Spa': ('Baytur Resort & Spa', 'Baytur Resort & Spa'),
    'Премиальный семейный курорт на северном берегу Иссык-Куля': (
        'A premium family resort on the northern shore of Issyk-Kul',
        'Ысык-Көлдүн түндүк жээгиндеги премиум үй-бүлөлүк курорт'),
    'Юрточный городок': ('Yurt Camp', 'Боз үй шаарчасы'),
    'Национальный колорит и комфорт отеля на одной территории': (
        'National flavour and hotel comfort in one place',
        'Улуттук колорит жана мейманкананын ыңгайлуулугу бир аймакта'),
    'Бассейны и пляжный отдых': ('Pools and Beach', 'Бассейндер жана жээкте эс алуу'),
    'Открытые и крытый бассейны, шезлонги, свой выход к озеру': (
        'Outdoor and indoor pools, sun loungers, private lake access',
        'Ачык жана жабык бассейндер, шезлонгдор, көлгө өз чыгуу жолу'),
    'Забронировать': ('Book Now', 'Брондоо'),

    # Настройки сайта
    'Курорт на северном берегу Иссык-Куля': (
        'A resort on the northern shore of Issyk-Kul',
        'Ысык-Көлдүн түндүк жээгиндеги курорт'),
    'Кыргызстан, Иссык-Кульская обл., с. Бостери': (
        'Bosteri, Issyk-Kul region, Kyrgyzstan',
        'Кыргызстан, Ысык-Көл облусу, Бостери айылы'),
    'Ресепшен работает круглосуточно': ('Reception is open 24/7', 'Ресепшн саат бою иштейт'),

    # Преимущества
    'Свой пляж 300 м': ('Private 300 m beach', 'Өзүнүн 300 м жээги'),
    'Песчаный берег и чистая вода в шаговой доступности от номера.': (
        'A sandy shore and clean water a short walk from your room.',
        'Кумдуу жээк жана таза суу бөлмөңүздөн бир нече кадам алыс.'),
    'SPA и бассейны': ('Spa and Pools', 'SPA жана бассейндер'),
    'Крытый и открытый бассейны, хаммам, сауна, массаж.': (
        'Indoor and outdoor pools, hammam, sauna, massage.',
        'Жабык жана ачык бассейндер, хаммам, сауна, массаж.'),
    'Питание': ('Dining', 'Тамактануу'),
    'Рестораны национальной и европейской кухни, детское меню.': (
        'Restaurants with national and European cuisine, kids menu.',
        'Улуттук жана европалык ашкана ресторандары, балдар менюсу.'),
    'Для детей': ('For Kids', 'Балдар үчүн'),
    'Детский клуб, анимация, площадки и мелкий бассейн.': (
        'Kids club, animation, playgrounds and a shallow pool.',
        'Балдар клубу, анимация, аянтчалар жана тайыз бассейн.'),

    # Удобства
    'Wi-Fi': ('Wi-Fi', 'Wi-Fi'),
    'Кондиционер': ('Air conditioning', 'Кондиционер'),
    'Балкон': ('Balcony', 'Балкон'),
    'Вид на озеро': ('Lake view', 'Көлгө көрүнүш'),
    'Мини-бар': ('Mini bar', 'Мини-бар'),
    'Сейф': ('Safe', 'Сейф'),
    'Телевизор': ('TV', 'Телевизор'),
    'Фен': ('Hair dryer', 'Фен'),

    # Категории номеров
    'Стандарт': ('Standard', 'Стандарт'),
    'Полулюкс': ('Junior Suite', 'Жарым люкс'),
    'Люкс': ('Suite', 'Люкс'),
    'Семейный': ('Family Room', 'Үй-бүлөлүк бөлмө'),
    'Коттедж у озера': ('Lakeside Cottage', 'Көл жээгиндеги коттедж'),
    'Юрта в юрточном городке': ('Yurt in the Yurt Camp', 'Боз үй шаарчасындагы боз үй'),
    '1 двуспальная': ('1 double bed', '1 кош керебет'),
    '1 двуспальная + диван': ('1 double bed + sofa', '1 кош керебет + диван'),
    '1 двуспальная + 2 односпальные': ('1 double + 2 single beds', '1 кош + 2 жеке керебет'),
    '2 двуспальные': ('2 double beds', '2 кош керебет'),
    '3 спальни': ('3 bedrooms', '3 уктоочу бөлмө'),
    'Топчаны': ('Traditional low beds', 'Тапчандар'),

    # Категории услуг
    'SPA и wellness': ('Spa & Wellness', 'SPA жана wellness'),
    'Бассейны': ('Pools', 'Бассейндер'),
    'Рестораны': ('Restaurants', 'Ресторандар'),
    'Спорткомплекс': ('Sports Complex', 'Спорт комплекси'),
    'Детская зона': ('Kids Area', 'Балдар аймагы'),

    # Услуги
    'Общий массаж': ('Full body massage', 'Жалпы массаж'),
    'Хаммам': ('Hammam', 'Хаммам'),
    'Открытый бассейн': ('Outdoor pool', 'Ачык бассейн'),
    'Ужин по меню': ('À la carte dinner', 'Меню боюнча кечки тамак'),
    'Тренажёрный зал': ('Gym', 'Машыгуу залы'),
    'Детский клуб': ('Kids club', 'Балдар клубу'),
    '60 минут': ('60 minutes', '60 мүнөт'),
    '90 минут': ('90 minutes', '90 мүнөт'),
    'Для гостей курорта': ('For resort guests', 'Курорттун конокторуна'),

    # Залы
    'Большой конференц-зал': ('Grand Conference Hall', 'Чоң конференц-зал'),
    'Малый зал': ('Small Hall', 'Кичи зал'),
    'Проектор, экран, звук, микрофоны, флипчарт': (
        'Projector, screen, sound, microphones, flipchart',
        'Проектор, экран, үн, микрофондор, флипчарт'),
    'ТВ-панель, флипчарт': ('TV panel, flipchart', 'ТВ-панель, флипчарт'),

    # Спецпредложения
    'Проживание + SPA': ('Stay + Spa', 'Жашоо + SPA'),
    '2 ночи в люксе и посещение SPA для двоих': (
        '2 nights in a suite and spa access for two',
        'Люкста 2 түн жана экөөгө SPA'),
    'Раннее бронирование': ('Early Booking', 'Эрте брондоо'),
    'Скидка 10% при брони за 30 дней': (
        '10% off when booking 30 days ahead',
        '30 күн мурун брондогондо 10% арзандатуу'),

    # Галерея
    'Территория курорта': ('Resort Grounds', 'Курорттун аймагы'),
    'Номера': ('Rooms', 'Бөлмөлөр'),

    # Блог
    'Открытие пляжного сезона': ('Beach Season Opening', 'Жээк сезонунун ачылышы'),
    'Рассказываем, что нового ждёт гостей на Иссык-Куле этим летом.': (
        'What is new for guests at Issyk-Kul this summer.',
        'Быйылкы жайда Ысык-Көлдө конокторду эмне күтөт.'),

    # Страницы
    'О нас': ('About Us', 'Биз жөнүндө'),
    'Иссык-Куль, с. Бостери': ('Issyk-Kul, Bosteri', 'Ысык-Көл, Бостери айылы'),
    'Политика конфиденциальности': ('Privacy Policy', 'Купуялык саясаты'),
    'Публичная оферта': ('Public Offer', 'Ачык оферта'),
    'Правила проживания': ('House Rules', 'Жашоо эрежелери'),

    # Доп. услуги
    'Завтрак': ('Breakfast', 'Эртең мененки тамак'),
    'Шведский стол в главном ресторане': (
        'Buffet in the main restaurant', 'Башкы ресторанда швед столу'),
    'Трансфер из Бишкека': ('Transfer from Bishkek', 'Бишкектен трансфер'),
    'Легковой автомобиль в одну сторону': ('One-way car transfer', 'Бир тарапка жеңил унаа'),
    'SPA-программа': ('Spa Programme', 'SPA-программа'),
    'Хаммам, бассейн и массаж': ('Hammam, pool and massage', 'Хаммам, бассейн жана массаж'),
}

# Какие поля переводим у каких моделей
FIELDS = [
    (SiteSettings, ('tagline', 'address', 'working_hours')),
    (HomeSlide, ('title', 'subtitle', 'button_text')),
    (Advantage, ('title', 'description')),
    (Amenity, ('name',)),
    (RoomCategory, ('name', 'beds')),
    (ServiceCategory, ('name',)),
    (Service, ('name', 'duration')),
    (ConferenceHall, ('name', 'equipment')),
    (SpecialOffer, ('title', 'subtitle')),
    (GalleryAlbum, ('title',)),
    (Post, ('title', 'excerpt')),
    (AboutSection, ('title', 'subtitle')),
    (StaticPage, ('title',)),
    (Addon, ('name', 'description')),
]

# Шаблоны, которые собираются из данных объекта, а не берутся из словаря
ROOM_DESCRIPTION = {
    'en': '{name} with a view over the resort grounds, up to {guests} guests.',
    'ky': 'Курорттун аймагына көрүнүшү бар {name}, {guests} конокко чейин.',
}
SERVICE_DESCRIPTION = {
    'en': '{name} — a service of Baytur Resort & Spa.',
    'ky': '{name} — Baytur Resort & Spa курортунун кызматы.',
}


class Command(BaseCommand):
    help = 'Заполняет en/ky версии демо-контента.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать уже заполненные переводы')

    def handle(self, *args, **options):
        self.force = options['force']
        total = 0
        missing = set()

        for model, fields in FIELDS:
            for obj in model.objects.all():
                changed = []
                for field in fields:
                    source = getattr(obj, field + '_ru', None) or getattr(obj, field, None)
                    if not source:
                        continue
                    pair = TEXTS.get(source.strip())
                    if not pair:
                        missing.add(source.strip()[:60])
                        continue
                    for lang, value in (('en', pair[0]), ('ky', pair[1])):
                        attr = '%s_%s' % (field, lang)
                        if getattr(obj, attr, None) and not self.force:
                            continue
                        setattr(obj, attr, value)
                        changed.append(attr)
                if changed:
                    obj.save(update_fields=changed)
                    total += len(changed)

        total += self.translate_descriptions()

        self.stdout.write(self.style.SUCCESS('Заполнено переводов: %s' % total))
        if missing:
            self.stdout.write(self.style.WARNING(
                'Нет перевода для: ' + '; '.join(sorted(missing)[:15])
            ))

    def translate_descriptions(self):
        """Короткие описания собираются по шаблону — переводим их отдельно."""
        count = 0

        for room in RoomCategory.objects.all():
            for lang, template in ROOM_DESCRIPTION.items():
                attr = 'short_description_' + lang
                if getattr(room, attr, None) and not self.force:
                    continue
                name = getattr(room, 'name_' + lang, None) or room.name
                setattr(room, attr, template.format(name=name, guests=room.max_guests))
                count += 1
            room.save()

        for service in Service.objects.all():
            for lang, template in SERVICE_DESCRIPTION.items():
                attr = 'short_description_' + lang
                if getattr(service, attr, None) and not self.force:
                    continue
                name = getattr(service, 'name_' + lang, None) or service.name
                setattr(service, attr, template.format(name=name))
                count += 1
            service.save()

        return count
