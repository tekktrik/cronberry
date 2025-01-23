# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration settings for sphinx."""

project = "cronberry"
copyright = "2024 Alec Delaney"
author = "Alec Delaney"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
