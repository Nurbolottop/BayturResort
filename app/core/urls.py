"""
Маршруты сайта Baytur Resort & Spa.

Языковые версии подключены через i18n_patterns: русская — без префикса
(resort.baytur.kg/), английская и кыргызская — с префиксом (/en/, /ky/).
Так у каждой версии свой корректный URL, как требует п. 5.4 и 9 ТЗ.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.base.sitemaps import SITEMAPS

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('i18n/', include('django.conf.urls.i18n')),

    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='seo/robots.txt', content_type='text/plain')),

    # Бронирование — без языкового префикса: сюда же приходит колбэк FreedomPay,
    # который дергает сервер, а не браузер гостя.
    path('booking/', include('apps.booking.urls')),
]

urlpatterns += i18n_patterns(
    path('', include('apps.base.urls')),
    path('rooms/', include('apps.rooms.urls')),
    path('offers/', include('apps.offers.urls')),
    path('gallery/', include('apps.gallery.urls')),
    path('', include('apps.services.urls')),
    path('', include('apps.blog.urls')),
    path('', include('apps.contacts.urls')),
    path('', include('apps.cms.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'apps.base.errors.page_not_found'
handler500 = 'apps.base.errors.server_error'
