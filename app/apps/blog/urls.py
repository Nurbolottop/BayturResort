from django.urls import path

from apps.blog.views import PostDetailView, PostListView, ReviewListView

app_name = 'blog'

urlpatterns = [
    path('blog/', PostListView.as_view(), name='list'),
    path('blog/<slug:slug>/', PostDetailView.as_view(), name='detail'),
    path('reviews/', ReviewListView.as_view(), name='reviews'),
]
