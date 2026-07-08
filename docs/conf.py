# MARC 2026 Developer Guide — Sphinx configuration (English)
#
# Built by the primary RTD project via .readthedocs.yaml (sphinx.configuration: docs/conf.py).
# The Korean counterpart is docs_ko/conf.py (language='ko'), built by a separate RTD
# project linked as a Translation (see docs_ko/.readthedocs.yaml).

import os
import sys

sys.path.insert(0, os.path.abspath('.'))

project = 'MARC 2026'
copyright = '2026, IOTCOSS (IoT Convergence & Open Sharing System)'
author = 'IOTCOSS'

# Release / version (aligned with marc-sdk 2026.1.0 and image tag v2026.1.0).
release = '2026.1.0'
version = '2026.1'

# Markdown source via MyST.
source_suffix = {
    '.md': 'markdown',
}

exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
]

extensions = [
    'myst_parser',
    'sphinx_copybutton',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinxcontrib.mermaid',
]

templates_path = ['_templates']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['custom.css']  # 표 셀 줄바꿈(가로 스크롤 제거)

# Sidebar EN <-> KO toggle (see _templates/layout.html). GitHub Pages serves the
# English tree at /en/ and the Korean tree at /ko/, so the counterpart of the
# current page is one directory up and over. This English config links to Korean.
html_context = {
    'lang_switch_prefix': '../ko/',
    'lang_switch_label': '한국어',
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'torch': ('https://pytorch.org/docs/stable/', None),
    'ros2': ('https://docs.ros.org/en/humble/', None),
}

# Local offline preview (scripts/serve_preview.sh sets MARC_DOCS_OFFLINE=1) skips remote
# inventory fetches, which fail behind captive/bot-check proxies. RTD leaves the var unset
# and resolves the mappings normally.
if os.environ.get('MARC_DOCS_OFFLINE', '') == '1':
    intersphinx_mapping = {}

myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'fieldlist',
    'html_image',
    'substitution',
    'tasklist',
    'smartquotes',
    'replacements',
    'html_admonition',
]
myst_enable_checkboxes = True

# sphinx-copybutton: strip common shell prompts so copied commands are clean.
copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True

# Read the Docs output wiring.
if os.environ.get('READTHEDOCS', '') == 'True':
    html_baseurl = os.environ.get('READTHEDOCS_URL', '')
    _out = os.environ.get('READTHEDOCS_OUTPUT', '')
    if _out and not os.path.exists(_out):
        os.makedirs(_out)
