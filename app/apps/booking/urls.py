from django.urls import path

from apps.booking.request_views import BookingRequestView
from apps.booking.views import (
    BookingCheckoutView,
    BookingDetailView,
    BookingSearchView,
    PaymentFailureView,
    PaymentResultView,
    PaymentSuccessView,
    availability_api,
)

app_name = 'booking'

urlpatterns = [
    path('', BookingSearchView.as_view(), name='search'),
    path('api/availability/', availability_api, name='availability_api'),
    path('request/', BookingRequestView.as_view(), name='request'),
    path('checkout/<slug:slug>/', BookingCheckoutView.as_view(), name='checkout'),
    path('payment/result/', PaymentResultView.as_view(), name='payment_result'),
    path('<str:number>/', BookingDetailView.as_view(), name='detail'),
    path('<str:number>/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('<str:number>/failure/', PaymentFailureView.as_view(), name='payment_failure'),
]
