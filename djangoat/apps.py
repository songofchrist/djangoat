from django.apps import AppConfig
from django.conf import settings



class DjangoatConfig(AppConfig):
    name = 'djangoat'

    def ready(self):
        dgs = getattr(settings, 'DJANGOAT_SETTINGS', None)
        if dgs:  # process Djangoat settings
            pass
        # TODO specify a DJANGOAT_SETTINGS constant in settings with the path to this file
        # TODO create a djangoat settings file that corresonds to this path
        # TODO import this file here and make adjustments to functionality based on what's recorded there
