from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

from djangoat.models import CacheFrag



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# Execute once on server start after apps have loaded
CacheFrag.populate_cache_frags()
