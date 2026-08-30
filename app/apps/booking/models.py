from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from apps.base.models import SortableModel, TimeStampedModel


class Addon(SortableModel):
    """Допродажи при бронировании: трансфер, завтрак, SPA (п. 5.6 ТЗ)."""

    class PriceType(models.TextChoices):
        PER_BOOKING = 'booking', _('За бронь')
        PER_NIGHT = 'night', _('За ночь')
        PER_GUEST = 'guest', _('За гостя')
        PER_GUEST_NIGHT = 'guest_night', _('За гостя за ночь')

    class Meta:
        verbose_name = _('Дополнительная услуга')
        verbose_name_plural = _('Дополнительные услуги (при брони)')
        ordering = ('order', 'id')

    name = models.CharField(_('Название'), max_length=255)
    description = models.CharField(_('Описание'), max_length=500, blank=True)
    icon = models.FileField(_('Иконка'), upload_to='booking/addons/', blank=True, null=True)
    image = ResizedImageField(
        _('Фото'), size=[800, 600], crop=['middle', 'center'], quality=85,
        upload_to='booking/addons/', blank=True, null=True,
    )

    price = models.DecimalField(_('Цена, сом'), max_digits=10, decimal_places=2, default=0)
    price_type = models.CharField(
        _('Тип расчёта'), max_length=15, choices=PriceType.choices, default=PriceType.PER_BOOKING,
    )
    shelter_code = models.CharField(_('Код услуги в Shelter'), max_length=64, blank=True)

    def __str__(self):
        return str(self.name)

    def calculate_total(self, *, quantity, nights, guests):
        """Стоимость услуги для конкретной брони."""
        quantity = Decimal(quantity or 1)
        if self.price_type == self.PriceType.PER_NIGHT:
            multiplier = Decimal(nights)
        elif self.price_type == self.PriceType.PER_GUEST:
            multiplier = Decimal(guests)
        elif self.price_type == self.PriceType.PER_GUEST_NIGHT:
            multiplier = Decimal(guests) * Decimal(nights)
        else:
            multiplier = Decimal(1)
        return (self.price * multiplier * quantity).quantize(Decimal('0.01'))


class BookingRequest(TimeStampedModel):
    """
    Заявка на бронирование, отправленная в WhatsApp ресепшена.

    Онлайн-оплата и связка с PMS пока не подключены: Заказчик сначала хочет
    измерить спрос через сайт. Поэтому гость уходит в WhatsApp, а мы
    сохраняем запрос — по этим записям и считается количество обращений.
    """

    class Meta:
        verbose_name = _('Заявка на бронирование')
        verbose_name_plural = _('Заявки на бронирование')
        ordering = ('-created_at',)

    room_category = models.ForeignKey(
        'rooms.RoomCategory', verbose_name=_('Категория'), on_delete=models.SET_NULL,
        blank=True, null=True, related_name='requests',
    )
    room_category_name = models.CharField(
        _('Категория (снимок)'), max_length=255, blank=True,
        help_text=_('Сохраняем название на момент заявки — категорию могут переименовать.'),
    )

    check_in = models.DateField(_('Заезд'), blank=True, null=True)
    check_out = models.DateField(_('Выезд'), blank=True, null=True)
    nights = models.PositiveSmallIntegerField(_('Ночей'), default=0)
    adults = models.PositiveSmallIntegerField(_('Взрослых'), default=2)
    children = models.PositiveSmallIntegerField(_('Детей'), default=0)

    estimated_total = models.DecimalField(
        _('Расчётная сумма'), max_digits=12, decimal_places=2, default=0,
        help_text=_('Цена с сайта на момент заявки, не подтверждённая отелем.'),
    )

    source_page = models.CharField(_('Откуда отправлена'), max_length=255, blank=True)
    language = models.CharField(_('Язык сайта'), max_length=5, blank=True)
    ip_address = models.GenericIPAddressField(_('IP'), blank=True, null=True)
    user_agent = models.CharField(_('Браузер'), max_length=300, blank=True)

    is_processed = models.BooleanField(
        _('Обработана'), default=False, db_index=True,
        help_text=_('Отметка менеджера: с гостем связались.'),
    )
    comment = models.TextField(_('Комментарий менеджера'), blank=True)

    def __str__(self):
        return '%s — %s' % (self.room_category_name or _('без категории'),
                            self.created_at.strftime('%d.%m.%Y %H:%M'))


