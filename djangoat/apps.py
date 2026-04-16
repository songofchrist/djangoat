from django.apps import AppConfig
from django.conf import settings
from django.db.models import Q
from django.db.models.fields.files import FieldFile, ImageFieldFile

from . import THUMB




class DjangoatConfig(AppConfig):
    name = 'djangoat'

    def ready(self):
        # Bind Thumbnail Methods
        FieldFile.get_thumb_html = THUMB['get_thumb_html'] or (lambda self, key: '')
        FieldFile.get_thumb_url = THUMB['get_thumb_url'] or (lambda self, key: self.url if self and isinstance(self, ImageFieldFile) else '')
