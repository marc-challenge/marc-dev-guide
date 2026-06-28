# marc-dev-guide

Source for the **MARC 2026 Developer Guide** (MetaSejong AI Robot Challenge 2026),
built with Sphinx and hosted on Read the Docs. Bilingual (English primary, Korean mirror).

## Structure

- `docs/`     — English guide (primary). `docs/conf.py` is the RTD build configuration.
- `docs_ko/`  — Korean guide.
- `requirements.txt`, `.readthedocs.yaml` — build setup (Ubuntu 22.04 / Python 3.10).

Pages: Quickstart & environment (`getting-started`), ROS 2 reference (`api-reference`),
SDK + baseline agent (`technical-guide`), submission & scoring (`submit-guide`),
troubleshooting & notices (`faq`).

## Local build

```bash
pip install -r requirements.txt
sphinx-build -b html docs    _build/en      # http://localhost -> python -m http.server -d _build/en
sphinx-build -b html docs_ko _build/ko
```

> Draft — version strings (image tags, wheel versions, dates) are provisional and under
> internal review until the release freeze.
