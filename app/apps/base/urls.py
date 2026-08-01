from django.urls import path

from apps.base.views import AboutView, HomeView

app_name = 'base'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
]
