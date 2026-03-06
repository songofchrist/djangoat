from django.contrib import admin

from djangoat.admin import CacheFragAdmin
from djangoat.models import CacheFrag



admin.site.register(CacheFrag, CacheFragAdmin)
