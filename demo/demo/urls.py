from django.contrib import admin
from django.urls import include, path

from djangoat import THUMB
from djangoat.models import CacheFrag

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
]



CacheFrag.populate_cache_frags()

def test(field_file, key):
    print(field_file)
    print(type(field_file))
    print(dir(field_file))
    return 'blah'

THUMB.update({
    'get_thumb_url': test
})
