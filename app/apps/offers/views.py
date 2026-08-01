from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.base.seo import SEOMixin
from apps.booking.forms import AvailabilitySearchForm
from apps.offers.models import SpecialOffer


class OfferListView(SEOMixin, ListView):
    """Акции, пакеты, сезонные тарифы (п. 4 ТЗ)."""

    model = SpecialOffer
    template_name = 'pages/offers/list.html'
    context_object_name = 'offers'
    paginate_by = 12
    meta_title = _('Спецпредложения и акции — Baytur Resort & Spa')
    meta_description = _('Пакеты «проживание + SPA», завтраки, сезонные тарифы и промокоды '
                         'курорта Baytur Resort & Spa.')

    def get_queryset(self):
        return [o for o in SpecialOffer.objects.filter(is_active=True) if o.is_running]


class OfferDetailView(SEOMixin, DetailView):
    model = SpecialOffer
    template_name = 'pages/offers/detail.html'
    context_object_name = 'offer'

    def get_queryset(self):
        return SpecialOffer.objects.filter(is_active=True).prefetch_related('room_categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AvailabilitySearchForm()
        return context
