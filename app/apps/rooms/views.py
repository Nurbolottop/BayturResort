from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.base.seo import SEOMixin
from apps.booking.forms import AvailabilitySearchForm
from apps.rooms.models import RoomCategory


class RoomListView(SEOMixin, ListView):
    """Каталог номеров, люксов, коттеджей и вилл (п. 5.5 ТЗ)."""

    model = RoomCategory
    template_name = 'pages/rooms/list.html'
    context_object_name = 'rooms'
    paginate_by = 12
    meta_title = _('Номера и жильё — Baytur Resort & Spa')
    meta_description = _('Стандарты, полулюксы, люксы, коттеджи и виллы Baytur Resort & Spa. '
                         'Фото, вместимость, удобства и цены.')

    def get_queryset(self):
        queryset = RoomCategory.objects.filter(is_active=True).prefetch_related('amenities', 'images')
        kind = self.request.GET.get('kind')
        if kind:
            queryset = queryset.filter(kind=kind)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kinds'] = RoomCategory.Kind.choices
        context['active_kind'] = self.request.GET.get('kind', '')
        context['search_form'] = AvailabilitySearchForm(self.request.GET or None)
        return context


class RoomDetailView(SEOMixin, DetailView):
    model = RoomCategory
    template_name = 'pages/rooms/detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        return RoomCategory.objects.filter(is_active=True).prefetch_related('amenities', 'images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AvailabilitySearchForm(self.request.GET or None)
        context['similar_rooms'] = RoomCategory.objects.filter(
            is_active=True, kind=self.object.kind,
        ).exclude(pk=self.object.pk)[:3]
        return context
