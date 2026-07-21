from django.forms import Textarea




class MonoTextarea(Textarea):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs['class'] = (attrs['class'] + ' ' if 'class' in attrs else '') + 'dg-mono'
        super().__init__(attrs)

    class Media:
        css = {'all': ('djangoat/widgets.css',)}



class PrettyJSONTextarea(MonoTextarea):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs['class'] = (attrs['class'] + ' ' if 'class' in attrs else '') + 'dg-json'
        super().__init__(attrs)

    class Media:
        js = 'djangoat/widgets.js',
