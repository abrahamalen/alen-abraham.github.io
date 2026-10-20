"""Build alenabraham.me: content/**/*.md + site/templates -> public/.

Replaces Hugo + PaperMod. URLs, feeds and markup follow what Hugo produced so the
look and every published URL stay the same (see site/urls.txt and check_urls.py).
"""

import hashlib
import html
import json
import math
import os
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from itertools import groupby
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markupsafe import Markup

import diagrams

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
    "extended/diagram.css",
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
    return d if d.tzinfo else d.replace(tzinfo=UTC)


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
    # Inlined diagrams carry their own <title> and <style>; neither is prose.
    content_html = re.sub(r"<svg\b.*?</svg>", " ", ANCHOR_RE.sub("", content_html), flags=re.S)
    text = re.sub(r"<[^>]+>", " ", content_html)
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

MERMAID_SC = re.compile(r"\{\{<\s*mermaid\s*>\}\}(.*?)\{\{<\s*/mermaid\s*>\}\}", re.S)


class Shortcodes:
    """Hugo shortcodes used in my content: figure, mermaid, lastmod; plus diagram."""

    def __init__(self):
        self.blocks: list[str] = []

    def _hold(self, rendered: str) -> str:
        # Placeholders keep raw HTML (and Mermaid's blank lines) away from the Markdown parser.
        self.blocks.append(rendered)
        return f"\n\nSHORTCODE{len(self.blocks) - 1}END\n\n"

    def expand(self, body: str, page: dict) -> str:
        def mermaid(m):
            return self._hold(diagrams.mermaid(m.group(1), page, page.get("limits")))

        def diagram(m):
            a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            if not page.get("bundle"):
                raise SystemExit(f"{page.get('source')}: {{{{< diagram >}}}} needs a page bundle (<slug>/index.md)")
            src = a.get("src", "")
            path, url = page["bundle"] / "diagrams" / src, f"{page['url']}diagrams/{src}"
            alt, caption = a.get("alt", ""), a.get("caption", "")
            return self._hold(diagrams.diagram(path, url, alt, caption, page, page.get("limits")))

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
            # Git's last commit date, else the front-matter date; never the build time.
            when = page["lastmod"] or page["date"]
            return when.strftime("%B %-d, %Y at %-I:%M %p") if when else ""

        body = MERMAID_SC.sub(mermaid, body)
        body = re.sub(r"\{\{<\s*diagram\s+(.*?)>\}\}", diagram, body)
        body = re.sub(r"\{\{<\s*figure\s+(.*?)>\}\}", figure, body)
        return re.sub(r"\{\{<\s*lastmod\s*>\}\}", lastmod, body)

    def restore(self, out: str) -> str:
        for i, block in enumerate(self.blocks):
            out = out.replace(f"<p>SHORTCODE{i}END</p>", block).replace(f"SHORTCODE{i}END", block)
        return out


def _fence(self, tokens, idx, options, env):
    """```mermaid blocks become their committed render; other fences render as usual."""
    token = tokens[idx]
    if token.info.strip() == "mermaid":
        page = env["page"]
        return env["shortcodes"]._hold(diagrams.mermaid(token.content, page, page.get("limits")))
    return RendererHTML.fence(self, tokens, idx, options, env)


md.add_render_rule("fence", _fence)

IMG_RE = re.compile(r'<img src="([^"]+)" alt="([^"]*)"(?: title="[^"]*")? ?/?>')
RELATIVE_RE = re.compile(r'(\s(?:src|href)=")(?![a-zA-Z][\w+.-]*:|/|#|\?)([^"]+)"')


def bundle_links(out: str, page: dict, sc: "Shortcodes") -> str:
    """In a page bundle, `![alt](diagrams/x.svg)` is a diagram, and relative links resolve against the page."""

    def svg_image(m):
        src, alt = m.groups()
        if RELATIVE_RE.match(f' src="{src}"') is None or not src.lower().endswith(".svg"):
            return m.group(0)
        path = page["bundle"] / urllib.parse.unquote(src)
        return sc._hold(diagrams.diagram(path, page["url"] + src, alt, "", page, page.get("limits")))

    out = IMG_RE.sub(svg_image, out)
    # Absolute, so the links also work in feeds and on list pages.
    return RELATIVE_RE.sub(lambda m: f'{m.group(1)}{page["url"]}{m.group(2)}"', out)


