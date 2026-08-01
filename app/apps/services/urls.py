from django.urls import path

from apps.services.views import (
    ConferenceHallDetailView,
    ConferenceHallListView,
    ServiceCategoryDetailView,
    ServiceCategoryListView,
    ServiceDetailView,
)

app_name = 'services'

urlpatterns = [
    path('services/', ServiceCategoryListView.as_view(), name='list'),
    path('services/category/<slug:slug>/', ServiceCategoryDetailView.as_view(), name='category'),
    path('services/<slug:slug>/', ServiceDetailView.as_view(), name='detail'),
    path('halls/', ConferenceHallListView.as_view(), name='halls'),
    path('halls/<slug:slug>/', ConferenceHallDetailView.as_view(), name='hall_detail'),
]
