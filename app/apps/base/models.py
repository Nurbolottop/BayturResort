from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField


# =============================================================================
# АБСТРАКТНЫЕ МОДЕЛИ (переиспользуются во всех приложениях)
# =============================================================================

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)

    class Meta:
        abstract = True


class SortableModel(models.Model):
    order = models.PositiveIntegerField(_('Порядок'), default=0, db_index=True)
    is_active = models.BooleanField(_('Активно'), default=True, db_index=True)

    class Meta:
        abstract = True


class SEOModel(models.Model):
    """Мета-теги для каждой страницы и каждой языковой версии (п. 9 ТЗ)."""

    seo_title = models.CharField(_('SEO: title'), max_length=255, blank=True)
    seo_description = models.TextField(_('SEO: description'), blank=True)
    seo_keywords = models.CharField(_('SEO: keywords'), max_length=255, blank=True)
    og_image = ResizedImageField(
        _('Изображение для соцсетей (OG)'),
        size=[1200, 630], crop=['middle', 'center'], quality=85,
        upload_to='seo/', blank=True, null=True,
    )

    class Meta:
        abstract = True

    def get_seo_title(self):
        return self.seo_title or str(self)

    def get_seo_description(self):
        return self.seo_description


# =============================================================================
# НАСТРОЙКИ САЙТА (одна запись, редактируется в админке)
# =============================================================================

