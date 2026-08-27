"""
Демо-наполнение блока «Наши гости» на странице отзывов.

Фото берутся из media/import (выгрузка с текущего сайта). Реальных гостей
с их согласием на публикацию добавляет Заказчик через админку.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.blog.models import Guest

IMPORT_DIR = Path(settings.MEDIA_ROOT) / 'import'

GUESTS = [
    {
        'full_name': 'Айгуль Осмонова',
        'role': ('Гость курорта, Бишкек', 'Resort guest, Bishkek', 'Курорттун коногу, Бишкек'),
        'quote': (
            'Приезжаем всей семьёй третий год подряд. Дети не вылезают из бассейна, '
            'а мы наконец-то отдыхаем по-настоящему.',
            'We have been coming as a family for three years running. The kids never '
            'leave the pool, and we finally get real rest.',
            'Үч жылдан бери бүт үй-бүлө менен келебиз. Балдар бассейнден чыкпайт, '
            'биз болсо чыныгы эс алабыз.',
        ),
        'photo': '48.jpg',
    },
    {
        'full_name': 'Данияр Сапаров',
        'role': ('Гость курорта, Алматы', 'Resort guest, Almaty', 'Курорттун коногу, Алматы'),
        'quote': (
            'Проводили здесь корпоратив на 80 человек. Зал, питание, размещение — '
            'всё взяли на себя, мне осталось только приехать.',
            'We held a corporate event here for 80 people. The hall, catering and '
            'rooms were all handled — I just had to show up.',
            'Бул жерде 80 кишиге корпоратив өткөрдүк. Зал, тамак-аш, жайгаштыруу — '
            'баарын өздөрү уюштурду.',
        ),
        'photo': '54.jpg',
    },
    {
        'full_name': 'Elena Volkova',
        'role': ('Гость курорта, Москва', 'Resort guest, Moscow', 'Курорттун коногу, Москва'),
        'quote': (
            'Юрточный городок — отдельное впечатление. Такого сочетания комфорта '
            'и национального колорита я не встречала нигде.',
            'The yurt camp is an experience of its own. I have not seen this blend of '
            'comfort and national character anywhere else.',
            'Боз үй шаарчасы — өзүнчө таасир. Мындай ыңгайлуулук менен улуттук '
            'колориттин айкалышын эч жерден көргөн эмесмин.',
        ),
        'photo': '61.jpg',
    },
]


class Command(BaseCommand):
    help = 'Наполняет блок «Наши гости» демо-данными (ru/en/ky).'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Перезаписать существующих')

    def handle(self, *args, **options):
        if Guest.objects.exists() and not options['force']:
            self.stdout.write('Гости уже добавлены — пропускаю.')
            return

        if options['force']:
            Guest.objects.all().delete()

        for order, item in enumerate(GUESTS):
            guest = Guest(full_name=item['full_name'], order=order)
            for lang, role, quote in zip(('ru', 'en', 'ky'), item['role'], item['quote']):
                setattr(guest, 'role_%s' % lang, role)
                setattr(guest, 'quote_%s' % lang, quote)

            path = IMPORT_DIR / item['photo']
            if path.exists():
                with path.open('rb') as fh:
                    guest.photo.save(path.name, File(fh), save=False)
            guest.save()

        self.stdout.write(self.style.SUCCESS('Добавлено гостей: %s' % Guest.objects.count()))
        self.stdout.write('Это демо-данные. Реальных гостей заказчик добавляет в админке '
                          'с их согласия на публикацию фото и имени.')
