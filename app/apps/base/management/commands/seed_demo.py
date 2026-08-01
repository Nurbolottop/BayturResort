"""
Демо-наполнение для показа вёрстки до получения реального контента от Заказчика.

Только для разработки. Данные помечены как демонстрационные и удаляются
командой `python manage.py seed_demo --clear`.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.base.models import Advantage, SiteSettings
from apps.blog.models import Post, Review
from apps.booking.models import Addon
from apps.cms.models import AboutSection, StaticPage
from apps.gallery.models import GalleryAlbum, VirtualTour
from apps.offers.models import PromoCode, SpecialOffer
from apps.rooms.models import Amenity, RoomCategory
from apps.services.models import ConferenceHall, Service, ServiceCategory


class Command(BaseCommand):
    help = 'Наполняет сайт демонстрационным контентом (только для разработки).'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Удалить демо-данные')

    def handle(self, *args, **options):
        if options['clear']:
            return self.clear()

        self.stdout.write('Наполняю сайт демо-контентом...')

        site = SiteSettings.get_solo()
        site.site_name = 'Baytur Resort & Spa'
        site.tagline = 'Курорт на северном берегу Иссык-Куля'
        site.phone = '+996 (700) 00-00-00'
        site.phone_extra = '+996 (555) 00-00-00'
        site.email = 'info@baytur.kg'
        site.address = 'Кыргызстан, Иссык-Кульская обл., с. Бостери'
        site.working_hours = 'Ресепшен работает круглосуточно'
        site.whatsapp = '+996700000000'
        site.instagram = 'https://instagram.com/'
        site.legal_name = 'ОсОО «Байтур Резорт»'
        site.seo_description = (
            'Baytur Resort & Spa — курорт на берегу Иссык-Куля: номера и коттеджи, '
            'SPA, бассейны, рестораны, конференц-залы. Онлайн-бронирование.'
        )
        site.save()

        for order, (title, text) in enumerate([
            ('Свой пляж 300 м', 'Песчаный берег и чистая вода в шаговой доступности от номера.'),
            ('SPA и бассейны', 'Крытый и открытый бассейны, хаммам, сауна, массаж.'),
            ('Питание', 'Рестораны национальной и европейской кухни, детское меню.'),
            ('Для детей', 'Детский клуб, анимация, площадки и мелкий бассейн.'),
        ]):
            Advantage.objects.get_or_create(title=title, defaults={'description': text, 'order': order})

        amenities = {}
        for name in ['Wi-Fi', 'Кондиционер', 'Балкон', 'Вид на озеро', 'Мини-бар', 'Сейф', 'Телевизор', 'Фен']:
            amenities[name], _ = Amenity.objects.get_or_create(name=name)

        rooms = [
            ('standard', 'Стандарт', RoomCategory.Kind.STANDARD, 4500, 2, 0, 22, '1 двуспальная', 20),
            ('semi-lux', 'Полулюкс', RoomCategory.Kind.SEMI_LUX, 7200, 2, 1, 34, '1 двуспальная + диван', 12),
            ('lux', 'Люкс', RoomCategory.Kind.LUX, 11500, 2, 2, 48, '1 двуспальная + 2 односпальные', 8),
            ('family', 'Семейный', RoomCategory.Kind.FAMILY, 13800, 4, 2, 55, '2 двуспальные', 6),
            ('cottage', 'Коттедж у озера', RoomCategory.Kind.COTTAGE, 24000, 6, 3, 110, '3 спальни', 4),
            ('yurt', 'Юрта в юрточном городке', RoomCategory.Kind.YURT, 6000, 4, 2, 30, 'Топчаны', 10),
        ]
        for order, (slug, name, kind, price, adults, children, area, beds, total) in enumerate(rooms):
            room, created = RoomCategory.objects.get_or_create(slug=slug, defaults={
                'name': name, 'kind': kind, 'base_price': Decimal(price),
                'capacity_adults': adults, 'capacity_children': children,
                'area': Decimal(area), 'beds': beds, 'total_rooms': total,
                'shelter_code': slug.upper(), 'order': order,
                'show_on_home': order < 3,
                'short_description': f'{name} с видом на территорию курорта, до {adults + children} гостей.',
            })
            if created:
                room.amenities.set(amenities.values())

        services = [
            ('spa', 'SPA и wellness', [('Общий массаж', 2500, '60 минут'), ('Хаммам', 1500, '90 минут')]),
            ('pools', 'Бассейны', [('Открытый бассейн', 0, 'Для гостей курорта')]),
            ('restaurants', 'Рестораны', [('Ужин по меню', 1200, '')]),
            ('sport', 'Спорткомплекс', [('Тренажёрный зал', 500, '')]),
            ('kids', 'Детская зона', [('Детский клуб', 0, 'Для гостей курорта')]),
        ]
        for order, (slug, name, items) in enumerate(services):
            category, _ = ServiceCategory.objects.get_or_create(slug=slug, defaults={'name': name, 'order': order})
            for i, (title, price, note) in enumerate(items):
                Service.objects.get_or_create(slug=f'{slug}-{i}', defaults={
                    'category': category, 'name': title,
                    'price': Decimal(price) if price else None,
                    'duration': note, 'order': i,
                    'short_description': f'{title} — услуга курорта Baytur Resort & Spa.',
                })

        ConferenceHall.objects.get_or_create(slug='grand-hall', defaults={
            'name': 'Большой конференц-зал', 'area': Decimal('220'),
            'capacity_theatre': 200, 'capacity_banquet': 150, 'capacity_classroom': 90, 'capacity_ushape': 60,
            'equipment': 'Проектор, экран, звук, микрофоны, флипчарт', 'price_from': Decimal('25000'),
        })
        ConferenceHall.objects.get_or_create(slug='small-hall', defaults={
            'name': 'Малый зал', 'area': Decimal('70'), 'order': 1,
            'capacity_theatre': 60, 'capacity_banquet': 40, 'capacity_classroom': 30,
            'equipment': 'ТВ-панель, флипчарт', 'price_from': Decimal('9000'),
        })

        promo, _ = PromoCode.objects.get_or_create(code='BAYTUR10', defaults={
            'comment': 'Демонстрационный промокод −10%',
            'discount_type': PromoCode.DiscountType.PERCENT, 'value': Decimal('10'),
        })

        today = timezone.localdate()
        SpecialOffer.objects.get_or_create(slug='spa-package', defaults={
            'title': 'Проживание + SPA', 'subtitle': '2 ночи в люксе и посещение SPA для двоих',
            'price': Decimal('21000'), 'old_price': Decimal('26000'),
            'valid_from': today, 'valid_to': today + timedelta(days=90),
            'promo_code': promo, 'show_on_home': True,
        })
        SpecialOffer.objects.get_or_create(slug='early-booking', defaults={
            'title': 'Раннее бронирование', 'subtitle': 'Скидка 10% при брони за 30 дней',
            'price': Decimal('4050'), 'old_price': Decimal('4500'), 'order': 1,
            'valid_from': today, 'valid_to': today + timedelta(days=180), 'show_on_home': True,
        })

        for order, (slug, title) in enumerate([
            ('territory', 'Территория курорта'),
            ('rooms', 'Номера'),
            ('spa', 'SPA и бассейны'),
        ]):
            GalleryAlbum.objects.get_or_create(slug=slug, defaults={'title': title, 'order': order})

        VirtualTour.objects.get_or_create(title='3D-тур по курорту', defaults={
            'embed_url': 'https://kuula.co/share/collection/example', 'show_on_home': True,
        })

        Post.objects.get_or_create(slug='otkrytie-sezona', defaults={
            'title': 'Открытие пляжного сезона',
            'excerpt': 'Рассказываем, что нового ждёт гостей на Иссык-Куле этим летом.',
            'content': '<p>Демо-текст новости. Замените реальным контентом.</p>',
        })

        for i, (name, city, text) in enumerate([
            ('Айгуль', 'Бишкек', 'Отдыхали семьёй, детям очень понравился бассейн и анимация. Вернёмся ещё.'),
            ('Данияр', 'Алматы', 'Чистый пляж, вкусная кухня, вежливый персонал. Рекомендую.'),
            ('Elena', 'Москва', 'Прекрасный вид на озеро из номера, отличный SPA. Спасибо за отдых!'),
        ]):
            Review.objects.get_or_create(author_name=name, defaults={
                'author_city': city, 'text': text, 'rating': 5,
                'is_approved': True, 'show_on_home': True, 'order': i,
            })

        AboutSection.objects.get_or_create(title='О курорте', defaults={
            'subtitle': 'Иссык-Куль, с. Бостери',
            'content': '<p>Демо-текст о курорте. Замените реальным описанием от Заказчика.</p>',
        })

        for order, (slug, title) in enumerate([
            ('privacy', 'Политика конфиденциальности'),
            ('offer', 'Публичная оферта'),
            ('rules', 'Правила проживания'),
        ]):
            StaticPage.objects.get_or_create(slug=slug, defaults={
                'title': title, 'show_in_footer': True, 'order': order,
                'content': '<p>Демо-текст. Замените юридическим текстом.</p>',
            })

        for order, (name, price, price_type, description) in enumerate([
            ('Завтрак', 600, Addon.PriceType.PER_GUEST_NIGHT, 'Шведский стол в главном ресторане'),
            ('Трансфер из Бишкека', 5000, Addon.PriceType.PER_BOOKING, 'Легковой автомобиль в одну сторону'),
            ('SPA-программа', 3500, Addon.PriceType.PER_GUEST, 'Хаммам, бассейн и массаж'),
        ]):
            Addon.objects.get_or_create(name=name, defaults={
                'price': Decimal(price), 'price_type': price_type,
                'description': description, 'order': order,
            })

        self.stdout.write(self.style.SUCCESS('Демо-контент добавлен.'))
        self.stdout.write('Фото не загружены — карточки будут без изображений, это ожидаемо.')

    def clear(self):
        for model in (Addon, Review, Post, StaticPage, AboutSection, VirtualTour,
                      GalleryAlbum, SpecialOffer, PromoCode, ConferenceHall,
                      Service, ServiceCategory, RoomCategory, Amenity, Advantage):
            deleted, _ = model.objects.all().delete()
            self.stdout.write(f'{model.__name__}: удалено {deleted}')
        self.stdout.write(self.style.SUCCESS('Демо-данные удалены.'))
