from django.apps import AppConfig





class DjangoatConfig(AppConfig):
    name = 'djangoat'

    def ready(self):
        # Read existing CacheFrag records into a dict, so we don't have to hit the database for existing keys
        from .models import CACHE_FRAG_KEYS, CacheFrag
        CACHE_FRAG_KEYS.update({f'{cf.name}|{cf.user_id or ""}|{cf.site_id or ""}|{cf.tokens}': cf.key for cf in CacheFrag.objects.all()})
