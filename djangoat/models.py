import itertools

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models.query import QuerySet




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
            search_fields = 'user__email', 'user__first_name', 'user__last_name', 'tokens

            def has_add_permission(self, request):
                return False

            def has_change_permission(self, request, obj=None):
                return False

    On the CacheFrag list page, we will now be able to search for and filter on CacheFrag records and clear them
    individually via the cache key associated with each and which is derived from the fragment name and tokens.

    Note that we will also have the option of deleting these records, but deleting a CacheFrag will NOT affect the
    cache, and the record will simply repopulate the next time it's accessed from a template. We should only delete
    CacheFrag records that are no longer in use, so as to declutter the list.
    """
    key = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    site_id = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)  # use an int field, so as not to require the Sites framework
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    tokens = models.JSONField(null=True, blank=True)  # an array of tokens to vary on name / site / user

    def __str__(self):
        r = [self.name]
        if self.site_id:
            r.append('Site #' + str(self.site_id))
        if self.user:
            r.append('User: ' + str(self.user))
        if self.tokens:
            r.append('Tokens: ' + str(self.tokens))
        return ' | '.join(r)

    @staticmethod
    def clear(name, filters=None, sites=None):
        """
        A convenience function that clears the specified CacheFragments.

        :param name: the name of the fragment; may be a string name or list of string names
        :param filters: a dict of filters for the QuerySet returned for CacheFragments with "name"; these filters will
            apply to all returned fragments. Alternatively, if both "name" and "filters" are lists of the same length,
            each member of "filters" should be a dict that applies only to its matching member in "name", allowing us
            to combine different types of queries into a single statement. For example, you might use the following:

                clear(['detail', 'list1', 'list2], [{'extra__startswith': 123}, {}, {'extra__contains': 'media'}])

            Each name has a corresponding filter item. If the lists are not the same length, we'll throw an error.
        :param sites: a list of sites or site ids to filter on
        :return: a queryset of cleared CacheFragments or list of querysets
        """
        debug = []
        if sites:
            sites = list(sites)
            sites = {'site_id__in': sites if isinstance(sites[0], int) else [s.id for s in sites]}
        else:
            sites = {}
        if isinstance(filters, list) and isinstance(name, list):
            cfs = []
            if len(filters) != len(name):
                raise Exception('"name" and "filters" lists must have the same number of members.')
            for i, v in enumerate(name):
                debug.append({**{'name': v}, **(filters[i] or {}), **sites})
                cfss = CacheFragment.objects.filter(**debug[i])
                for cf in cfss:
                    cache.delete(str(cf.key))
                cfs.append(cfss)
        else:
            debug.append({**{('name' if isinstance(name, str) else 'name__in'): name}, **(filters or {}), **sites})
            cfs = CacheFragment.objects.filter(**debug[0])
            for cf in cfs:
                cache.delete(str(cf.key))
        if settings.DEBUG:
            print('CACHE FRAGS CLEARED KWARGS:')
            for d in debug:  # show kwargs used in each clearing
                print('  ' + str(d))
        return cfs

    def get(name):
        """
        :param name: the name of the fragment; may be a string name or list of string names
        :return: associated CacheFragment objects
        """
        return CacheFragment.objects.filter(name__in=[name] if isinstance(name, str) else name)

    @staticmethod
    def get_for_sites(name, sites, vary_on=None):
        """
        :param name: the name of the fragment; may be a string name or list of string names
        :param sites: a list of Site objects or site ids
        :param vary_on: an optional list of items on which fragments are varied
        :return: associated CacheFragment objects
        """
        return CacheFragment.get(name).filter(extra__in=CacheFragment.get_extra(sites, vary_on=vary_on))

    @staticmethod
    def get_for_sites_users(name, sites, users, vary_on=None):
        """
        :param name: the name of the fragment; may be a string name or list of string names
        :param sites: a list of Site objects or site ids
        :param users: a list of User objects or user ids
        :param vary_on: an optional list of items on which fragments are varied
        :return: associated CacheFragment objects
        """
        return CacheFragment.get(name).filter(extra__in=CacheFragment.get_extra(sites, users, vary_on))

    @staticmethod
    def get_extra(sites=None, users=None, vary_on=None):
        """
        A systematic means of getting the "extra" value for CacheFragments created via the "mycache", "mysitecache",
        and "mysiteusercache" cache tags. Note that "users" will be ignored if no "sites" argument is provided.

        :param sites: a list of Site objects or site ids
        :param users: a list of User objects or user ids
        :param vary_on: an optional list of items on which fragments are varied; this may also contain lists.
                For example, [['product', 'image'], [10, 4]] will result in the following "extra" strings:
                ['product', 10], ['image', 10], ['product', 4], ['image', 4]. Note that sites / users ids
                will automatically be added at the end of vary_on to create unique "extra" variants for each
                combination.
        :return: a list of "extra" strings for the given data
        """
        if not vary_on:
            vary_on = []
        if sites:
            vary_on += [[s.id for s in sites] if sites.__class__ == QuerySet else list(sites)]
            if users:
                vary_on += [[u.id for u in users] if users.__class__ == QuerySet else list(users)]
        for i, v in enumerate(vary_on):
            if type(v) not in (list, tuple):
                vary_on[i] = [v]  # vary_on members must be lists for the "product" method
        return ['[%s]' % str(v)[1:-1] for v in list(itertools.product(*vary_on))] if vary_on else None


