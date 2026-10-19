# Blog/Portfolio Website

[![Build and Publish Website](https://github.com/abrahamalen/alen-abraham.github.io/actions/workflows/gh-pages.yml/badge.svg)](https://github.com/abrahamalen/alen-abraham.github.io/actions/workflows/gh-pages.yml)

My personal site, [alenabraham.me](https://alenabraham.me). It's built by my own small Python generator in `site/`, which replaces Hugo and PaperMod. The look carries over from PaperMod (MIT); its CSS lives in `site/css/` with the license header kept.

Why I build it this way, and the plan for /eyrie: [docs/build.md](docs/build.md).

## Commands

Needs [uv](https://docs.astral.sh/uv/). Dependencies are pinned in `site/requirements.txt`.

```sh
make build   # content/ + site/templates -> public/
make serve   # build, then serve on http://localhost:1313 (PORT=xxxx to change)
make check   # build, then fail if any URL in site/urls.txt is missing
```

To force a theme while previewing, add `?theme=light` or `?theme=dark` to any URL.

## Layout

- `content/`: Markdown posts, dailies and pages (front matter unchanged from Hugo)
- `site/build.py`: the generator
- `site/site.yaml`: title, menu, socials, taxonomies
- `site/templates/`: Jinja templates for pages, RSS, sitemap and redirects
- `site/css/`: CSS sources, bundled in a fixed order into `/css/site.css`
- `site/urls.txt`: every URL the Hugo build published, checked by `make check`
- `static/`: images, favicons and `CNAME`, copied as-is
