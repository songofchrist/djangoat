from django import forms

from . import widgets




class MonoTextarea(forms.Textarea):
    widget = widgets.MonoTextarea



class PrettyJSONField(forms.JSONField):
    widget = widgets.PrettyJSONTextarea
