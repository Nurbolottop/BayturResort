from django.db import migrations, models

AMENITIES_HELP = ('По одному в строке: бассейн, пляж, SPA, Wi-Fi, парковка. '
                  'Выводятся в разметку для поисковиков и ИИ-поиска.')
AMENITIES_LABEL = 'Удобства курорта'


class Migration(migrations.Migration):
    """Координаты, звёздность, число номеров и список удобств — для микроразметки."""

    dependencies = [
        ('base', '0008_sitesettings_events_extras_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='latitude',
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True,
                help_text='Из Google Maps: правый клик по точке — первое число. Например 42.631234',
                verbose_name='Широта'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='longitude',
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True,
                help_text='Второе число из той же подсказки. Например 77.152345',
                verbose_name='Долгота'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='star_rating',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                help_text='Официальная категория. Если не присвоена — оставьте пустым.',
                verbose_name='Звёздность'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='rooms_total',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                help_text='Общее количество номеров на курорте.',
                verbose_name='Всего номеров'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='amenities',
            field=models.TextField(blank=True, help_text=AMENITIES_HELP, verbose_name=AMENITIES_LABEL),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='amenities_en',
            field=models.TextField(blank=True, null=True, help_text=AMENITIES_HELP, verbose_name=AMENITIES_LABEL),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='amenities_ky',
            field=models.TextField(blank=True, null=True, help_text=AMENITIES_HELP, verbose_name=AMENITIES_LABEL),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='amenities_ru',
            field=models.TextField(blank=True, null=True, help_text=AMENITIES_HELP, verbose_name=AMENITIES_LABEL),
        ),
    ]
