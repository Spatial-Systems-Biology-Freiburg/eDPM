# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.append(os.path.abspath('../../'))
print(os.getcwd())
import FisInMa


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'FisInMa'
copyright = '2022, Jonas Pleyer, Polina Gaindrik'
author = 'Jonas Pleyer, Polina Gaindrik'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
]

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = ['_build', '_templates', 'Thumbs.db', '.DS_Store']

# Do not include documentation of these imports
autodoc_mock_imports =  ["scipy", "dataclass"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']