from django.utils import timezone




DJANGOAT_DATA = {
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

DJANGOAT_TIMES = {
    **{'1y': 365 * 24 * 60 * 60},  # one year
    **{str(t) + 'd': t * 60 * 60 * 24 for t in range(1, 365)},  # e.g. TIMES["5d"] = 5 days
    **{str(t) + 'h': t * 60 * 60 for t in range(1, 24)},  # e.g. TIMES["5h"] = 5 hours
    **{str(t) + 'm': t * 60 for t in range(1, 60)},  # e.g. TIMES["5m"] = 5 minutes
}
