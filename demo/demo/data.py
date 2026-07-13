from djangoat import DATA

from ..app.models import Company, Post




DATA.update({
    'companies': lambda: Company.objects.all(),
    'posts': lambda: Post.objects.all(),
})