class Booking(TimeStampedModel):
    """
    Бронь, созданная на сайте (п. 5.1, 6.1 ТЗ).

    Наличие номеров сайт не ведёт — единый источник это PMS Shelter.
    В Shelter бронь записывается только после успешной оплаты, после чего
    статус становится CONFIRMED, а `shelter_reservation_id` заполняется.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        AWAITING_PAYMENT = 'awaiting_payment', _('Ожидает оплаты')
        PAID = 'paid', _('Оплачена')
        CONFIRMED = 'confirmed', _('Подтверждена (записана в Shelter)')
        PAYMENT_FAILED = 'payment_failed', _('Оплата не прошла')
        CANCELLED = 'cancelled', _('Отменена')
        EXPIRED = 'expired', _('Истекла')

    class Meta:
        verbose_name = _('Бронь')
        verbose_name_plural = _('Брони')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['status', '-created_at']),
        ]

    number = models.CharField(_('Номер брони'), max_length=32, unique=True, db_index=True)
    status = models.CharField(
        _('Статус'), max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True,
    )

    # Что бронируют
    room_category = models.ForeignKey(
        'rooms.RoomCategory', verbose_name=_('Категория номера'), on_delete=models.PROTECT,
        related_name='bookings',
    )
    room_category_name = models.CharField(
        _('Название категории (снимок)'), max_length=255, blank=True,
        help_text=_('Фиксируется на момент брони, чтобы переименование категории не искажало историю.'),
    )
    shelter_room_code = models.CharField(_('Код категории в Shelter'), max_length=64, blank=True)
    rooms_count = models.PositiveSmallIntegerField(_('Количество номеров'), default=1)

    # Даты и гости
    check_in = models.DateField(_('Заезд'), db_index=True)
    check_out = models.DateField(_('Выезд'), db_index=True)
    adults = models.PositiveSmallIntegerField(_('Взрослых'), default=2)
    children = models.PositiveSmallIntegerField(_('Детей'), default=0)
    children_ages = models.CharField(
        _('Возраст детей'), max_length=100, blank=True, help_text=_('Через запятую, например: 4, 9'),
    )

    # Гость
    guest_first_name = models.CharField(_('Имя'), max_length=150)
    guest_last_name = models.CharField(_('Фамилия'), max_length=150, blank=True)
    guest_phone = models.CharField(_('Телефон'), max_length=50)
    guest_email = models.EmailField(_('E-mail'))
    guest_country = models.CharField(_('Страна'), max_length=100, blank=True)
    comment = models.TextField(_('Пожелания гостя'), blank=True)

    # Деньги
    currency = models.CharField(_('Валюта'), max_length=3, default='KGS')
    room_total = models.DecimalField(_('Стоимость проживания'), max_digits=12, decimal_places=2, default=0)
    addons_total = models.DecimalField(_('Стоимость доп. услуг'), max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_('Скидка'), max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('Итого к оплате'), max_digits=12, decimal_places=2, default=0)
    prepay_amount = models.DecimalField(
        _('Сумма предоплаты'), max_digits=12, decimal_places=2, default=0,
        help_text=_('Сколько списывается онлайн. Может быть частью суммы брони.'),
    )
    paid_amount = models.DecimalField(_('Оплачено'), max_digits=12, decimal_places=2, default=0)

    promo_code = models.ForeignKey(
        'offers.PromoCode', verbose_name=_('Промокод'), on_delete=models.SET_NULL,
        blank=True, null=True, related_name='bookings',
    )
    special_offer = models.ForeignKey(
        'offers.SpecialOffer', verbose_name=_('Спецпредложение'), on_delete=models.SET_NULL,
        blank=True, null=True, related_name='bookings',
    )

    # Интеграция с Shelter
    shelter_reservation_id = models.CharField(
        _('ID брони в Shelter'), max_length=64, blank=True, db_index=True,
    )
    shelter_synced_at = models.DateTimeField(_('Записана в Shelter'), blank=True, null=True)
    shelter_error = models.TextField(
        _('Ошибка синхронизации с Shelter'), blank=True,
        help_text=_('Если заполнено — бронь оплачена, но не попала в PMS. Требует ручной обработки.'),
    )

    # Служебное
    language = models.CharField(_('Язык оформления'), max_length=5, blank=True)
    source = models.CharField(_('Источник'), max_length=50, default='website')
    ip_address = models.GenericIPAddressField(_('IP'), blank=True, null=True)
    confirmed_at = models.DateTimeField(_('Подтверждена'), blank=True, null=True)
    cancelled_at = models.DateTimeField(_('Отменена'), blank=True, null=True)
    admin_comment = models.TextField(_('Комментарий администратора'), blank=True)

    def __str__(self):
        return f'{self.number} — {self.room_category_name or self.room_category}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        if not self.room_category_name and self.room_category_id:
            self.room_category_name = str(self.room_category)
        if not self.shelter_room_code and self.room_category_id:
            self.shelter_room_code = self.room_category.shelter_code
        super().save(*args, **kwargs)

    @staticmethod
    def generate_number():
        from django.utils.crypto import get_random_string
        stamp = timezone.localtime().strftime('%y%m%d')
        return f'BR-{stamp}-{get_random_string(5).upper()}'

    @property
    def nights(self):
        if self.check_in and self.check_out:
            return max((self.check_out - self.check_in).days, 0)
        return 0

    @property
    def guests_total(self):
        return self.adults + self.children

    @property
    def guest_full_name(self):
        return f'{self.guest_first_name} {self.guest_last_name}'.strip()

    @property
    def amount_due(self):
        """Остаток к оплате на месте."""
        return max(self.total_amount - self.paid_amount, Decimal('0'))

    @property
    def is_paid(self):
        return self.status in (self.Status.PAID, self.Status.CONFIRMED)

    def recalculate_totals(self):
        """Пересчитывает итоги из позиций. Не сохраняет объект."""
        self.addons_total = sum(
            (item.total for item in self.addons.all()), Decimal('0'),
        )
        subtotal = self.room_total + self.addons_total
        self.total_amount = max(subtotal - self.discount_amount, Decimal('0'))
        return self.total_amount


class BookingAddon(models.Model):
    class Meta:
        verbose_name = _('Доп. услуга в брони')
        verbose_name_plural = _('Доп. услуги в брони')

    booking = models.ForeignKey(
        Booking, verbose_name=_('Бронь'), on_delete=models.CASCADE, related_name='addons',
    )
    addon = models.ForeignKey(
        Addon, verbose_name=_('Услуга'), on_delete=models.PROTECT, related_name='booking_items',
    )
    name = models.CharField(_('Название (снимок)'), max_length=255, blank=True)
    quantity = models.PositiveSmallIntegerField(_('Количество'), default=1)
    price = models.DecimalField(_('Цена за единицу'), max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(_('Сумма'), max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.name or self.addon} × {self.quantity}'

    def save(self, *args, **kwargs):
        if not self.name and self.addon_id:
            self.name = str(self.addon)
        super().save(*args, **kwargs)


class Payment(TimeStampedModel):
    """Платёж через FreedomPay (п. 5.3, 6.3 ТЗ). Данные карт на сайте не хранятся."""

    class Status(models.TextChoices):
        CREATED = 'created', _('Создан')
        PENDING = 'pending', _('Ожидает подтверждения')
        SUCCESS = 'success', _('Успешно')
        FAILED = 'failed', _('Ошибка')
        CANCELLED = 'cancelled', _('Отменён')
        REFUNDED = 'refunded', _('Возвращён')

    class Meta:
        verbose_name = _('Платёж')
        verbose_name_plural = _('Платежи')
        ordering = ('-created_at',)

    booking = models.ForeignKey(
        Booking, verbose_name=_('Бронь'), on_delete=models.CASCADE, related_name='payments',
    )
    provider = models.CharField(_('Провайдер'), max_length=30, default='freedompay')
    order_id = models.CharField(_('Order ID'), max_length=64, unique=True, db_index=True)
    external_id = models.CharField(_('ID платежа у провайдера'), max_length=64, blank=True, db_index=True)

    amount = models.DecimalField(_('Сумма'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Валюта'), max_length=3, default='KGS')
    status = models.CharField(
        _('Статус'), max_length=15, choices=Status.choices, default=Status.CREATED, db_index=True,
    )

    payment_url = models.URLField(_('Ссылка на оплату'), max_length=1000, blank=True)
    error_message = models.CharField(_('Текст ошибки'), max_length=500, blank=True)

    request_data = models.JSONField(_('Запрос'), blank=True, null=True)
    response_data = models.JSONField(_('Ответ'), blank=True, null=True)
    callback_data = models.JSONField(_('Колбэк'), blank=True, null=True)

    paid_at = models.DateTimeField(_('Оплачен'), blank=True, null=True)

    def __str__(self):
        return f'{self.order_id} — {self.amount} {self.currency} ({self.get_status_display()})'
