from decimal import Decimal

from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SEOModel, SortableModel, TimeStampedModel


class SpecialOffer(SortableModel, SEOModel, TimeStampedModel):
    """Акции и пакеты: проживание + SPA / завтрак, сезонные тарифы (п. 5.6 ТЗ)."""

    class Meta:
        verbose_name = _('Спецпредложение')
        verbose_name_plural = _('Спецпредложения')
        ordering = ('order', '-id')

    title = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL'), max_length=255, unique=True)
    subtitle = models.CharField(_('Подзаголовок'), max_length=500, blank=True)
    description = RichTextUploadingField(_('Описание'), blank=True)
    cover = ResizedImageField(
        _('Фото'), size=[1600, 900], crop=['middle', 'center'], quality=85,
        upload_to='offers/', blank=True, null=True,
    )

    price = models.DecimalField(_('Цена по акции, сом'), max_digits=10, decimal_places=2, blank=True, null=True)
    old_price = models.DecimalField(_('Цена без скидки, сом'), max_digits=10, decimal_places=2, blank=True, null=True)

    valid_from = models.DateField(_('Действует с'), blank=True, null=True)
    valid_to = models.DateField(_('Действует до'), blank=True, null=True)

    room_categories = models.ManyToManyField(
        'rooms.RoomCategory', verbose_name=_('Применимо к категориям'), blank=True, related_name='offers',
    )
    promo_code = models.ForeignKey(
        'offers.PromoCode', verbose_name=_('Промокод'), on_delete=models.SET_NULL,
        blank=True, null=True, related_name='offers',
    )

    show_on_home = models.BooleanField(_('Показывать на главной'), default=True)

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('offers:detail', kwargs={'slug': self.slug})

    @property
    def is_running(self):
        today = timezone.localdate()
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        return self.is_active

    @property
    def discount_percent(self):
        if self.price and self.old_price and self.old_price > 0:
            return int(round((1 - self.price / self.old_price) * 100))
        return None


class PromoCode(TimeStampedModel):
    """Промокоды и скидки (п. 5.6 ТЗ)."""

    class DiscountType(models.TextChoices):
        PERCENT = 'percent', _('Процент')
        FIXED = 'fixed', _('Фиксированная сумма')

    class Meta:
        verbose_name = _('Промокод')
        verbose_name_plural = _('Промокоды')
        ordering = ('-id',)

    code = models.CharField(_('Код'), max_length=64, unique=True, db_index=True)
    comment = models.CharField(_('Комментарий'), max_length=255, blank=True)

    discount_type = models.CharField(
        _('Тип скидки'), max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT,
    )
    value = models.DecimalField(_('Размер скидки'), max_digits=10, decimal_places=2, default=0)

    valid_from = models.DateField(_('Действует с'), blank=True, null=True)
    valid_to = models.DateField(_('Действует до'), blank=True, null=True)

    min_nights = models.PositiveSmallIntegerField(_('Минимум ночей'), default=1)
    min_amount = models.DecimalField(_('Минимальная сумма брони'), max_digits=10, decimal_places=2, default=0)

    max_uses = models.PositiveIntegerField(
        _('Лимит применений'), default=0, help_text=_('0 — без ограничений'),
    )
    used_count = models.PositiveIntegerField(_('Использован раз'), default=0, editable=False)

    room_categories = models.ManyToManyField(
        'rooms.RoomCategory', verbose_name=_('Только для категорий'), blank=True, related_name='promo_codes',
        help_text=_('Пусто — действует на все категории.'),
    )

    is_active = models.BooleanField(_('Активен'), default=True, db_index=True)

    def __str__(self):
        return str(self.code)

    def clean(self):
        if self.discount_type == self.DiscountType.PERCENT and not (0 < self.value <= 100):
            raise ValidationError({'value': _('Процент скидки должен быть от 1 до 100.')})

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def check_availability(self, *, amount, nights, room_category=None):
        """Возвращает (ok: bool, error: str). Проверяет все условия применения."""
        today = timezone.localdate()

        if not self.is_active:
            return False, _('Промокод неактивен.')
        if self.valid_from and today < self.valid_from:
            return False, _('Промокод ещё не действует.')
        if self.valid_to and today > self.valid_to:
            return False, _('Срок действия промокода истёк.')
        if self.max_uses and self.used_count >= self.max_uses:
            return False, _('Лимит применений промокода исчерпан.')
        if nights < self.min_nights:
            return False, _('Промокод действует при бронировании от %(n)s ночей.') % {'n': self.min_nights}
        if self.min_amount and amount < self.min_amount:
            return False, _('Промокод действует при сумме от %(s)s сом.') % {'s': self.min_amount}
        if room_category and self.room_categories.exists():
            if not self.room_categories.filter(pk=room_category.pk).exists():
                return False, _('Промокод не применим к выбранной категории.')
        return True, ''

    def calculate_discount(self, amount):
        """Сумма скидки для указанной суммы брони."""
        amount = Decimal(amount)
        if self.discount_type == self.DiscountType.PERCENT:
            discount = amount * self.value / Decimal('100')
        else:
            discount = self.value
        return min(discount, amount).quantize(Decimal('0.01'))
