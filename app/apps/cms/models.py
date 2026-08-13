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


class Mission(models.Model):
    """
    Миссия и цели курорта — первый блок страницы «О нас».

    Запись всегда одна: это не список блоков, а вступление ко всей странице,
    поэтому модель одиночная, как настройки сайта.
    """

    class Meta:
        verbose_name = _('Миссия и цели')
        verbose_name_plural = _('Миссия и цели')

    is_active = models.BooleanField(_('Показывать на сайте'), default=True)

    eyebrow = models.CharField(
        _('Надпись над заголовком'), max_length=120, blank=True,
        help_text=_('Например: «Наш замысел».'),
    )
    title = models.CharField(_('Заголовок'), max_length=255, default=_('Миссия и цели'))
    statement = models.TextField(
        _('Миссия'), blank=True,
        help_text=_('Одна-две ёмкие фразы. Выводится крупно, как цитата.'),
    )
    content = RichTextUploadingField(
        _('Текст под миссией'), blank=True,
        help_text=_('Необязательно: развёрнутое пояснение.'),
    )
    image = ResizedImageField(
        _('Изображение'), size=[1600, 1067], crop=['middle', 'center'], quality=85,
        upload_to='about/', blank=True, null=True,
    )

    def __str__(self):
        return str(self.title)

    @classmethod
    def get_solo(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class MissionGoal(SortableModel):
    """Отдельная цель в блоке «Миссия и цели»."""

    class Meta:
        verbose_name = _('Цель')
        verbose_name_plural = _('Цели')
        ordering = ('order', 'id')

    mission = models.ForeignKey(
        Mission, verbose_name=_('Блок'), on_delete=models.CASCADE, related_name='goals',
    )
    title = models.CharField(_('Цель'), max_length=255)
    description = models.CharField(_('Пояснение'), max_length=500, blank=True)

    def __str__(self):
        return str(self.title)


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
