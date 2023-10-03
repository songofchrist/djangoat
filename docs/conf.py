# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import django

from django.conf import settings

sys.path.insert(0, os.path.abspath('../'))

# Configure Django
settings.configure(
    SECRET_KEY='docs',
    INSTALLED_APPS=[
        'django.contrib.sessions',
        'djangoat',
    ],
)
django.setup()

# Project information
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = 'Djangoat'
copyright = '2023, Bryant Glisson'
author = 'Bryant Glisson'
release = '0.0.1'

# General configuration
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
extensions = ['sphinx.ext.autodoc']
templates_path = ['_templates']


# Options for HTML output
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Global settings
rst_epilog = """
.. _cachefrag: models.html#djangoat.models.CacheFrag
.. _cachefrag tag: templatetags.html#djangoat.templatetags.djangoat.cachefrag
.. _data tag: templatetags.html#djangoat.templatetags.djangoat.data
.. _dataf filter: templatetags.html#djangoat.templatetags.djangoat.dataf
.. _get_csv_content: utils.html#djangoat.utils.get_csv_content
.. _get_csv_rows_from_queryset: utils.html#djangoat.utils.get_csv_rows_from_queryset
.. _jsonfield: https://docs.djangoproject.com/en/dev/topics/db/queries/#querying-jsonfield
.. _requests api: https://github.com/psf/requests/blob/main/src/requests/api.py
.. _thumb_url tag: templatetags.html#djangoat.templatetags.djangoat.thumb_url
"""