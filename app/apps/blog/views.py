from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.base.seo import SEOMixin
from apps.blog.models import Guest, Post, Review


class PostListView(SEOMixin, ListView):
    model = Post
    template_name = 'pages/blog/list.html'
    context_object_name = 'posts'
    paginate_by = 9
    meta_title = _('Новости и статьи — Baytur Resort & Spa')
    meta_description = _('Новости курорта, гид по отдыху на Иссык-Куле и полезные статьи '
                         'от Baytur Resort & Spa.')

    def get_queryset(self):
        return Post.objects.published()


class PostDetailView(SEOMixin, DetailView):
    model = Post
    template_name = 'pages/blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.published()

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        Post.objects.filter(pk=self.object.pk).update(views=F('views') + 1)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_posts'] = Post.objects.published().exclude(pk=self.object.pk)[:3]
        return context


class ReviewListView(SEOMixin, ListView):
    model = Review
    template_name = 'pages/blog/reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20
    meta_title = _('Наши гости — Baytur Resort & Spa')
    meta_description = _('Гости курорта Baytur Resort & Spa на Иссык-Куле и их отзывы.')

    def get_queryset(self):
        return Review.objects.filter(is_approved=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['guests'] = Guest.objects.filter(is_active=True)
        return context
