"""Build alenabraham.me: content/**/*.md + site/templates -> public/.

Replaces Hugo + PaperMod. URLs, feeds and markup follow what Hugo produced so the
look and every published URL stay the same (see site/urls.txt and check_urls.py).
"""

import hashlib
import html
import json
import math
import re
import shutil
import ssl
import subprocess
import tarfile
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt

SITE_DIR = Path(__file__).resolve().parent
ROOT = SITE_DIR.parent
CONTENT = ROOT / "content"
OUT = ROOT / "public"
EYRIE_LOCK = SITE_DIR / "eyrie.lock"
CACHE = ROOT / ".cache"
EYRIE_RELEASES = "https://github.com/abrahamalen/eyrie/releases/download"

# Order matters: it is the order PaperMod bundled these in, so the cascade is unchanged.
CSS_BUNDLE = [
    "core/license.css",
    "core/theme-vars.css",
    "core/reset.css",
    "common/404.css",
    "common/archive.css",
    "common/footer.css",
    "common/header.css",
    "common/main.css",
    "common/post-entry.css",
    "common/post-single.css",
    "common/terms.css",
    "common/hljs-an-old-hope.css",
    "common/scroll-bar.css",
    "core/zmedia.css",
    "extended/custom.css",
    "extended/eyrie.css",
    "extended/mermaid.css",
    "extended/timeline.css",
    "extended/search.css",
]

SUMMARY_WORDS = 70  # Hugo's default summaryLength
WORDS_PER_MINUTE = 213  # Hugo's ReadingTime divisor


class _Loader(yaml.SafeLoader):
    """SafeLoader that keeps timestamps as strings so UTC offsets survive parsing."""


_Loader.yaml_implicit_resolvers = {
    k: [r for r in v if r[0] != "tag:yaml.org,2002:timestamp"]
    for k, v in _Loader.yaml_implicit_resolvers.items()
}

md = MarkdownIt("commonmark", {"html": True, "typographer": True, "linkify": True}).enable(
    ["table", "strikethrough", "replacements", "smartquotes", "linkify"]
)


# ---------- helpers ----------

def parse_date(value) -> datetime | None:
    if not value:
        return None
    d = datetime.fromisoformat(str(value))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def anchorize(text: str) -> str:
    """Hugo's default ("github") heading id style, so existing #fragment links keep working."""
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def urlize(term: str) -> str:
    return term.strip().lower().replace(" ", "-")


def term_title(term: str) -> str:
    # Hugo title-cases the term at word, slash and hyphen boundaries ("ui/ux" -> "Ui/Ux", "qure.ai" -> "Qure.ai").
    return re.sub(r"(^|[\s/\-])(\w)", lambda m: m.group(1) + m.group(2).upper(), term)


ANCHOR_RE = re.compile(r'<a hidden class="anchor"[^>]*>#</a>')


