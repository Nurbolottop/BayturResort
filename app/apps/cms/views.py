from django.views.generic import DetailView

from apps.base.seo import SEOMixin
from apps.cms.models import StaticPage


class StaticPageView(SEOMixin, DetailView):
    """Политика конфиденциальности, оферта, правила проживания и прочие тексты."""

    model = StaticPage
    template_name = 'pages/static_page.html'
    context_object_name = 'page'

    def get_queryset(self):
        return StaticPage.objects.filter(is_active=True)
