from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import TimeStampedModel


class RequestStatus(models.TextChoices):
    NEW = 'new', _('Новая')
    IN_PROGRESS = 'in_progress', _('В работе')
    DONE = 'done', _('Обработана')
    SPAM = 'spam', _('Спам')


class ContactRequest(TimeStampedModel):
    """Заявка из формы обратной связи (п. 5.7 ТЗ)."""

    class Meta:
        verbose_name = _('Обращение')
        verbose_name_plural = _('Обращения')
        ordering = ('-created_at',)

    name = models.CharField(_('Имя'), max_length=255)
    phone = models.CharField(_('Телефон'), max_length=50)
    email = models.EmailField(_('E-mail'), blank=True)
    message = models.TextField(_('Сообщение'), blank=True)

    status = models.CharField(
        _('Статус'), max_length=20, choices=RequestStatus.choices, default=RequestStatus.NEW, db_index=True,
    )
    admin_comment = models.TextField(_('Комментарий администратора'), blank=True)

    page_url = models.CharField(_('Страница отправки'), max_length=500, blank=True)
    language = models.CharField(_('Язык'), max_length=5, blank=True)
    ip_address = models.GenericIPAddressField(_('IP'), blank=True, null=True)

    def __str__(self):
        return f'{self.name} — {self.phone}'


class EventRequest(TimeStampedModel):
    """Заявка на мероприятие / конференц-зал (п. 5.7 ТЗ)."""

    class EventType(models.TextChoices):
        CONFERENCE = 'conference', _('Конференция / семинар')
        BANQUET = 'banquet', _('Банкет')
        WEDDING = 'wedding', _('Свадьба')
        CORPORATE = 'corporate', _('Корпоратив')
        OTHER = 'other', _('Другое')

    class Meta:
        verbose_name = _('Заявка на мероприятие')
        verbose_name_plural = _('Заявки на мероприятия')
        ordering = ('-created_at',)

    name = models.CharField(_('Контактное лицо'), max_length=255)
    company = models.CharField(_('Компания'), max_length=255, blank=True)
    phone = models.CharField(_('Телефон'), max_length=50)
    email = models.EmailField(_('E-mail'), blank=True)

    event_type = models.CharField(
        _('Тип мероприятия'), max_length=20, choices=EventType.choices, default=EventType.CONFERENCE,
    )
    hall = models.ForeignKey(
        'services.ConferenceHall', verbose_name=_('Зал'), on_delete=models.SET_NULL,
        blank=True, null=True, related_name='requests',
    )
    event_date = models.DateField(_('Дата мероприятия'), blank=True, null=True)
    guests_count = models.PositiveIntegerField(_('Количество гостей'), blank=True, null=True)
    need_accommodation = models.BooleanField(_('Нужно размещение'), default=False)
    comment = models.TextField(_('Комментарий'), blank=True)

    status = models.CharField(
        _('Статус'), max_length=20, choices=RequestStatus.choices, default=RequestStatus.NEW, db_index=True,
    )
    admin_comment = models.TextField(_('Комментарий администратора'), blank=True)
    language = models.CharField(_('Язык'), max_length=5, blank=True)

    def __str__(self):
        return f'{self.name} — {self.get_event_type_display()}'


class Subscriber(TimeStampedModel):
    """Подписка на спецпредложения (п. 5.7 ТЗ)."""

    class Meta:
        verbose_name = _('Подписчик')
        verbose_name_plural = _('Подписчики')
        ordering = ('-created_at',)

    email = models.EmailField(_('E-mail'), unique=True)
    name = models.CharField(_('Имя'), max_length=255, blank=True)
    language = models.CharField(_('Язык'), max_length=5, blank=True)
    is_active = models.BooleanField(_('Активна'), default=True)

    def __str__(self):
        return str(self.email)
