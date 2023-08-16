from django.conf import settings
from django.core.cache import cache
from django.db import models




CACHE_FRAG_KEYS = {}  # store cache keys by CacheFrag name / site / user / token strings to save database hits for lookups




# QUERYSETS
class CacheFragQuerySet(models.QuerySet):
    def clear(self):
        """Clears associated content from the cache.

        :return: the queryset
        """
        for cf in self.all():
            cache.delete(cf.key)
        return self




# MODELS
class CacheFrag(models.Model):
    """CacheFrag records provide a means of associating cached content with the key under which it is stored in the cache.

    The primary advantage of storing cache related data in the database is that we can now distinguish different sorts
    of cached content from one another in the admin and directly target those we want to clear. For example, suppose
    we register an admin for this model as shown below:

    ..  code-block:: python

        from djangoat.models import CacheFrag
        from django.contrib import admin


        def clear_cache_frags(modeladmin, request, queryset):
            for cf in queryset:
                cache.delete(cf.key)  # clear cache contents, so it can repopulate on next access
        clear_cache_frags.short_description = 'Clear selected fragments'


        @admin.register(CacheFrag)
        class CacheFragAdmin(admin.ModelAdmin):
            actions = clear_cache_frags,
            list_display = 'name', 'site_id', 'user', 'tokens'
            list_filter = 'name', 'site_id'
            search_fields = 'user__email', 'user__first_name', 'user__last_name', 'tokens'

            def has_add_permission(self, request):
                return False

            def has_change_permission(self, request, obj=None):
                return False

    On the CacheFrag list page, we will now be able to search for and filter on CacheFrag records and clear them
    individually via the cache key associated with each.

    Note that we will also have the option of deleting these records, but deleting a CacheFrag will NOT affect the
    cache, and the record will simply repopulate the next time it's accessed from a template. We should only delete
    CacheFrag records that are no longer in use, so as to declutter the list.
    """
    key = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    site_id = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)  # use an int field, so as not to require the Sites framework
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    tokens = models.JSONField(null=True, blank=True)  # an array of tokens to vary on name / site / user

    objects = CacheFragQuerySet.as_manager()

    def __str__(self):
        r = [self.name]
        if self.site_id:
            r.append('Site #' + str(self.site_id))
        if self.user:
            r.append('User: ' + str(self.user))
        if self.tokens:
            r.append('Tokens: ' + str(self.tokens))
        return ' | '.join(r)
