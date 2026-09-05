"""
Заполняет раздел «Наши гости».

Данные готовятся заранее и лежат в data/guests.json: имя, подпись и файл
с фотографией. Фотографии кладутся в media/guests_src/ — команда переносит
их в поле модели, где Django сам приводит их к нужному размеру.

Цитаты не заполняются: карточка гостя — это фото и имя.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.blog.models import Guest

DATA_FILE = Path(__file__).parent / 'data' / 'guests.json'
SOURCE_DIR = Path(settings.MEDIA_ROOT) / 'guests_src'


class Command(BaseCommand):
    help = 'Заполняет раздел «Наши гости» из data/guests.json.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать фото у уже существующих гостей')
        parser.add_argument('--clear', action='store_true',
                            help='Удалить всех гостей перед загрузкой')

    def handle(self, *args, **options):
        if not DATA_FILE.exists():
            self.stderr.write('Нет файла со списком: %s' % DATA_FILE)
            return

        if options['clear']:
            removed = Guest.objects.all().delete()[0]
            self.stdout.write('  удалено прежних записей: %s' % removed)

        items = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        missing = []

        for order, item in enumerate(items):
            guest, created = Guest.objects.update_or_create(
                full_name=item['full_name'],
                defaults={'role': item.get('role', ''), 'order': order},
            )

            photo = SOURCE_DIR / item['photo'] if item.get('photo') else None
            if photo and photo.exists():
                if not guest.photo or options['force']:
                    with photo.open('rb') as fh:
                        guest.photo.save(photo.name, File(fh), save=True)
            elif item.get('photo'):
                missing.append(item['photo'])

            self.stdout.write('  %-30s %s' % (
                item['full_name'], 'добавлен' if created else 'обновлён'))

        if missing:
            self.stdout.write(self.style.WARNING(
                'Нет файлов с фото: %s' % ', '.join(missing)))

        self.stdout.write(self.style.SUCCESS(
            'Гостей в разделе: %s' % Guest.objects.count()))
