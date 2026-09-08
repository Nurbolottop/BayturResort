from django.db import migrations, models


class Migration(migrations.Migration):
    """Индекс по IP: по нему считается почасовой лимит заявок."""

    dependencies = [
        ('booking', '0002_bookingrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingrequest',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, db_index=True, null=True, verbose_name='IP'),
        ),
    ]
