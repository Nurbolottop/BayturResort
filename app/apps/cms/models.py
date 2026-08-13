from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SEOModel, SortableModel, TimeStampedModel


class StaticPage(SortableModel, SEOModel, TimeStampedModel):
    """
    Служебные и текстовые страницы: политика конфиденциальности, оферта,
    правила проживания, «О нас» (п. 4 ТЗ). Всё в HTML, без PDF.
    """

    class Meta:
        verbose_name = _('Страница')
        verbose_name_plural = _('Страницы сайта')
        ordering = ('order', 'id')

    title = models.CharField(_('Заголовок'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    content = RichTextUploadingField(_('Содержимое'), blank=True)
    cover = ResizedImageField(
        _('Обложка'), size=[1920, 800], crop=['middle', 'center'], quality=85,
        upload_to='pages/', blank=True, null=True,
    )

    show_in_footer = models.BooleanField(_('Показывать в подвале'), default=False)
    show_in_menu = models.BooleanField(_('Показывать в меню'), default=False)

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('cms:page', kwargs={'slug': self.slug})


class AboutSection(SortableModel):
    """Блок на странице «О нас»: история, миссия, инфраструктура, юрточный городок."""

    class Meta:
        verbose_name = _('Блок «О нас»')
        verbose_name_plural = _('Страница «О нас»')
        ordering = ('order', 'id')

    title = models.CharField(_('Заголовок'), max_length=255)
    subtitle = models.CharField(_('Подзаголовок'), max_length=500, blank=True)
    content = RichTextUploadingField(_('Текст'), blank=True)
    image = ResizedImageField(
        _('Изображение'), size=[1600, 1067], crop=['middle', 'center'], quality=85,
        upload_to='about/', blank=True, null=True,
    )
    image_position = models.CharField(
        _('Положение изображения'), max_length=10, default='right',
        choices=(('left', _('Слева')), ('right', _('Справа'))),
    )

    def __str__(self):
        return str(self.title)