def plain_text(content_html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", ANCHOR_RE.sub("", content_html))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def git_dates() -> dict[str, datetime]:
    """Last author date per content file, from one `git log` pass."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--format=@%aI", "--name-only", "--", "content"],
        capture_output=True, text=True, check=False,
    ).stdout
    dates, current = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            current = datetime.fromisoformat(line[1:])
        elif line and current and line not in dates:
            dates[line] = current
    return dates


# ---------- content ----------

class Shortcodes:
    """Hugo shortcodes used in my content: figure, mermaid, lastmod."""

    def __init__(self):
        self.blocks: list[str] = []

    def _hold(self, rendered: str) -> str:
        # Placeholders keep raw HTML (and Mermaid's blank lines) away from the Markdown parser.
        self.blocks.append(rendered)
        return f"\n\nSHORTCODE{len(self.blocks) - 1}END\n\n"

    def expand(self, body: str, page: dict) -> str:
        def mermaid(m):
            page["needs_mermaid"] = True
            return self._hold(f'<div class="mermaid">\n{m.group(1).strip()}\n</div>')

        def figure(m):
            a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            img = f'<img loading="lazy" src="{a["src"]}" alt="{a.get("alt", a.get("title", ""))}">'
            if a.get("link"):
                target = f' target="{a["target"]}"' if a.get("target") else ""
                img = f'<a href="{a["link"]}"{target}>{img}</a>'
            cap = ""
            if a.get("title") or a.get("caption"):
                cap = "<figcaption>"
                cap += f"<h4>{a['title']}</h4>" if a.get("title") else ""
                cap += f"<p>{a['caption']}</p>" if a.get("caption") else ""
                cap += "</figcaption>"
            cls = f' class="{a["class"]}"' if a.get("class") else ""
            return self._hold(f"<figure{cls}>{img}{cap}</figure>")

        def lastmod(_):
            when = page["lastmod"] or datetime.now(timezone.utc)
            return when.strftime("%B %-d, %Y at %-I:%M %p")

        body = re.sub(r"\{\{<\s*mermaid\s*>\}\}(.*?)\{\{<\s*/mermaid\s*>\}\}", mermaid, body, flags=re.S)
        body = re.sub(r"\{\{<\s*figure\s+(.*?)>\}\}", figure, body)
        return re.sub(r"\{\{<\s*lastmod\s*>\}\}", lastmod, body)

    def restore(self, out: str) -> str:
        for i, block in enumerate(self.blocks):
            out = out.replace(f"<p>SHORTCODE{i}END</p>", block).replace(f"SHORTCODE{i}END", block)
        return out


def render_markdown(body: str, page: dict) -> tuple[str, list]:
    sc = Shortcodes()
    out = md.render(sc.expand(body, page))
    headings, seen = [], defaultdict(int)

    def heading(m):
        level, inner = int(m.group(1)), m.group(2)
        slug = anchorize(inner)
        if seen[slug]:
            slug = f"{slug}-{seen[slug]}"
        seen[anchorize(inner)] += 1
        headings.append({"level": level, "id": slug, "text": inner})
        return (
            f'<h{level} id="{slug}">{inner}'
            f'<a hidden class="anchor" aria-hidden="true" href="#{slug}">#</a></h{level}>'
        )

    out = re.sub(r"<h([1-6])>(.*?)</h\1>", heading, out, flags=re.S)
    out = out.replace("<pre><code", '<pre tabindex="0"><code')
    out = out.replace("<img ", '<img loading="lazy" ')
    return sc.restore(out), build_toc(headings)


def build_toc(headings: list[dict]) -> list:
    """Nest headings under the shallowest level present, like PaperMod's ToC."""
    if not headings:
        return []
    top = min(h["level"] for h in headings)
    root: list = []
    stack = [(top - 1, root)]
    for h in headings:
        node = {**h, "children": []}
        while stack[-1][0] >= h["level"]:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((h["level"], node["children"]))
    return root


def load_page(path: Path, section: str, dates: dict) -> dict | None:
    _, fm, body = path.read_text().split("---", 2)
    meta = yaml.load(fm, Loader=_Loader) or {}
    if meta.get("draft"):
        return None
    rel = str(path.relative_to(ROOT))
    default_url = f"/{section}/{path.stem}/" if section else f"/{path.stem}/"
    page = {
        "kind": "page",
        "section": section,
        "meta": meta,
        "title": meta.get("title", ""),
        "url": meta.get("url", default_url),
        "layout": meta.get("layout", ""),
        "date": parse_date(meta.get("date")),
        "lastmod": dates.get(rel),
        "needs_mermaid": False,
    }
    page["content"], page["toc"] = render_markdown(body, page)
    words = plain_text(page["content"]).split()
    page["word_count"] = len(words)
    page["reading_time"] = max(1, math.ceil(len(words) / WORDS_PER_MINUTE))
    if meta.get("summary"):
        page["summary"], page["truncated"] = meta["summary"], False
    else:
        page["summary"], page["truncated"] = auto_summary(page["content"])
    page["description"] = meta.get("description") or page["summary"]
    page["image"] = (meta.get("cover") or {}).get("image")
    page["has_code"] = "<pre" in page["content"]
    return page


def auto_summary(content_html: str) -> tuple[str, bool]:
    """Hugo-style summary: everything up to the first </p> after SUMMARY_WORDS words."""
    for m in re.finditer(r"</p>", content_html):
        head = plain_text(content_html[: m.end()])
        if len(head.split()) >= SUMMARY_WORDS:
            return head, bool(plain_text(content_html[m.end():]))
    return plain_text(content_html), False


def newest_first(pages: list[dict]) -> list[dict]:
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(pages, key=lambda p: p["date"] or epoch, reverse=True)


def search_index(pages: list[dict], cfg: dict) -> str:
    """/index.json for the search box on /archives/: every content page, minus list pages and `searchHidden: true`."""
    skip = {"archives", "dailies", "eyrie"}
    titles = cfg["section_titles"]
    entries = [
        {
            "title": p["title"],
            "url": p["url"],
            "date": p["date"].strftime("%B %-d, %Y") if p["date"] else "",
            "section": titles.get(p["section"], ""),
            "tags": [t for tax in cfg["taxonomies"] for t in p["meta"].get(tax) or []],
            "text": plain_text(p["content"]),
        }
        for p in pages
        if p["layout"] not in skip and not p["meta"].get("searchHidden")
    ]
    return json.dumps(entries, ensure_ascii=False, separators=(",", ":"))


# ---------- /eyrie/ landing page (release artifact) ----------

def read_eyrie_lock(lock: Path | None) -> dict | None:
    """The pinned landing-page release, or None when the lock is missing or commented out."""
    if lock is None or not lock.is_file():
        return None
    # Plain `key: value` lines, not YAML: YAML would read an all-digit digest as an int.
    pin = dict(
        (k.strip(), v.strip())
        for k, _, v in (line.partition(":") for line in lock.read_text().splitlines())
        if k.strip() and not k.lstrip().startswith("#")
    )
    if not pin.get("version"):
        return None
    if not re.fullmatch(r"[0-9a-f]{64}", pin.get("sha256", "")):
        raise SystemExit(f"{lock}: `sha256:` must be the tarball's 64-char hex digest")
    return {"version": pin["version"], "sha256": pin["sha256"]}


def sha256_of(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def fetch_eyrie(pin: dict, cache: Path) -> Path:
    """Pinned tarball from the cache, downloading it on a miss. Fails on a hash mismatch."""
    name = f"eyrie-landing-{pin['version']}.tar.gz"
    tarball = cache / "eyrie" / name
    if tarball.is_file() and sha256_of(tarball) == pin["sha256"]:
        return tarball
    tarball.parent.mkdir(parents=True, exist_ok=True)
    url = f"{EYRIE_RELEASES}/v{pin['version']}/{name}"
    print(f"fetching {url}")
    partial = tarball.with_suffix(".part")
    # python.org's macOS Python ships without a CA bundle; the OS one works.
    os_bundle = Path("/etc/ssl/cert.pem")
    use_os = not ssl.get_default_verify_paths().cafile and os_bundle.is_file()
    tls = ssl.create_default_context(cafile=str(os_bundle) if use_os else None)
    with urllib.request.urlopen(url, timeout=60, context=tls) as resp, partial.open("wb") as f:
        shutil.copyfileobj(resp, f)
    got = sha256_of(partial)
    if got != pin["sha256"]:
        partial.unlink()
        raise SystemExit(f"{name}: sha256 {got} does not match site/eyrie.lock ({pin['sha256']})")
    partial.replace(tarball)
    return tarball


def unpack_eyrie(tarball: Path, out: Path) -> int:
    """Unpack the landing page into out/eyrie/. Runs after the site has rendered."""
    dest = out / "eyrie"
    if dest.exists():
        made = sorted(str(p.relative_to(out)) for p in dest.rglob("*") if p.is_file())
        raise SystemExit(f"the site rendered files under /eyrie/, which the landing page owns: {made}")
    dest.mkdir(parents=True)
    with tarfile.open(tarball) as tar:
        tar.extractall(dest, filter="data")
    if not (dest / "index.html").is_file():
        raise SystemExit(f"{tarball.name} has no index.html at its root")
    return sum(1 for p in dest.rglob("*") if p.is_file())


# ---------- site ----------

def build(
    config: Path = SITE_DIR / "site.yaml",
    out: Path = OUT,
    eyrie_lock: Path | None = EYRIE_LOCK,
    cache: Path = CACHE,
) -> None:
    cfg = yaml.safe_load(config.read_text())
    dates = git_dates()
    eyrie = read_eyrie_lock(eyrie_lock)
    # Fetch before rendering so a bad pin fails fast, and so a later network error can't leave half a site.
    eyrie_tarball = fetch_eyrie(eyrie, cache) if eyrie else None

    pages = []
    for section in ("posts", "daily"):
        pages += [load_page(p, section, dates) for p in sorted((CONTENT / section).glob("*.md"))]
    pages += [load_page(p, "", dates) for p in sorted(CONTENT.glob("*.md"))]
    # The coming-soon page (and its icons in static/eyrie/) only exist when the artifact is off.
    pages = newest_first([p for p in pages if p and not (eyrie and p["meta"].get("eyrie_fallback"))])

    sections = {s: [p for p in pages if p["section"] == s] for s in cfg["section_titles"]}
    main_pages = sections[cfg["main_section"]]

    taxonomies: dict[str, dict[str, list]] = {t: defaultdict(list) for t in cfg["taxonomies"]}
    for p in pages:
        for tax in taxonomies:
            for term in p["meta"].get(tax) or []:
                taxonomies[tax][term.strip().lower()].append(p)

    env = Environment(
        loader=FileSystemLoader(SITE_DIR / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    now = datetime.now(timezone.utc)
    env.globals.update(site=cfg, now=now, year=now.year, abs=lambda u: cfg["base_url"] + u)
    env.filters["date"] = lambda d, fmt="%B %-d, %Y": d.strftime(fmt) if d else ""
    env.filters["rfc822"] = lambda d: d.strftime("%a, %d %b %Y %H:%M:%S %z") if d else ""
    env.filters["iso"] = lambda d: d.isoformat() if d else ""

    if out.exists():
        shutil.rmtree(out)
    skip_eyrie = (lambda d, names: ["eyrie"] if Path(d) == ROOT / "static" else []) if eyrie else None
    shutil.copytree(ROOT / "static", out, ignore=skip_eyrie)
    (out / "css").mkdir(exist_ok=True)
    (out / "css" / "site.css").write_text(
        "\n".join((SITE_DIR / "css" / f).read_text() for f in CSS_BUNDLE)
    )
    (out / "js").mkdir(exist_ok=True)
    shutil.copy(SITE_DIR / "js" / "highlight.js", out / "js" / "highlight.min.js")
    shutil.copy(SITE_DIR / "js" / "search.js", out / "js" / "search.js")

    outputs: dict[str, str] = {}
    sitemap: list[tuple[str, datetime | None]] = []

    def emit(url: str, template: str, in_sitemap: bool = True, lastmod=None, **ctx) -> None:
        outputs[url] = env.get_template(template).render(**ctx)
        if in_sitemap:
            sitemap.append((url, lastmod))

    def latest(ps):
        return max((p["lastmod"] or p["date"] for p in ps if p["lastmod"] or p["date"]), default=None)

    def feed(url: str, title: str, items: list[dict]) -> None:
        outputs[url + "index.xml"] = env.get_template("rss.xml").render(
            feed={"url": url, "title": title, "items": items}
        )

    def paged_alias(url: str) -> None:
        # Hugo publishes /<list>/page/1/ as a redirect to the list itself; keep it.
        outputs[url + "page/1/"] = env.get_template("alias.html").render(target=cfg["base_url"] + url)

    # Home
    emit("/", "home.html", lastmod=latest(main_pages), page={"kind": "home", "url": "/"}, posts=main_pages)
    feed("/", "", [p for p in pages if p["layout"] != "archives" and not p["meta"].get("excludeFromFeeds")])
    paged_alias("/")

    # Regular pages
    layouts = {"about": "about.html", "dailies": "dailies.html", "archives": "archives.html", "eyrie": "eyrie.html"}
    for p in pages:
        template = layouts.get(p["layout"]) or ("daily.html" if p["section"] == "daily" else "single.html")
        ctx = {"page": p}
        if p["layout"] == "archives":
            ctx["years"] = [
                (year, [(month, list(ms)) for month, ms in groupby(list(ys), key=lambda q: q["date"].strftime("%B"))])
                for year, ys in groupby(main_pages, key=lambda q: q["date"].year)
            ]
            ctx["year_counts"] = {y: sum(len(m[1]) for m in ms) for y, ms in ctx["years"]}
        if p["layout"] == "dailies":
            daily = sections["daily"]
            numbered = [(len(daily) - 1 - i, d) for i, d in enumerate(daily)]
            ctx["years"] = [
                (year, [(month, list(ms)) for month, ms in groupby(list(ys), key=lambda q: q[1]["date"].strftime("%B"))])
                for year, ys in groupby(numbered, key=lambda q: q[1]["date"].year)
            ]
        emit(p["url"], template, lastmod=p["lastmod"] or p["date"], **ctx)

    # Sections
    for section, title in cfg["section_titles"].items():
        url = f"/{section}/"
        sp = {"kind": "section", "url": url, "title": title}
        emit(url, "list.html", lastmod=latest(sections[section]), page=sp, entries=sections[section])
        feed(url, title, sections[section])
        paged_alias(url)

    # Taxonomies and terms
    for tax, title in cfg["taxonomies"].items():
        url = f"/{tax}/"
        terms = sorted(taxonomies[tax].items())
        term_list = [{"name": t, "url": f"{url}{urlize(t)}/", "count": len(ps)} for t, ps in terms]
        tp = {"kind": "taxonomy", "url": url, "title": title}
        all_tax_pages = [p for _, ps in terms for p in ps]
        emit(url, "terms.html", lastmod=latest(all_tax_pages), page=tp, terms=term_list)
        term_items = []
        for t, ps in terms:
            turl = f"{url}{urlize(t)}/"
            ps = newest_first(ps)
            term_page = {"kind": "term", "url": turl, "title": term_title(t)}
            emit(turl, "list.html", lastmod=latest(ps), page=term_page, entries=ps)
            feed(turl, term_title(t), ps)
            paged_alias(turl)
            term_items.append({"title": term_title(t), "url": turl, "date": ps[0]["date"], "description": ""})
        feed(url, title, sorted(term_items, key=lambda i: i["date"], reverse=True))

    if any(p["layout"] == "archives" for p in pages):
        outputs["/index.json"] = search_index(pages, cfg)

    if eyrie:
        sitemap.append(("/eyrie/", None))
    emit("/404.html", "404.html", in_sitemap=False, page={"kind": "404", "url": "/404.html", "title": "404 Page not found"})
    outputs["/sitemap.xml"] = env.get_template("sitemap.xml").render(urls=sitemap)

    for url, body in outputs.items():
        dest = out / url.lstrip("/")
        if url.endswith("/"):
            dest = dest / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body)
    print(f"built {len(outputs)} files ({len(pages)} pages) -> {out}/")
    if eyrie_tarball:
        n = unpack_eyrie(eyrie_tarball, out)
        print(f"eyrie landing {eyrie['version']}: {n} files -> {out}/eyrie/")


if __name__ == "__main__":
    build()
