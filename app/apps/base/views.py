from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from apps.base.models import Advantage, HomeSlide
from apps.base.seo import SEOMixin
from apps.blog.models import Post, Review
from apps.booking.forms import AvailabilitySearchForm
from apps.cms.models import AboutSection
from apps.gallery.models import GalleryAlbum, VirtualTour
from apps.offers.models import SpecialOffer
from apps.rooms.models import RoomCategory
from apps.services.models import ServiceCategory


class HomeView(SEOMixin, TemplateView):
    """Главная: презентация, преимущества, блок брони, номера, услуги, отзывы (п. 4 ТЗ)."""

    template_name = 'pages/home.html'
    meta_title = _('Baytur Resort & Spa — отдых на Иссык-Куле, с. Бостери')
    meta_description = _(
        'Курорт Baytur Resort & Spa на берегу Иссык-Куля: номера и коттеджи, SPA, '
        'бассейны, рестораны, конференц-залы. Онлайн-бронирование с подтверждением на e-mail.'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'slides': HomeSlide.objects.filter(is_active=True),
            'advantages': Advantage.objects.filter(is_active=True),
            'search_form': AvailabilitySearchForm(),
            'rooms': RoomCategory.objects.filter(
                is_active=True, show_on_home=True,
            ).prefetch_related('amenities')[:6],
            'service_categories': ServiceCategory.objects.filter(is_active=True)[:6],
            'offers': SpecialOffer.objects.filter(is_active=True, show_on_home=True)[:3],
            'reviews': Review.objects.filter(is_approved=True, show_on_home=True)[:6],
            'albums': GalleryAlbum.objects.filter(is_active=True)[:4],
            'virtual_tour': VirtualTour.objects.filter(is_active=True, show_on_home=True).first(),
            'posts': Post.objects.published()[:3],
        })
        return context


class AboutView(SEOMixin, TemplateView):
    """О нас: история, миссия, инфраструктура, юрточный городок, галерея."""

    template_name = 'pages/about.html'
    meta_title = _('О нас — Baytur Resort & Spa')
    meta_description = _('История, инфраструктура и территория курорта Baytur Resort & Spa на Иссык-Куле.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'sections': AboutSection.objects.filter(is_active=True),
            'advantages': Advantage.objects.filter(is_active=True),
            'albums': GalleryAlbum.objects.filter(is_active=True)[:6],
        })
        return context
