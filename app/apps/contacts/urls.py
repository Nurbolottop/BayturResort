from django.urls import path

from apps.contacts.views import ContactsView, EventRequestView, SubscribeView

app_name = 'contacts'

urlpatterns = [
    path('contacts/', ContactsView.as_view(), name='index'),
    path('event-request/', EventRequestView.as_view(), name='event_request'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
]
