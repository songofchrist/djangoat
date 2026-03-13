from django.utils import timezone

from .models import CacheFrag




class Djangoat:
    def __init__(self):
        self.cache_keys_set = []  # any cache keys set during this request that need CacheFrag.date_set updated
        self.cache_refresh = False  # if set to True, refresh all cache entries encountered in the current request



class DjangoatMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        dg = request.djangoat = Djangoat()
        response = self.get_response(request)
        if dg.cache_keys_set:
            CacheFrag.objects.filter(key__in=request.djangoat.cache_keys_set).update(date_set=timezone.now())
        return response
