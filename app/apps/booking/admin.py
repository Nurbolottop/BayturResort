import csv

from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from apps.booking.models import BookingRequest, Addon, Booking, BookingAddon, Payment


@admin.register(Addon)
class AddonAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'price', 'price_type', 'shelter_code', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('price_type', 'is_active')
    search_fields = ('name',)


class BookingAddonInline(admin.TabularInline):
    model = BookingAddon
    extra = 0
    readonly_fields = ('addon', 'name', 'quantity', 'price', 'total')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('order_id', 'external_id', 'amount', 'currency', 'status',
                       'error_message', 'paid_at', 'created_at')
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'status_badge', 'room_category_name', 'check_in', 'check_out',
        'nights_display', 'guest_full_name', 'guest_phone', 'total_amount',
        'paid_amount', 'shelter_state', 'created_at',
    )
    list_filter = ('status', 'check_in', 'room_category', 'created_at')
    search_fields = ('number', 'guest_first_name', 'guest_last_name', 'guest_phone',
                     'guest_email', 'shelter_reservation_id')
    date_hierarchy = 'check_in'
    inlines = (BookingAddonInline, PaymentInline)
    actions = ('export_csv', 'retry_shelter_sync')

    readonly_fields = (
        'number', 'room_category_name', 'shelter_room_code', 'nights_display',
        'shelter_reservation_id', 'shelter_synced_at', 'shelter_error',
        'paid_amount', 'ip_address', 'language', 'source',
        'confirmed_at', 'cancelled_at', 'created_at', 'updated_at',
    )

    fieldsets = (
        (None, {
            'fields': ('number', 'status', 'admin_comment'),
        }),
        (_('Проживание'), {
            'fields': ('room_category', 'room_category_name', 'rooms_count',
                       'check_in', 'check_out', 'nights_display'),
        }),
        (_('Гости'), {
            'fields': ('guest_first_name', 'guest_last_name', 'guest_phone', 'guest_email',
                       'guest_country', 'adults', 'children', 'children_ages', 'comment'),
        }),
        (_('Деньги'), {
            'fields': ('currency', 'room_total', 'addons_total', 'discount_amount',
                       'total_amount', 'prepay_amount', 'paid_amount',
                       'promo_code', 'special_offer'),
        }),
        (_('PMS Shelter'), {
            'fields': ('shelter_room_code', 'shelter_reservation_id', 'shelter_synced_at', 'shelter_error'),
        }),
        (_('Служебное'), {
            'fields': ('source', 'language', 'ip_address', 'confirmed_at', 'cancelled_at',
                       'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        """Брони создаются гостями на сайте, вручную их не заводят."""
        return False

    @admin.display(description=_('Ночей'))
    def nights_display(self, obj):
        return obj.nights

    @admin.display(description=_('Статус'), ordering='status')
    def status_badge(self, obj):
        colors = {
            Booking.Status.DRAFT: '#9e9e9e',
            Booking.Status.AWAITING_PAYMENT: '#f0a30a',
            Booking.Status.PAID: '#1e88e5',
            Booking.Status.CONFIRMED: '#2e7d32',
            Booking.Status.PAYMENT_FAILED: '#c62828',
            Booking.Status.CANCELLED: '#616161',
            Booking.Status.EXPIRED: '#616161',
        }
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;'
            'font-size:11px;white-space:nowrap;">{}</span>',
            colors.get(obj.status, '#9e9e9e'), obj.get_status_display(),
        )

    @admin.display(description='Shelter')
    def shelter_state(self, obj):
        if obj.shelter_reservation_id:
            return format_html('<span style="color:#2e7d32;">✓ {}</span>', obj.shelter_reservation_id)
        if obj.shelter_error:
            return format_html('<span style="color:#c62828;" title="{}">⚠ ошибка</span>', obj.shelter_error)
        return '—'

    @admin.action(description=_('Повторить запись брони в Shelter'))
    def retry_shelter_sync(self, request, queryset):
        from apps.booking.services import push_booking_to_shelter

        ok = failed = 0
        for booking in queryset.filter(status__in=(Booking.Status.PAID, Booking.Status.CONFIRMED)):
            if booking.shelter_reservation_id:
                continue
            if push_booking_to_shelter(booking):
                ok += 1
            else:
                failed += 1

        self.message_user(
            request,
            _('Записано в Shelter: %(ok)s, с ошибкой: %(failed)s') % {'ok': ok, 'failed': failed},
            messages.SUCCESS if not failed else messages.WARNING,
        )

    @admin.action(description=_('Выгрузить брони в CSV'))
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename=bookings.csv'
        response.write('﻿')

        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'Номер', 'Статус', 'Категория', 'Заезд', 'Выезд', 'Ночей', 'Номеров',
            'Взрослых', 'Детей', 'Гость', 'Телефон', 'E-mail',
            'Итого', 'Оплачено', 'Валюта', 'ID в Shelter', 'Создана',
        ])
        for b in queryset.select_related('room_category'):
            writer.writerow([
                b.number, b.get_status_display(), b.room_category_name,
                b.check_in, b.check_out, b.nights, b.rooms_count,
                b.adults, b.children, b.guest_full_name, b.guest_phone, b.guest_email,
                b.total_amount, b.paid_amount, b.currency,
                b.shelter_reservation_id, b.created_at.strftime('%d.%m.%Y %H:%M'),
            ])
        return response


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'booking', 'amount', 'currency', 'status', 'external_id', 'paid_at', 'created_at')
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('order_id', 'external_id', 'booking__number')
    readonly_fields = [f.name for f in Payment._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    """Заявки с сайта. Нужны, чтобы измерить спрос до покупки модуля брони."""

    list_display = ('created_at', 'room_category_name', 'check_in', 'check_out',
                    'nights', 'adults', 'children', 'estimated_total', 'is_processed')
    list_filter = ('is_processed', 'created_at', 'room_category', 'language')
    list_editable = ('is_processed',)
    search_fields = ('room_category_name', 'comment')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'room_category', 'room_category_name',
                       'check_in', 'check_out', 'nights', 'adults', 'children',
                       'estimated_total', 'source_page', 'language', 'ip_address', 'user_agent')

    fieldsets = (
        (None, {
            'fields': ('created_at', 'room_category', 'room_category_name',
                       'check_in', 'check_out', 'nights', 'adults', 'children',
                       'estimated_total'),
        }),
        ('Обработка', {
            'fields': ('is_processed', 'comment'),
        }),
        ('Технические данные', {
            'fields': ('source_page', 'language', 'ip_address', 'user_agent', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False
