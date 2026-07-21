from django.contrib import admin

from djangoat.admin import CacheFragAdmin
from djangoat.models import CacheFrag

from .models import Company, NewsletterSectionType, Post, Tag



@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass



@admin.register(NewsletterSectionType)
class NewsletterSectionTypeAdmin(admin.ModelAdmin):
    pass



@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass



@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass



admin.site.register(CacheFrag, CacheFragAdmin)