class SiteSettings(SEOModel):
    class Meta:
        verbose_name = _('Настройки сайта')
        verbose_name_plural = _('Настройки сайта')

    # Идентичность
    site_name = models.CharField(_('Название сайта'), max_length=255, default='Baytur Resort & Spa')
    tagline = models.CharField(_('Слоган'), max_length=255, blank=True)
    logo = models.ImageField(_('Логотип'), upload_to='site/', blank=True, null=True)
    logo_light = models.ImageField(_('Логотип (светлый)'), upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(_('Favicon'), upload_to='site/', blank=True, null=True)

    # Контакты
    phone = models.CharField(_('Телефон'), max_length=50, blank=True)
    phone_extra = models.CharField(_('Дополнительный телефон'), max_length=50, blank=True)
    email = models.EmailField(_('E-mail'), blank=True)
    address = models.CharField(_('Адрес'), max_length=255, blank=True)
    working_hours = models.CharField(_('Часы работы ресепшена'), max_length=255, blank=True)

    # Всплывающее окно с акциями. Показывается один раз и с задержкой:
    # окно, которое выскакивает сразу и на каждой странице, гости
    # закрывают не читая, а часть уходит с сайта.
    popup_enabled = models.BooleanField(
        _('Показывать окно с акциями'), default=False,
        help_text=_('Окно появляется только если есть действующие акции.'),
    )
    popup_title = models.CharField(
        _('Заголовок окна'), max_length=255, blank=True,
        help_text=_('По умолчанию — «Специальные предложения».'),
    )
    popup_text = models.CharField(_('Подпись в окне'), max_length=500, blank=True)
    popup_delay = models.PositiveSmallIntegerField(
        _('Задержка перед показом, сек'), default=4,
        help_text=_('Даём гостю осмотреться. Рекомендуем 3–6 секунд.'),
    )
    popup_repeat_days = models.PositiveSmallIntegerField(
        _('Не показывать повторно, дней'), default=7,
        help_text=_('Сколько дней не показывать окно тому, кто его закрыл. 0 — показывать каждый раз.'),
    )
    popup_limit = models.PositiveSmallIntegerField(
        _('Сколько акций показывать'), default=3,
    )

    # Виртуальный тур. Ссылка внешняя (kuula.co) и одна на все языки —
    # выводится кнопкой в шапке, подвале и на странице галереи.
    tour_url = models.URLField(
        _('Ссылка на 3D-тур'), max_length=1000, blank=True,
        help_text=_('Внешняя ссылка на виртуальный тур. Кнопка «3D-тур» '
                    'появляется в шапке, подвале и в галерее, если поле заполнено.'),
    )

    # Карты и мессенджеры
    map_embed = models.TextField(_('Карта (iframe Google Maps / 2GIS)'), blank=True)
    # По клику на адрес гость выбирает карту сам: на телефоне система иначе
    # открывает приложение по умолчанию, а в Кыргызстане это чаще 2ГИС,
    # но не у всех.
    map_google_url = models.URLField(
        _('Ссылка на Google Maps'), max_length=500, blank=True,
        help_text=_('Открывается по клику на адрес.'),
    )
    map_2gis_url = models.URLField(
        _('Ссылка на 2ГИС'), max_length=500, blank=True,
        help_text=_('Открывается по клику на адрес.'),
    )
    whatsapp = models.CharField(_('WhatsApp (номер или ссылка)'), max_length=255, blank=True)
    # Заявки с сайта уходят на ресепшен, а он не обязан совпадать с общим
    # номером для вопросов — поэтому отдельное поле с запасным вариантом.
    booking_whatsapp = models.CharField(
        _('WhatsApp ресепшена для заявок'), max_length=255, blank=True,
        help_text=_('Куда уходят заявки на бронирование. Если пусто — берётся общий WhatsApp.'),
    )
    telegram = models.CharField(_('Telegram'), max_length=255, blank=True)
    instagram = models.URLField(_('Instagram'), blank=True)
    facebook = models.URLField(_('Facebook'), blank=True)
    youtube = models.URLField(_('YouTube'), blank=True)
    tiktok = models.URLField(_('TikTok'), blank=True)

    # Реквизиты
    legal_name = models.CharField(_('Юридическое лицо'), max_length=255, blank=True)
    requisites = models.TextField(_('Реквизиты'), blank=True)

    # Аналитика и подтверждение прав
    google_analytics_id = models.CharField(_('Google Analytics ID'), max_length=50, blank=True)
    google_site_verification = models.CharField(_('Google Search Console'), max_length=255, blank=True)
    yandex_metrika_id = models.CharField(_('Яндекс.Метрика ID'), max_length=50, blank=True)

    # Бронирование
    booking_rules = RichTextUploadingField(_('Правила бронирования'), blank=True)
    check_in_time = models.CharField(_('Время заезда'), max_length=20, default='14:00')
    check_out_time = models.CharField(_('Время выезда'), max_length=20, default='12:00')

    def __str__(self):
        return str(self.site_name)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_('Настройки сайта удалять нельзя.'))

    @classmethod
    def get_solo(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


# =============================================================================
# ГЛАВНАЯ СТРАНИЦА
# =============================================================================

class HomeSlide(SortableModel):
    """Слайд первого экрана главной страницы."""

    class Meta:
        verbose_name = _('Слайд на главной')
        verbose_name_plural = _('Слайды на главной')
        ordering = ('order', 'id')

    title = models.CharField(_('Заголовок'), max_length=255)
    subtitle = models.CharField(_('Подзаголовок'), max_length=500, blank=True)
    image = ResizedImageField(
        _('Изображение'), size=[1920, 1080], quality=85, upload_to='home/slides/',
    )
    video_url = models.URLField(_('Ссылка на видео (mp4/YouTube)'), blank=True)
    button_text = models.CharField(_('Текст кнопки'), max_length=100, blank=True)
    button_url = models.CharField(_('Ссылка кнопки'), max_length=255, blank=True)

    def __str__(self):
        return str(self.title)


class Advantage(SortableModel):
    """Преимущество курорта — блок «Почему мы» на главной."""

    class Meta:
        verbose_name = _('Преимущество')
        verbose_name_plural = _('Преимущества')
        ordering = ('order', 'id')

    title = models.CharField(_('Заголовок'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    icon = models.FileField(_('Иконка (SVG/PNG)'), upload_to='home/icons/', blank=True, null=True)

    def __str__(self):
        return str(self.title)
