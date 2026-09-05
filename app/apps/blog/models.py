from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SEOModel, SortableModel, TimeStampedModel


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True, published_at__lte=timezone.now())


class Post(SortableModel, SEOModel, TimeStampedModel):
    """Новости и статьи (п. 4 ТЗ — раздел «Отзывы / Блог»)."""

    class Meta:
        verbose_name = _('Статья')
        verbose_name_plural = _('Блог и новости')
        ordering = ('-published_at', '-id')

    title = models.CharField(_('Заголовок'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    excerpt = models.TextField(_('Краткое описание'), blank=True)
    content = RichTextUploadingField(_('Текст'), blank=True)
    cover = ResizedImageField(
        _('Обложка'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='blog/', blank=True, null=True,
    )
    published_at = models.DateTimeField(_('Дата публикации'), default=timezone.now, db_index=True)
    views = models.PositiveIntegerField(_('Просмотры'), default=0, editable=False)

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})


class Guest(SortableModel):
    """
    Гость курорта с фотографией и цитатой — блок «Наши гости».

    Отличается от отзыва: отзыв приходит с сайта или из карт и модерируется,
    а гостя добавляет администратор вручную. Цитата необязательна —
    карточка может быть просто фотографией с именем.
    """

    class Meta:
        verbose_name = _('Гость')
        verbose_name_plural = _('Наши гости')
        ordering = ('order', '-id')

    full_name = models.CharField(_('ФИО'), max_length=255)
    role = models.CharField(
        _('Кто это'), max_length=255, blank=True,
        help_text=_('Например: «Гость курорта, Алматы» или должность.'),
    )
    photo = ResizedImageField(
        _('Фото'), size=[800, 800], crop=['middle', 'center'], quality=88,
        upload_to='guests/', blank=True, null=True,
    )
    quote = models.TextField(
        _('Цитата'), blank=True,
        help_text=_('Необязательно. Карточка работает и без неё — '
                    'только фото и имя гостя.'),
    )

    def __str__(self):
        return str(self.full_name)


class Review(SortableModel, TimeStampedModel):
    """Отзывы гостей. Отзывы с сайта публикуются только после модерации."""

    class Source(models.TextChoices):
        SITE = 'site', _('Форма на сайте')
        BOOKING = 'booking', _('Booking.com')
        GOOGLE = 'google', _('Google')
        TWOGIS = '2gis', _('2GIS')
        MANUAL = 'manual', _('Добавлен вручную')

    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ('order', '-created_at')

    author_name = models.CharField(_('Имя автора'), max_length=255)
    author_city = models.CharField(_('Город / страна'), max_length=255, blank=True)
    avatar = ResizedImageField(
        _('Фото автора'), size=[200, 200], crop=['middle', 'center'], quality=85,
        upload_to='reviews/', blank=True, null=True,
    )
    rating = models.PositiveSmallIntegerField(_('Оценка (1–5)'), default=5)
    text = models.TextField(_('Текст отзыва'))
    source = models.CharField(_('Источник'), max_length=20, choices=Source.choices, default=Source.SITE)
    source_url = models.URLField(_('Ссылка на отзыв'), blank=True)

    # Идентификатор отзыва во внешнем сервисе. Нужен, чтобы повторный импорт
    # обновлял существующую запись, а не создавал дубль.
    external_id = models.CharField(
        _('ID во внешнем сервисе'), max_length=255, blank=True, db_index=True,
    )
    published_at = models.DateTimeField(_('Дата отзыва'), blank=True, null=True)

    is_approved = models.BooleanField(_('Одобрен к публикации'), default=False, db_index=True)
    show_on_home = models.BooleanField(_('Показывать на главной'), default=False)

    def __str__(self):
        return f'{self.author_name} — {self.rating}/5'
