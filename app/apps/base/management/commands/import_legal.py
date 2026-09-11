"""
Юридические страницы сайта: политика конфиденциальности и публичная оферта.

Тексты присланы Заказчиком в .docx и переведены на английский и кыргызский.
Хранятся файлами рядом с командой, а не в фикстуре: договоры правятся целыми
абзацами, и обычный diff по html читается, а по json — нет.

Русская редакция — юридически обязывающая, у переводов в конце стоит оговорка
об этом. Если Заказчик пришлёт новую редакцию, достаточно заменить файл и
прогнать команду с --force.
"""

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cms.models import StaticPage

DATA_DIR = Path(__file__).resolve().parent / 'data' / 'legal'

PAGES = [
    {
        'slug': 'privacy',
        'file': 'privacy',
        'order': 10,
        'title': {
            'ru': 'Политика конфиденциальности',
            'en': 'Privacy Policy',
            'ky': 'Купуялуулук саясаты',
        },
        'seo_description': {
            'ru': 'Как курорт Baytur Resort & Spa собирает, хранит и защищает '
                  'персональные данные гостей сайта.',
            'en': 'How Baytur Resort & Spa collects, stores and protects the '
                  'personal data of website guests.',
            'ky': 'Baytur Resort & Spa курорту сайттын конактарынын жеке '
                  'маалыматтарын кантип чогултат, сактайт жана коргойт.',
        },
    },
    {
        'slug': 'offer',
        'file': 'offer',
        'order': 20,
        'title': {
            'ru': 'Публичная оферта',
            'en': 'Public Offer',
            'ky': 'Ачык оферта',
        },
        'seo_description': {
            'ru': 'Условия оказания гостиничных услуг в курорте Baytur Resort & Spa: '
                  'бронирование, оплата, заезд и выезд, отмена и возврат.',
            'en': 'Terms of hotel services at Baytur Resort & Spa: booking, payment, '
                  'check-in and check-out, cancellation and refunds.',
            'ky': 'Baytur Resort & Spa курортунда мейманкана кызматтарын көрсөтүү '
                  'шарттары: брондоо, төлөө, кирүү жана чыгуу, жокко чыгаруу жана кайтаруу.',
        },
    },
]


class Command(BaseCommand):
    help = 'Загружает политику конфиденциальности и публичную оферту на трёх языках'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='Перезаписать страницы, которые уже есть в базе.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']

        for spec in PAGES:
            page = StaticPage.objects.filter(slug=spec['slug']).first()
            if page and not force:
                self.stdout.write(self.style.WARNING(
                    'Пропущено: /%s/ уже есть в базе (--force перезапишет)' % spec['slug']
                ))
                continue

            if page is None:
                page = StaticPage(slug=spec['slug'])

            for lang, title in spec['title'].items():
                setattr(page, 'title_%s' % lang, title)
                setattr(page, 'seo_title_%s' % lang, title)
                setattr(page, 'seo_description_%s' % lang, spec['seo_description'][lang])
                content = (DATA_DIR / ('%s.%s.html' % (spec['file'], lang))).read_text()
                setattr(page, 'content_%s' % lang, content)

            page.order = spec['order']
            page.is_active = True
            page.show_in_footer = True
            page.show_in_menu = False
            page.save()

            self.stdout.write(self.style.SUCCESS(
                '/%s/ — %s' % (spec['slug'], ', '.join(
                    '%s: %d символов' % (lang, len(getattr(page, 'content_%s' % lang) or ''))
                    for lang in spec['title']
                ))
            ))
