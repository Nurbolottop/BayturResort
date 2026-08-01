from django.urls import path

from apps.gallery.views import GalleryAlbumView, GalleryView

app_name = 'gallery'

urlpatterns = [
    path('', GalleryView.as_view(), name='index'),
    path('<slug:slug>/', GalleryAlbumView.as_view(), name='album'),
]
