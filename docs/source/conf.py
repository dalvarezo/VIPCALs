# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- File path setup ---------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join('..','..')))
sys.path.insert(0, os.path.abspath(os.path.join('..','..','vipcals')))
sys.path.insert(0, os.path.abspath(os.path.join('..','..','vipcals','scripts')))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'VIPCALs'
copyright = '2024, Diego Alvarez-Ortega'
author = 'Diego Alvarez-Ortega'
release = '0.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',   # Parses docstrings
              'sphinx.ext.napoleon',  # Parses Numpy docstrings
              'sphinx.ext.mathjax',   # Print mathematical expressions
              'sphinx.ext.ifconfig'   # Include content base on configuration
              ]

templates_path = ['_templates']



# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Mock some modules to avoid errors

autodoc_mock_imports = ["AIPS", "AIPSTask","Obit","OErr", "OSystem", "AIPSDir",
        "History", "Image", "UV", "InfoList", "Table", "TableList"]

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

pygments_style = "friendly" # Background coloring of the code cells

html_theme_options = {
    'collapse_navigation': False,  # keeps sidebar expanded
    'navigation_depth': 3,         # controls heading depth in sidebar
}
