from django.apps import AppConfig
from django.conf import settings
from django.db.models import Q





class DjangoatConfig(AppConfig):
    name = 'djangoat'

    def ready(self):
        # Read existing CacheFrag records into a dict, so we don't have to hit the database for existing keys
        from .models import CACHE_FRAG_KEYS, CacheFrag
        cfs = CacheFrag.objects.all()
        if getattr(settings, 'SITE_ID', None):  # no reason to import frags for other sites
            cfs = cfs.filter(Q(site_id=None) | Q(site_id=settings.SITE_ID))
        CACHE_FRAG_KEYS.update({f'{cf.name}|{cf.user_id or ""}|{cf.site_id or ""}|{cf.tokens}': cf.key for cf in cfs})
