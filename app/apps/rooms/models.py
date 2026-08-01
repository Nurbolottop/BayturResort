from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SEOModel, SortableModel, TimeStampedModel


class Amenity(SortableModel):
    """Удобство номера: Wi-Fi, кондиционер, балкон, вид на озеро и т.д."""

    class Meta:
        verbose_name = _('Удобство')
        verbose_name_plural = _('Удобства')
        ordering = ('order', 'id')

    name = models.CharField(_('Название'), max_length=120)
    icon = models.FileField(_('Иконка'), upload_to='rooms/amenities/', blank=True, null=True)

    def __str__(self):
        return str(self.name)


class RoomCategory(SortableModel, SEOModel, TimeStampedModel):
    """
    Категория размещения (п. 5.5 ТЗ): стандарт, полулюкс, люкс, делюкс,
    президентский, семейный, коттедж, вилла.

    Наличие и актуальная цена берутся из PMS Shelter по `shelter_code`;
    `base_price` — витринная цена «от», показывается пока даты не выбраны.
    """

    class Kind(models.TextChoices):
        STANDARD = 'standard', _('Стандарт')
        SEMI_LUX = 'semi_lux', _('Полулюкс')
        LUX = 'lux', _('Люкс')
        DELUXE = 'deluxe', _('Делюкс')
        PRESIDENT = 'president', _('Президентский')
        FAMILY = 'family', _('Семейный')
        COTTAGE = 'cottage', _('Коттедж')
        VILLA = 'villa', _('Вилла')
        YURT = 'yurt', _('Юрта')

    class Meta:
        verbose_name = _('Категория номера')
        verbose_name_plural = _('Номера и жильё')
        ordering = ('order', 'id')

    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    kind = models.CharField(_('Тип размещения'), max_length=20, choices=Kind.choices, default=Kind.STANDARD)

    short_description = models.CharField(_('Краткое описание'), max_length=500, blank=True)
    description = RichTextUploadingField(_('Описание'), blank=True)

    cover = ResizedImageField(
        _('Обложка'), size=[1600, 1067], crop=['middle', 'center'], quality=85,
        upload_to='rooms/covers/', blank=True, null=True,
    )

    # Вместимость и параметры
    capacity_adults = models.PositiveSmallIntegerField(_('Взрослых (макс.)'), default=2)
    capacity_children = models.PositiveSmallIntegerField(_('Детей (макс.)'), default=0)
    area = models.DecimalField(_('Площадь, м²'), max_digits=6, decimal_places=1, blank=True, null=True)
    beds = models.CharField(_('Кровати'), max_length=255, blank=True)
    rooms_count = models.PositiveSmallIntegerField(_('Комнат'), default=1)

    # Цена
    base_price = models.DecimalField(
        _('Цена от, сом/ночь'), max_digits=10, decimal_places=2, default=0,
        help_text=_('Витринная цена. Точная цена на выбранные даты приходит из Shelter.'),
    )

    amenities = models.ManyToManyField(Amenity, verbose_name=_('Удобства'), blank=True, related_name='room_categories')

    # Интеграция с PMS
    shelter_code = models.CharField(
        _('Код категории в Shelter'), max_length=64, blank=True, db_index=True,
        help_text=_('Идентификатор категории номера в PMS Shelter. Без него бронирование недоступно.'),
    )
    total_rooms = models.PositiveSmallIntegerField(
        _('Всего номеров категории'), default=0,
        help_text=_('Резервное значение, если Shelter недоступен.'),
    )

    is_bookable = models.BooleanField(_('Доступно к бронированию'), default=True)
    show_on_home = models.BooleanField(_('Показывать на главной'), default=False)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('rooms:detail', kwargs={'slug': self.slug})

    @property
    def max_guests(self):
        return self.capacity_adults + self.capacity_children


class RoomImage(SortableModel):
    class Meta:
        verbose_name = _('Фото номера')
        verbose_name_plural = _('Фото номера')
        ordering = ('order', 'id')

    category = models.ForeignKey(
        RoomCategory, verbose_name=_('Категория'), on_delete=models.CASCADE, related_name='images',
    )
    image = ResizedImageField(
        _('Фото'), size=[1600, 1067], quality=85, upload_to='rooms/gallery/',
    )
    alt = models.CharField(_('Alt-текст'), max_length=255, blank=True)

    def __str__(self):
        return f'{self.category} — {self.pk}'
