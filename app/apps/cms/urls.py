from django.urls import path

from apps.cms.views import StaticPageView

app_name = 'cms'

urlpatterns = [
    path('page/<slug:slug>/', StaticPageView.as_view(), name='page'),
]
