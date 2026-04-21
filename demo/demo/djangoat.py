import mimetypes

from django.conf import settings
from django.db.models.fields.files import ImageFieldFile



THUMB = {
    'type_html': {
        'default': '<i class="bi bi-file-earmark"></i>',
        'application/pdf': '<i class="bi bi-filetype-pdf"></i>',
    },
    'type_urls': {
        'default': settings.STATIC_URL + 'file.jpg',
        'application/pdf': settings.STATIC_URL + 'pdf.jpg',
    },
}


# FUNCTIONS
def get_thumb_html(field_file, key):
    if isinstance(field_file, ImageFieldFile):
        return f'<img src="{field_file.url}">'  # in a real application, we would use "key" here to retrieve thumbnail html
    return THUMB['type_html'].get(mimetypes.guess_type(field_file.path)[0], None) or THUMB['type_html']['default']


def get_thumb_url(field_file, key):
    if isinstance(field_file, ImageFieldFile):
        return field_file.url  # in a real application, we would use "key" here to retrieve a thumbnail url
    return THUMB['type_urls'].get(mimetypes.guess_type(field_file.path)[0], None) or THUMB['type_urls']['default']
