"""Карта сайта для всех языковых версий (п. 9 ТЗ)."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import Post
from apps.cms.models import StaticPage
from apps.gallery.models import GalleryAlbum
from apps.offers.models import SpecialOffer
from apps.rooms.models import RoomCategory
from apps.services.models import ConferenceHall, Service, ServiceCategory


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'
    i18n = True

    def items(self):
        return [
            'base:home', 'base:about', 'rooms:list', 'services:list',
            'services:halls', 'offers:list', 'gallery:index',
            'blog:list', 'blog:reviews', 'contacts:index',
        ]

    def location(self, item):
        return reverse(item)


class ModelSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    i18n = True
    model = None

    def items(self):
        return self.model.objects.filter(is_active=True)

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)


class RoomSitemap(ModelSitemap):
    model = RoomCategory
    priority = 0.9


class ServiceCategorySitemap(ModelSitemap):
    model = ServiceCategory


class ServiceSitemap(ModelSitemap):
    model = Service


class HallSitemap(ModelSitemap):
    model = ConferenceHall


class OfferSitemap(ModelSitemap):
    model = SpecialOffer
    changefreq = 'daily'
    priority = 0.8


class GallerySitemap(ModelSitemap):
    model = GalleryAlbum
    priority = 0.5


class PostSitemap(ModelSitemap):
    model = Post
    priority = 0.6

    def items(self):
        return Post.objects.published()


class StaticPageSitemap(ModelSitemap):
    model = StaticPage
    priority = 0.3
    changefreq = 'monthly'


SITEMAPS = {
    'static': StaticViewSitemap,
    'rooms': RoomSitemap,
    'service_categories': ServiceCategorySitemap,
    'services': ServiceSitemap,
    'halls': HallSitemap,
    'offers': OfferSitemap,
    'gallery': GallerySitemap,
    'blog': PostSitemap,
    'pages': StaticPageSitemap,
}
