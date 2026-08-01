from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.base.seo import SEOMixin
from apps.contacts.forms import EventRequestForm
from apps.services.models import ConferenceHall, Service, ServiceCategory


class ServiceCategoryListView(SEOMixin, ListView):
    """SPA, бассейны, рестораны, спорткомплекс, детская зона, развлечения."""

    model = ServiceCategory
    template_name = 'pages/services/list.html'
    context_object_name = 'categories'
    meta_title = _('Услуги курорта — Baytur Resort & Spa')
    meta_description = _('SPA, бассейны, рестораны, спорткомплекс, детская зона и развлечения '
                         'курорта Baytur Resort & Spa.')

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True).prefetch_related('services')


class ServiceCategoryDetailView(SEOMixin, DetailView):
    model = ServiceCategory
    template_name = 'pages/services/category.html'
    context_object_name = 'category'

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = self.object.services.filter(is_active=True)
        return context


class ServiceDetailView(SEOMixin, DetailView):
    model = Service
    template_name = 'pages/services/detail.html'
    context_object_name = 'service'

    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related('category').prefetch_related('images')


class ConferenceHallListView(SEOMixin, ListView):
    """Конференц-залы: описание, вместимость, форма заявки (п. 4 ТЗ)."""

    model = ConferenceHall
    template_name = 'pages/services/halls.html'
    context_object_name = 'halls'
    meta_title = _('Конференц-залы и мероприятия — Baytur Resort & Spa')
    meta_description = _('Залы для конференций, банкетов и корпоративов на Иссык-Куле: '
                         'вместимость, оборудование, заявка онлайн.')

    def get_queryset(self):
        return ConferenceHall.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EventRequestForm()
        return context


class ConferenceHallDetailView(SEOMixin, DetailView):
    model = ConferenceHall
    template_name = 'pages/services/hall_detail.html'
    context_object_name = 'hall'

    def get_queryset(self):
        return ConferenceHall.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EventRequestForm(initial={'hall': self.object})
        return context
