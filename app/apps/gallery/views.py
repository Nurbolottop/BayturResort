from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from apps.base.seo import SEOMixin
from apps.gallery.models import GalleryAlbum, Video, VirtualTour


class GalleryView(SEOMixin, TemplateView):
    """Фото, видео и 3D-тур (п. 4 и 12 ТЗ)."""

    template_name = 'pages/gallery/index.html'
    meta_title = _('Галерея и 3D-тур — Baytur Resort & Spa')
    meta_description = _('Фотографии, видео и виртуальный 3D-тур по территории курорта '
                         'Baytur Resort & Spa на Иссык-Куле.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'albums': GalleryAlbum.objects.filter(is_active=True).prefetch_related('images'),
            'videos': Video.objects.filter(is_active=True),
            'tours': VirtualTour.objects.filter(is_active=True),
        })
        return context


class GalleryAlbumView(SEOMixin, DetailView):
    model = GalleryAlbum
    template_name = 'pages/gallery/album.html'
    context_object_name = 'album'

    def get_queryset(self):
        return GalleryAlbum.objects.filter(is_active=True).prefetch_related('images')
