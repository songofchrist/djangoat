from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver



CACHE_FRAG_KEYS = {}  # store cache keys by CacheFrag (FRAG_NAME, ARGS_STRING, USER_ID, SITE_ID) tuples




# QUERYSETS
class CacheFragQuerySet(models.QuerySet):
    def clear(self):
        """Clears associated content from the cache.

        For example, to clear all CacheFrags associated with a given user, we might use the following.

        ..  code-block:: python

            CacheFrag.object.filter(user_id=12345).clear()

        :return: the queryset
        """
        self.update(date_set=None)
        for cf in self.all():
            cache.delete(cf.key)
        return self




# MODELS
class CacheFrag(models.Model):
    """Provides a means of associating cached content with the key under which it is stored in the cache, so that
    it can be cleared through the admin. A prebuilt admin is available at ``djangoat.admin.CacheFragAdmin``.
    """
    key = models.CharField(max_length=100, primary_key=True)  # the key returned by Django's "make_template_fragment_key"
    name = models.CharField(max_length=100, db_index=True)
    args = models.CharField(max_length=500, null=True, blank=True)  # a list of args, converted to strings and joined together by "|"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    site_id = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)  # use an int field, so as not to require the Sites framework
    date_set = models.DateTimeField(null=True, blank=True)  # when this fragment was last set (clearing nullifies it)
    duration = models.CharField(max_length=100, null=True, blank=True)  # either numeric seconds until expiration or a date string (i.e. '1d3h')

    objects = CacheFragQuerySet.as_manager()

    class Meta:
        ordering = 'name',
        verbose_name = 'Cache Fragment'

    def __str__(self):
        return self.name

    @classmethod
    def populate_key_dict(cls):
        """
        Populates the CACHE_FRAG_KEYS dict based on existing CacheFrag records. We'll use this to determine if a
        CacheFrag already exists for a particular name / args / user / site combination, saving us a trip to the
        database.
        """
        cfs = cls.objects.all()
        if getattr(settings, 'SITE_ID', None):  # no reason to import frags for other sites
            cfs = cfs.filter(Q(site_id=None) | Q(site_id=settings.SITE_ID))
        for cf in cfs:
            CACHE_FRAG_KEYS[(cf.name, cf.args, cf.user_id, cf.site_id)] = (cf.key, cf.duration)



# SIGNALS
@receiver(post_delete, sender=CacheFrag)
def cache_frag_post_delete(sender, instance, using, origin, **kwargs):
    try:  # record was deleted; remove associated CACHE_FRAG_KEYS to reflect its deletion
        del CACHE_FRAG_KEYS[(instance.name, instance.args, instance.user_id, instance.site_id)]
    except KeyError:
        pass
