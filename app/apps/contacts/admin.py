import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from apps.contacts.models import ContactRequest, EventRequest, Subscriber


class ExportCsvMixin:
    export_fields = ()

    @admin.action(description=_('Выгрузить выбранное в CSV'))
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        model_name = queryset.model._meta.model_name
        response['Content-Disposition'] = f'attachment; filename={model_name}.csv'
        response.write('﻿')  # BOM, чтобы Excel не ломал кириллицу

        writer = csv.writer(response, delimiter=';')
        writer.writerow([queryset.model._meta.get_field(f).verbose_name for f in self.export_fields])
        for obj in queryset:
            writer.writerow([self._display(obj, f) for f in self.export_fields])
        return response

    @staticmethod
    def _display(obj, field_name):
        display = getattr(obj, f'get_{field_name}_display', None)
        value = display() if display else getattr(obj, field_name, '')
        return '' if value is None else str(value)


@admin.register(ContactRequest)
class ContactRequestAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'email', 'message')
    readonly_fields = ('name', 'phone', 'email', 'message', 'page_url', 'language',
                       'ip_address', 'created_at', 'updated_at')
    actions = ('export_csv',)
    export_fields = ('created_at', 'name', 'phone', 'email', 'message', 'status')

    def has_add_permission(self, request):
        return False


@admin.register(EventRequest)
class EventRequestAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'event_type', 'event_date', 'guests_count', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'event_type', 'event_date')
    search_fields = ('name', 'company', 'phone', 'email', 'comment')
    readonly_fields = ('name', 'company', 'phone', 'email', 'event_type', 'hall', 'event_date',
                       'guests_count', 'need_accommodation', 'comment', 'language',
                       'created_at', 'updated_at')
    actions = ('export_csv',)
    export_fields = ('created_at', 'name', 'company', 'phone', 'email', 'event_type',
                     'event_date', 'guests_count', 'status')

    def has_add_permission(self, request):
        return False


@admin.register(Subscriber)
class SubscriberAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ('email', 'name', 'language', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'language')
    search_fields = ('email', 'name')
    actions = ('export_csv',)
    export_fields = ('created_at', 'email', 'name', 'language', 'is_active')
