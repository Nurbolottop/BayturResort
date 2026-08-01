from django.urls import path

from apps.offers.views import OfferDetailView, OfferListView

app_name = 'offers'

urlpatterns = [
    path('', OfferListView.as_view(), name='list'),
    path('<slug:slug>/', OfferDetailView.as_view(), name='detail'),
]
