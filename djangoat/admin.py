from django.contrib import admin
from django.core.cache import cache




def clear_cache_frags(modeladmin, request, queryset):
    for cf in queryset:
        cache.delete(cf.key)  # clear cache contents, so it can repopulate on next access
clear_cache_frags.short_description = 'Clear selected fragments'



class CacheFragAdmin(admin.ModelAdmin):
    actions = clear_cache_frags,
    list_display = 'name', 'site_id', 'user', 'tokens'
    list_filter = 'name', 'site_id'
    search_fields = 'user__email', 'user__first_name', 'user__last_name', 'tokens'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
