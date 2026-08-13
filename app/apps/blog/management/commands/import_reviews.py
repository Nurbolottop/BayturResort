"""
Импорт отзывов из Google Maps и 2ГИС.

Ограничения сервисов, о которых важно помнить:

* Google Places отдаёт максимум **5 отзывов** на точку — это лимит самого
  Google, обойти его легально нельзя. Отзывы приходят те, что Google считает
  наиболее полезными, поэтому набор со временем меняется сам.
* 2ГИС не публикует отзывы в открытом API: ключ выдаётся по партнёрскому
  договору. Пока ключа нет, отзывы 2ГИС заводятся вручную в админке — там же
  указывается ссылка на оригинал.

Парсинг страниц сервисов не используется: он нарушает их правила и ломается
при любом изменении вёрстки.

Запуск:
    python manage.py import_reviews                # все настроенные источники
    python manage.py import_reviews --source google
    python manage.py import_reviews --min-rating 5 # публиковать только «пятёрки»
"""

from datetime import datetime, timezone as dt_timezone

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.blog.models import Review

GOOGLE_URL = 'https://maps.googleapis.com/maps/api/place/details/json'
TWOGIS_URL = 'https://public-api.reviews.2gis.com/2.0/branches/{branch}/reviews'


class Command(BaseCommand):
    help = 'Забирает отзывы из Google Maps и 2ГИС.'

    def add_arguments(self, parser):
        parser.add_argument('--source', choices=('all', 'google', '2gis'), default='all')
        parser.add_argument(
            '--min-rating', type=int, default=4,
            help='Отзывы с оценкой не ниже публикуются сразу, остальные ждут '
                 'решения менеджера в админке. По умолчанию 4.',
        )
        parser.add_argument('--limit', type=int, default=20,
                            help='Сколько отзывов забирать из 2ГИС за раз.')

    def handle(self, *args, **options):
        self.config = settings.REVIEWS_IMPORT
        self.min_rating = options['min_rating']
        source = options['source']

        total = 0
        if source in ('all', 'google'):
            total += self.import_google()
        if source in ('all', '2gis'):
            total += self.import_2gis(options['limit'])

        self.stdout.write(self.style.SUCCESS('Готово. Обработано отзывов: %s' % total))

    # ------------------------------------------------------------- сохранение

    def save_review(self, *, external_id, source, author, text, rating, url, published_at, city=''):
        """Создаёт или обновляет отзыв. Ключ — источник + внешний ID."""
        if not text or not text.strip():
            return False

        defaults = {
            'author_name': author or 'Гость',
            'author_city': city,
            'text': text.strip(),
            'rating': max(1, min(5, int(rating or 5))),
            'source_url': url or '',
            'published_at': published_at,
        }

        review = Review.objects.filter(source=source, external_id=external_id).first()
        if review:
            for field, value in defaults.items():
                setattr(review, field, value)
            review.save()
            return False

        # Решение о публикации принимаем один раз, при создании: если менеджер
        # потом снял галочку, повторный импорт не должен её возвращать.
        Review.objects.create(
            source=source,
            external_id=external_id,
            is_approved=defaults['rating'] >= self.min_rating,
            show_on_home=defaults['rating'] >= self.min_rating,
            **defaults,
        )
        return True

    # ---------------------------------------------------------------- Google

    def import_google(self):
        key = self.config.get('GOOGLE_API_KEY')
        place_id = self.config.get('GOOGLE_PLACE_ID')

        if not key or not place_id:
            self.stdout.write(self.style.WARNING(
                'Google: не заданы GOOGLE_PLACES_API_KEY и GOOGLE_PLACE_ID — пропускаю.'
            ))
            return 0

        try:
            response = requests.get(GOOGLE_URL, timeout=self.config['TIMEOUT'], params={
                'place_id': place_id,
                'fields': 'name,url,rating,reviews',
                'reviews_sort': 'newest',
                'language': 'ru',
                'key': key,
            })
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            self.stderr.write('Google: не удалось получить отзывы — %s' % error)
            return 0

        status = data.get('status')
        if status != 'OK':
            self.stderr.write('Google вернул статус %s: %s' % (
                status, data.get('error_message', '')))
            return 0

        result = data.get('result', {})
        place_url = result.get('url', '')
        reviews = result.get('reviews', []) or []

        created = 0
        for item in reviews:
            timestamp = item.get('time')
            published = (
                datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)
                if timestamp else None
            )
            # Своего ID у отзыва в ответе нет — собираем стабильный ключ
            # из автора и времени публикации.
            external_id = '%s:%s' % (item.get('author_name', ''), timestamp or '')

            if self.save_review(
                external_id=external_id,
                source=Review.Source.GOOGLE,
                author=item.get('author_name'),
                text=item.get('text'),
                rating=item.get('rating'),
                url=item.get('author_url') or place_url,
                published_at=published,
            ):
                created += 1

        self.stdout.write('Google: получено %s, новых %s (лимит сервиса — 5).'
                          % (len(reviews), created))
        return len(reviews)

    # ----------------------------------------------------------------- 2ГИС

    def import_2gis(self, limit):
        key = self.config.get('TWOGIS_API_KEY')
        branch = self.config.get('TWOGIS_BRANCH_ID')

        if not key or not branch:
            self.stdout.write(self.style.WARNING(
                '2ГИС: не заданы TWOGIS_REVIEWS_KEY и TWOGIS_BRANCH_ID — пропускаю. '
                'Ключ выдаётся по партнёрскому договору; пока его нет, отзывы 2ГИС '
                'добавляются вручную в админке.'
            ))
            return 0

        try:
            response = requests.get(
                TWOGIS_URL.format(branch=branch),
                timeout=self.config['TIMEOUT'],
                params={'key': key, 'limit': limit, 'sort_by': 'date_created'},
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            self.stderr.write('2ГИС: не удалось получить отзывы — %s' % error)
            return 0

        reviews = data.get('reviews', []) or []
        created = 0
        for item in reviews:
            user = item.get('user', {}) or {}
            published = None
            raw_date = item.get('date_created')
            if raw_date:
                try:
                    published = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                except ValueError:
                    published = None

            if self.save_review(
                external_id=str(item.get('id', '')),
                source=Review.Source.TWOGIS,
                author=user.get('name'),
                text=item.get('text'),
                rating=item.get('rating'),
                url=item.get('url', ''),
                published_at=published,
            ):
                created += 1

        self.stdout.write('2ГИС: получено %s, новых %s.' % (len(reviews), created))
        return len(reviews)
