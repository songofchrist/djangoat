from django.utils import timezone




DATA = {
    'now': lambda: timezone.now()
}

DJANGOAT_PAGER = {
    'items_per_page': 20,
    'next_text': 'Next »',
    'param': 'page',
    'plus_or_minus': 3,
    'prev_text': '« Prev',
}

DJANGOAT_THUMB_GET_URL = None

DJANGOAT_THUMB_TYPE_HTML = {
    # 'pdf': '<i class="pdf-icon"></i>'
}

DJANGOAT_THUMB_TYPE_URLS = {  # static paths (without STATIC_URL) keyed to the lowercase file extension
    'DEFAULT': 'djangoat/img/default.jpg',
    'MISSING': 'djangoat/img/missing.jpg',
    'pdf': 'djangoat/img/pdf.jpg',
}
