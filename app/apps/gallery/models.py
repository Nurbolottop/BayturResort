from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SEOModel, SortableModel, TimeStampedModel


class GalleryAlbum(SortableModel, SEOModel, TimeStampedModel):
    class Meta:
        verbose_name = _('Альбом')
        verbose_name_plural = _('Галерея')
        ordering = ('order', 'id')

    title = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    cover = ResizedImageField(
        _('Обложка'), size=[1600, 1067], crop=['middle', 'center'], quality=85,
        upload_to='gallery/covers/', blank=True, null=True,
    )

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('gallery:album', kwargs={'slug': self.slug})


class GalleryImage(SortableModel):
    class Meta:
        verbose_name = _('Фото')
        verbose_name_plural = _('Фото')
        ordering = ('order', 'id')

    album = models.ForeignKey(
        GalleryAlbum, verbose_name=_('Альбом'), on_delete=models.CASCADE, related_name='images',
    )
    image = ResizedImageField(_('Фото'), size=[1920, 1280], quality=85, upload_to='gallery/')
    title = models.CharField(_('Подпись'), max_length=255, blank=True)
    alt = models.CharField(_('Alt-текст'), max_length=255, blank=True)

    def __str__(self):
        return str(self.title or self.pk)


class Video(SortableModel):
    class Meta:
        verbose_name = _('Видео')
        verbose_name_plural = _('Видео')
        ordering = ('order', 'id')

    title = models.CharField(_('Название'), max_length=255)
    url = models.URLField(_('Ссылка (YouTube / mp4)'))
    poster = ResizedImageField(
        _('Постер'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='gallery/videos/', blank=True, null=True,
    )

    def __str__(self):
        return str(self.title)


class VirtualTour(SortableModel):
    """3D-тур (kuula.co или аналог) — п. 12 ТЗ."""

    class Meta:
        verbose_name = _('3D-тур')
        verbose_name_plural = _('3D-туры')
        ordering = ('order', 'id')

    title = models.CharField(_('Название'), max_length=255)
    embed_url = models.URLField(_('Ссылка для встраивания (iframe src)'))
    poster = ResizedImageField(
        _('Превью'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='gallery/tours/', blank=True, null=True,
    )
    show_on_home = models.BooleanField(_('Показывать на главной'), default=False)

    def __str__(self):
        return str(self.title)
