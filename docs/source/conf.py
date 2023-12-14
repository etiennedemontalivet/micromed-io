# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os

sys.path.insert(0, os.path.abspath("../.."))

from micromed_io import __version__


project = "Micromed IO"
copyright = "2023, Love only"
author = "Etienne de Montalivet"
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# poetry add sphinx sphinx-rtd-theme sphinx-copybutton numpydoc
extensions = [
    "sphinx.ext.autodoc",
    "sphinx_gallery.gen_gallery",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
    "numpydoc",
    "sphinx.ext.autosectionlabel",
]

sphinx_gallery_conf = {
    "examples_dirs": "../../examples",  # path to your example scripts
    "gallery_dirs": "_auto_examples",  # path to where to save gallery generated output
}

# copy code button settings
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\n"

# numpydoc_class_members_toctree = True
# numpydoc_show_class_members = True
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 10

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autosummary_imported_members = False
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]
exclude_patterns = ["_build", "_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
source_suffix = [".rst", ".md"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
