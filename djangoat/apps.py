from django.apps import AppConfig
from django.conf import settings
from django.db.models import Q
from django.db.models.fields.files import FieldFile, ImageFieldFile

from . import THUMB




class DjangoatConfig(AppConfig):
    name = 'djangoat'

    def ready(self):
        # Read existing CacheFrag records into CACHE_FRAG_KEYS, so we don't have to hit the database for existing keys
        from .models import CACHE_FRAG_KEYS, CacheFrag
        cfs = CacheFrag.objects.all()
        if getattr(settings, 'SITE_ID', None):  # no reason to import frags for other sites
            cfs = cfs.filter(Q(site_id=None) | Q(site_id=settings.SITE_ID))
        for cf in cfs:
            CACHE_FRAG_KEYS[(cf.name, cf.args, cf.user_id, cf.site_id)] = (cf.key, cf.duration)

        # Bind Thumbnail Methods
        FieldFile.get_thumb_html = THUMB['get_thumb_html'] or (lambda self, key: '')
        FieldFile.get_thumb_url = THUMB['get_thumb_url'] or (lambda self, key: self.url if self and isinstance(self, ImageFieldFile) else '')