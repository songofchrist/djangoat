import json

from django.db import models

from djangoat.forms import fields




class MonoTextarea(models.JSONField):
    """A textarea with mono text, a black background, and white text, for use with entering html / code."""
    def formfield(self, **kwargs):
        return super().formfield(form_class=fields.MonoTextarea)



class _PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['indent'] = 2
        kwargs['sort_keys'] = True
        super().__init__(*args, **kwargs)

class PrettyJSONField(models.JSONField):
    """A JSON field that presents JSON in a more readable manner and validates JSON in real time."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, encoder=kwargs.pop('encoder', _PrettyJSONEncoder), **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(form_class=fields.PrettyJSONField)
