from django.db.models import F, Max, Min
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.base.seo import SEOMixin
from apps.booking.forms import AvailabilitySearchForm
from apps.rooms.models import Amenity, RoomCategory


class RoomListView(SEOMixin, ListView):
    """Каталог номеров, люксов, коттеджей и вилл (п. 5.5 ТЗ)."""

    model = RoomCategory
    template_name = 'pages/rooms/list.html'
    context_object_name = 'rooms'
    paginate_by = 12
    meta_title = _('Номера и жильё — Baytur Resort & Spa')
    meta_description = _('Стандарты, полулюксы, люксы, коттеджи и виллы Baytur Resort & Spa. '
                         'Фото, вместимость, удобства и цены.')

    # Сортировки вынесены в словарь: так шаблон не может подставить в
    # order_by произвольное поле из адресной строки.
    SORTS = {
        'price': 'base_price',
        '-price': '-base_price',
        'area': '-area',
        'guests': '-capacity_adults',
    }

    def get_queryset(self):
        queryset = RoomCategory.objects.filter(is_active=True).prefetch_related('amenities', 'images')
        params = self.request.GET

        kind = params.get('kind')
        if kind:
            queryset = queryset.filter(kind=kind)

        # Вместимость: считаем сумму взрослых и детей, поэтому фильтруем
        # по вычисляемому полю, а не по одному из двух.
        guests = self._int(params.get('guests'))
        if guests:
            queryset = queryset.annotate(
                total_capacity=F('capacity_adults') + F('capacity_children'),
            ).filter(total_capacity__gte=guests)

        price_min = self._int(params.get('price_min'))
        if price_min:
            queryset = queryset.filter(base_price__gte=price_min)

        price_max = self._int(params.get('price_max'))
        if price_max:
            queryset = queryset.filter(base_price__lte=price_max)

        # Несколько удобств = И, а не ИЛИ: гость ждёт номер, где есть всё
        # отмеченное, поэтому фильтруем последовательно.
        amenities = [a for a in params.getlist('amenity') if a.isdigit()]
        for amenity_id in amenities:
            queryset = queryset.filter(amenities__id=amenity_id)
        if amenities:
            queryset = queryset.distinct()

        sort = params.get('sort')
        if sort in self.SORTS:
            queryset = queryset.order_by(self.SORTS[sort])

        return queryset

    @staticmethod
    def _int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET

        prices = RoomCategory.objects.filter(is_active=True).aggregate(
            low=Min('base_price'), high=Max('base_price'),
        )

        selected = [a for a in params.getlist('amenity') if a.isdigit()]

        context.update({
            'kinds': RoomCategory.Kind.choices,
            'active_kind': params.get('kind', ''),
            'search_form': AvailabilitySearchForm(params or None),
            'amenities': Amenity.objects.filter(is_active=True),
            'selected_amenities': [int(a) for a in selected],
            'price_low': prices['low'],
            'price_high': prices['high'],
            'active_guests': params.get('guests', ''),
            'active_price_min': params.get('price_min', ''),
            'active_price_max': params.get('price_max', ''),
            'active_sort': params.get('sort', ''),
            # Кнопка «сбросить» нужна только когда что-то выбрано
            'has_filters': any(
                params.get(key) for key in ('kind', 'guests', 'price_min', 'price_max', 'sort')
            ) or bool(selected),
        })
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
