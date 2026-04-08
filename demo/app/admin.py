from django.contrib import admin

from djangoat.admin import CacheFragAdmin
from djangoat.models import CacheFrag

from .models import Company, Post, Tag



@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass



@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass



@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass



admin.site.register(CacheFrag, CacheFragAdmin)
