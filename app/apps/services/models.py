from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SEOModel, SortableModel, TimeStampedModel


class ServiceCategory(SortableModel):
    """SPA, бассейны, рестораны, спорткомплекс, детская зона, развлечения (п. 5 ТЗ)."""

    class Meta:
        verbose_name = _('Категория услуг')
        verbose_name_plural = _('Категории услуг')
        ordering = ('order', 'id')

    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    icon = models.FileField(_('Иконка'), upload_to='services/icons/', blank=True, null=True)
    cover = ResizedImageField(
        _('Обложка'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='services/covers/', blank=True, null=True,
    )

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('services:category', kwargs={'slug': self.slug})


class Service(SortableModel, SEOModel, TimeStampedModel):
    class Meta:
        verbose_name = _('Услуга')
        verbose_name_plural = _('Услуги')
        ordering = ('order', 'id')

    category = models.ForeignKey(
        ServiceCategory, verbose_name=_('Категория'), on_delete=models.CASCADE, related_name='services',
    )
    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    short_description = models.CharField(_('Краткое описание'), max_length=500, blank=True)
    description = RichTextUploadingField(_('Описание'), blank=True)
    cover = ResizedImageField(
        _('Фото'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='services/', blank=True, null=True,
    )
    price = models.DecimalField(_('Цена, сом'), max_digits=10, decimal_places=2, blank=True, null=True)
    price_note = models.CharField(_('Примечание к цене'), max_length=255, blank=True)
    duration = models.CharField(_('Длительность'), max_length=100, blank=True)
    show_on_home = models.BooleanField(_('Показывать на главной'), default=False)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('services:detail', kwargs={'slug': self.slug})


class ServiceImage(SortableModel):
    class Meta:
        verbose_name = _('Фото услуги')
        verbose_name_plural = _('Фото услуги')
        ordering = ('order', 'id')

    service = models.ForeignKey(
        Service, verbose_name=_('Услуга'), on_delete=models.CASCADE, related_name='images',
    )
    image = ResizedImageField(_('Фото'), size=[1600, 1067], quality=85, upload_to='services/gallery/')
    alt = models.CharField(_('Alt-текст'), max_length=255, blank=True)

    def __str__(self):
        return f'{self.service} — {self.pk}'


class ConferenceHall(SortableModel, SEOModel, TimeStampedModel):
    """Конференц-залы: описание, вместимость, форма заявки (п. 4 ТЗ)."""

    class Meta:
        verbose_name = _('Конференц-зал')
        verbose_name_plural = _('Конференц-залы')
        ordering = ('order', 'id')

    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    description = RichTextUploadingField(_('Описание'), blank=True)
    cover = ResizedImageField(
        _('Фото'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='halls/', blank=True, null=True,
    )

    area = models.DecimalField(_('Площадь, м²'), max_digits=7, decimal_places=1, blank=True, null=True)
    capacity_theatre = models.PositiveSmallIntegerField(_('Театр, чел.'), blank=True, null=True)
    capacity_banquet = models.PositiveSmallIntegerField(_('Банкет, чел.'), blank=True, null=True)
    capacity_classroom = models.PositiveSmallIntegerField(_('Класс, чел.'), blank=True, null=True)
    capacity_ushape = models.PositiveSmallIntegerField(_('П-образно, чел.'), blank=True, null=True)

    equipment = models.TextField(_('Оборудование'), blank=True)
    price_from = models.DecimalField(_('Цена от, сом'), max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('services:hall_detail', kwargs={'slug': self.slug})