def render_markdown(body: str, page: dict) -> tuple[str, list]:
    sc = Shortcodes()
    out = md.render(sc.expand(body, page), {"page": page, "shortcodes": sc})
    if page.get("bundle"):
        out = bundle_links(out, page, sc)
    headings, used = [], set()

    def heading(m):
        level, inner = int(m.group(1)), m.group(2)
        base = slug = anchorize(inner)
        n = 0
        while slug in used:  # "Foo", "Foo", "Foo 1" -> foo, foo-1, foo-1-1
            n += 1
            slug = f"{base}-{n}"
        used.add(slug)
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


def content_files(directory: Path) -> list[Path]:
    """Single-file pages (<slug>.md) and page bundles (<slug>/index.md)."""
    return sorted([*directory.glob("*.md"), *directory.glob("*/index.md")])


def slug_of(path: Path) -> str:
    return path.parent.name if path.name == "index.md" else path.stem


def load_page(path: Path, section: str, dates: dict, limits: dict | None = None) -> dict | None:
    _, fm, body = path.read_text().split("---", 2)
    meta = yaml.load(fm, Loader=_Loader) or {}
    if meta.get("draft"):
        return None
    rel = str(path.relative_to(ROOT))
    if section in ("posts", "daily") and not meta.get("date"):
        raise SystemExit(f"{rel}: entries in {section}/ need a `date:` in their front matter")
    slug = slug_of(path)
    default_url = f"/{section}/{slug}/" if section else f"/{slug}/"
    page = {
        "kind": "page",
        "source": rel,
        "section": section,
        "meta": meta,
        "title": meta.get("title", ""),
        "url": meta.get("url", default_url),
        "layout": meta.get("layout", ""),
        "date": parse_date(meta.get("date")),
        "lastmod": dates.get(rel),
        "bundle": path.parent if path.name == "index.md" else None,
        "limits": limits,
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


def is_scheduled(page: dict, now: datetime) -> bool:
    """A post or daily dated after the build is scheduled: it stays out of every output until then."""
    return page["section"] in ("posts", "daily") and page["date"] is not None and page["date"] > now


def future_wanted() -> bool:
    """`FUTURE=1 make serve` previews scheduled posts locally."""
    return os.environ.get("FUTURE", "") not in ("", "0")


def scheduled(now: datetime) -> list[tuple[datetime, str, str]]:
    """(date, path, title) of every scheduled post or daily, soonest first. Front matter only."""
    upcoming = []
    for section in ("posts", "daily"):
        for path in content_files(CONTENT / section):
            meta = yaml.load(path.read_text().split("---", 2)[1], Loader=_Loader) or {}
            page = {"section": section, "date": parse_date(meta.get("date"))}
            if not meta.get("draft") and is_scheduled(page, now):
                upcoming.append((page["date"], str(path.relative_to(ROOT)), meta.get("title", "")))
    return sorted(upcoming)


def newest_first(pages: list[dict]) -> list[dict]:
    epoch = datetime.min.replace(tzinfo=UTC)
    return sorted(pages, key=lambda p: p["date"] or epoch, reverse=True)


def home_feed(pages: list[dict], cfg: dict) -> list[dict]:
    """/index.xml: dated entries only (posts and dailies), not standalone pages like About or Now."""
    return [p for p in pages if p["section"] in cfg["section_titles"] and not p["meta"].get("excludeFromFeeds")]


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


BUNDLE_SKIP = {".md", ".excalidraw"}  # sources, not published


def copy_bundles(pages: list[dict], out: Path, outputs: dict) -> int:
    """Copy each bundle's files (diagrams/, images) next to its page. Returns how many."""
    n = 0
    for p in pages:
        if not p["bundle"]:
            continue
        for f in sorted(p["bundle"].rglob("*")):
            rel = f.relative_to(p["bundle"])
            if not f.is_file() or f.suffix in BUNDLE_SKIP or any(part.startswith(".") for part in rel.parts):
                continue
            url = p["url"] + rel.as_posix()
            if url in outputs or (url.endswith("/index.html") and url[: -len("index.html")] in outputs):
                raise SystemExit(f"{url} is produced twice: by {p['source']} and by its bundle file {rel}")
            dest = out / url.lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            n += 1
    return n


def mermaid_blocks(body: str) -> list[str]:
    """Every Mermaid source in a page: {{< mermaid >}} shortcodes and ```mermaid fences."""
    blocks = [m.group(1) for m in MERMAID_SC.finditer(body)]
    tokens = md.parse(MERMAID_SC.sub("", body))
    return blocks + [t.content for t in tokens if t.type == "fence" and t.info.strip() == "mermaid"]


def render_all_mermaid(
    mmdc: Path = SITE_DIR / "node_modules/.bin/mmdc", config: Path = SITE_DIR / "mermaid.json"
) -> None:
    """`make diagrams`: render missing Mermaid blocks into their bundles, and drop renders nothing uses."""
    made, pruned = [], []
    bundles: dict[Path, set[str]] = {}
    for section in ("posts", "daily", ""):
        files = content_files(CONTENT / section) if section else sorted(CONTENT.glob("*.md"))
        for path in files:
            blocks = mermaid_blocks(path.read_text().split("---", 2)[2])
            bundle = path.parent if path.name == "index.md" else None
            if blocks and bundle is None:
                raise SystemExit(f"{path.relative_to(ROOT)}: Mermaid diagrams need a page bundle: "
                                 f"move it to {path.with_suffix('').relative_to(ROOT)}/index.md")
            if bundle is not None:
                bundles[bundle] = {diagrams.mermaid_key(b) for b in blocks}
                for b in blocks:
                    made += diagrams.render_mermaid(b, bundle, mmdc, config)
    for bundle, keep in bundles.items():
        pruned += diagrams.prune_mermaid(bundle, keep)
    for f in made:
        print(f"rendered {f.relative_to(ROOT)}")
    for f in pruned:
        print(f"removed  {f.relative_to(ROOT)}")
    print(f"mermaid: {len(made)} rendered, {len(pruned)} removed")


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
    future: bool | None = None,
) -> None:
    cfg = yaml.safe_load(config.read_text())
    now = datetime.now(UTC)
    future = future_wanted() if future is None else future
    dates = git_dates()
    eyrie = read_eyrie_lock(eyrie_lock)
    # Fetch before rendering so a bad pin fails fast, and so a later network error can't leave half a site.
    eyrie_tarball = fetch_eyrie(eyrie, cache) if eyrie else None

    pages = []
    for section in ("posts", "daily"):
        pages += [load_page(p, section, dates, cfg.get("diagrams")) for p in content_files(CONTENT / section)]
    pages += [load_page(p, "", dates, cfg.get("diagrams")) for p in sorted(CONTENT.glob("*.md"))]
    # The coming-soon page (and its icons in static/eyrie/) only exist when the artifact is off.
    pages = newest_first([p for p in pages if p and not (eyrie and p["meta"].get("eyrie_fallback"))])
    if future:
        print(f"FUTURE=1: including {sum(is_scheduled(p, now) for p in pages)} scheduled page(s)")
    else:
        pages = [p for p in pages if not is_scheduled(p, now)]

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
    env.globals.update(site=cfg, now=now, year=now.year, abs=lambda u: cfg["base_url"] + u)
    env.filters["date"] = lambda d, fmt="%B %-d, %Y": d.strftime(fmt) if d else ""
    env.filters["rfc822"] = lambda d: d.strftime("%a, %d %b %Y %H:%M:%S %z") if d else ""
    env.filters["iso"] = lambda d: d.isoformat() if d else ""
    # Cover captions are Markdown in front matter (PaperMod ran them through markdownify).
    env.filters["markdown_inline"] = lambda s: Markup(md.renderInline(str(s))) if s else ""

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
    sources: dict[str, str] = {}
    sitemap: list[tuple[str, datetime | None]] = []

    def put(url: str, body: str, source: str) -> None:
        # A second output at the same URL would silently overwrite the first:
        # tags "ui ux" and "ui-ux", or a page whose `url:` is a section's.
        if url in outputs:
            raise SystemExit(f"{url} is produced twice: by {sources[url]} and by {source}")
        outputs[url], sources[url] = body, source

    def emit(url: str, template: str, source: str, in_sitemap: bool = True, lastmod=None, **ctx) -> None:
        put(url, env.get_template(template).render(**ctx), source)
        if in_sitemap:
            sitemap.append((url, lastmod))

    def latest(ps):
        return max((p["lastmod"] or p["date"] for p in ps if p["lastmod"] or p["date"]), default=None)

    def feed(url: str, title: str, items: list[dict], source: str) -> None:
        put(url + "index.xml", env.get_template("rss.xml").render(feed={"url": url, "title": title, "items": items}),
            f"the feed of {source}")

    def paged_alias(url: str, source: str) -> None:
        # Hugo publishes /<list>/page/1/ as a redirect to the list itself; keep it.
        put(url + "page/1/", env.get_template("alias.html").render(target=cfg["base_url"] + url),
            f"the page/1/ alias of {source}")

    # Home
    emit("/", "home.html", "the home page", lastmod=latest(main_pages), page={"kind": "home", "url": "/"},
         posts=main_pages)
    feed("/", "", home_feed(pages, cfg), "the home page")
    paged_alias("/", "the home page")

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
        emit(p["url"], template, p["source"], lastmod=p["lastmod"] or p["date"], **ctx)

    # Sections
    for section, title in cfg["section_titles"].items():
        url = f"/{section}/"
        sp = {"kind": "section", "url": url, "title": title}
        src = f"section {section!r}"
        emit(url, "list.html", src, lastmod=latest(sections[section]), page=sp, entries=sections[section])
        feed(url, title, sections[section], src)
        paged_alias(url, src)

    # Taxonomies and terms
    for tax, title in cfg["taxonomies"].items():
        url = f"/{tax}/"
        terms = sorted(taxonomies[tax].items())
        term_list = [{"name": t, "url": f"{url}{urlize(t)}/", "count": len(ps)} for t, ps in terms]
        tp = {"kind": "taxonomy", "url": url, "title": title}
        all_tax_pages = [p for _, ps in terms for p in ps]
        # An empty taxonomy keeps its URL (Hugo published it) but says so, and stays out of the sitemap.
        emit(url, "terms.html", f"taxonomy {tax!r}", in_sitemap=bool(terms), lastmod=latest(all_tax_pages),
             page=tp, terms=term_list)
        term_items = []
        for t, ps in terms:
            turl = f"{url}{urlize(t)}/"
            ps = newest_first(ps)
            term_page = {"kind": "term", "url": turl, "title": term_title(t)}
            src = f"{tax} term {t!r}"
            emit(turl, "list.html", src, lastmod=latest(ps), page=term_page, entries=ps)
            feed(turl, term_title(t), ps, src)
            paged_alias(turl, src)
            term_items.append({"title": term_title(t), "url": turl, "date": ps[0]["date"], "description": ""})
        feed(url, title, sorted(term_items, key=lambda i: i["date"], reverse=True), f"taxonomy {tax!r}")

    if any(p["layout"] == "archives" for p in pages):
        put("/index.json", search_index(pages, cfg), "the search index")

    if eyrie:
        sitemap.append(("/eyrie/", None))
    page_404 = {"kind": "404", "url": "/404.html", "title": "404 Page not found"}
    emit("/404.html", "404.html", "the 404 page", in_sitemap=False, page=page_404, posts=main_pages[:5])
    put("/sitemap.xml", env.get_template("sitemap.xml").render(urls=sitemap), "the sitemap")
    put("/robots.txt", env.get_template("robots.txt").render() + "\n", "robots.txt")

    for url, body in outputs.items():
        dest = out / url.lstrip("/")
        if url.endswith("/"):
            dest = dest / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body)
    copied = copy_bundles(pages, out, outputs)
    print(f"built {len(outputs)} files ({len(pages)} pages, {copied} bundle files) -> {out}/")
    if eyrie_tarball:
        n = unpack_eyrie(eyrie_tarball, out)
        print(f"eyrie landing {eyrie['version']}: {n} files -> {out}/eyrie/")


if __name__ == "__main__":
    if sys.argv[1:] == ["--diagrams"]:
        render_all_mermaid()
    elif sys.argv[1:2] == ["--new-diagram"] and len(sys.argv) == 4:
        svg = diagrams.scaffold(CONTENT / "posts" / sys.argv[2], sys.argv[3])
        print(f"created {svg.relative_to(ROOT)}\n\nPrompt for Claude:\n{diagrams.PROMPT}")
    elif sys.argv[1:] == ["--scheduled"]:
        for when, path, title in scheduled(datetime.now(UTC)):
            print(f"{when.isoformat()}  {path}  {title}")
    else:
        build()
