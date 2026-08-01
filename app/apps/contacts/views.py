from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, FormView

from apps.base.seo import SEOMixin
from apps.booking.notifications import notify_request
from apps.contacts.forms import ContactForm, EventRequestForm, SubscribeForm


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class ContactsView(SEOMixin, CreateView):
    """Контакты: телефоны, карта, мессенджеры, форма связи (п. 4 ТЗ)."""

    form_class = ContactForm
    template_name = 'pages/contacts.html'
    success_url = reverse_lazy('contacts:index')
    meta_title = _('Контакты — Baytur Resort & Spa')
    meta_description = _('Телефоны, e-mail, адрес и карта проезда к курорту Baytur Resort & Spa, '
                         'с. Бостери, Иссык-Куль.')

    def get_meta_object(self):
        return None  # у формы нет SEO-полей, берём мета-теги вью

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.page_url = self.request.META.get('HTTP_REFERER', '')[:500]
        obj.language = self.request.LANGUAGE_CODE
        obj.ip_address = client_ip(self.request)
        obj.save()

        notify_request(obj, str(_('Новое обращение с сайта')))
        messages.success(self.request, _('Спасибо! Мы свяжемся с вами в ближайшее время.'))

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
        return super().form_invalid(form)


class EventRequestView(FormView):
    """Заявка на мероприятие / конференц-зал."""

    form_class = EventRequestForm
    template_name = 'pages/services/halls.html'
    success_url = reverse_lazy('services:halls')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.language = self.request.LANGUAGE_CODE
        obj.save()

        notify_request(obj, str(_('Новая заявка на мероприятие')))
        messages.success(self.request, _('Заявка отправлена. Менеджер свяжется с вами.'))

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
        messages.error(self.request, _('Проверьте правильность заполнения формы.'))
        return redirect(self.get_success_url())


class SubscribeView(FormView):
    """Подписка на спецпредложения — вызывается из подвала, обычно через AJAX."""

    form_class = SubscribeForm
    success_url = reverse_lazy('base:home')

    def form_valid(self, form):
        subscriber = form.save(commit=False)
        subscriber.language = self.request.LANGUAGE_CODE
        subscriber.save()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'message': str(_('Вы подписаны на спецпредложения.'))})
        messages.success(self.request, _('Вы подписаны на спецпредложения.'))
        return redirect(self.request.META.get('HTTP_REFERER', self.get_success_url()))

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
        messages.error(self.request, _('Проверьте правильность e-mail.'))
        return redirect(self.request.META.get('HTTP_REFERER', self.get_success_url()))
