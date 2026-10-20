# Template Style Guide

How I write the templates and build code in `site/`.

## Templates (`site/templates/`, Jinja2)

- 2-space indentation.
- The environment uses `trim_blocks` and `lstrip_blocks`, so block tags (`{% if %}`, `{% for %}`) can sit on their own lines without leaving blank lines in the output.
- Comments use `{# ... #}`, and only when the *why* isn't obvious.
- Pages extend `base.html` and fill `{% block main %}`. Shared pieces live in `partials/` and are pulled in with `{% include %}`.
- Keep the class names PaperMod used (`post-entry`, `post-single`, `page-header`, …), because the CSS in `site/css/` targets them.
- Autoescaping is on. Rendered Markdown is the only thing marked `| safe`.
- Internal links are root-relative (`/posts/x/`). Absolute URLs (`abs(...)`) are only for canonical links, OpenGraph tags, feeds and the sitemap.

## CSS (`site/css/`)

- One concern per file. `CSS_BUNDLE` in `site/build.py` sets the bundle order, so add new files to that list.
- `core/license.css` keeps PaperMod's MIT notice, and it stays first in the bundle.
- Page-specific scripts (Mermaid, highlight.js, Font Awesome) are added in `partials/head.html` only for the pages that need them.

## Build code (`site/build.py`)

- Python 3.12, standard library first. Every dependency is pinned in `site/requirements.in`, then compiled into `site/requirements.txt` with `uv pip compile`.
- New behaviour must keep `make check` green. If a URL is removed on purpose, update `site/urls.txt` in the same PR and explain why.
