# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../'))

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
