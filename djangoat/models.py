import itertools

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import models
from django.db.models.query import QuerySet




# MODELS
class CacheFragment(models.Model):
    """
    TODO revise and modify to meet new requirements

    CacheFragments are a means of associating template fragments with their cache key, so that they can be targeted
    and cleared via the admin. To do this, set up an admin such as the following:

        def clear_cache_fragments(modeladmin, request, queryset):
            for cf in queryset:
                cache.delete(cf.key)  # clear cache contents, so it can repopulate
        clear_cache_fragments.short_description = 'Clear selected fragments'

        @admin.register(CacheFragment)
        class CacheFragmentAdmin(MyAdmin):  # FYI, this will appear under the MY app
            actions = clear_cache_fragments,
            list_display = 'name', 'extra', 'user', 'site'
            list_filter = 'name', 'site'
            search_fields = 'extra', 'user__email', 'user__first_name', 'user__last_name'

            def has_add_permission(self, request):
                return False

            def has_change_permission(self, request, obj=None):
                return False

    Deleting CacheFragments from the admin will NOT affect the cache, but will simply delete the record that
    associates the fragment with its key. The record will repopulate the next time it is encountered in a
    template. So you should only delete a record if it is no longer used in templates.
    """
    key = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    extra = models.CharField(max_length=200, null=True, db_index=True)
    site = models.ForeignKey(Site, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)

    def __str__(self):
        return self.name + '|' + (self.extra or '')

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


