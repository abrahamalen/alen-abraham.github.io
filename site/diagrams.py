"""Diagrams in posts (docs/publishing.md §1): designed SVGs and Mermaid renders.

A diagram lives in its post's bundle (content/posts/<slug>/diagrams/). The build
inlines SVGs that use the --diagram-* CSS variables, emits <img> for the rest, and
shows a light/dark pair for x.light.svg + x.dark.svg (which is what Mermaid renders
are). It fails instead of warning when a diagram breaks one of the rules.
"""

import hashlib
import html
import re
import subprocess
import tempfile
from pathlib import Path

from defusedxml import ElementTree

DEFAULT_LIMITS = {"inline_svg_kb": 100, "img_svg_kb": 500, "png_kb": 400}
MERMAID_DIR = "diagrams/_mermaid"
THEMES = {"light": ("default", "white"), "dark": ("dark", "#111111")}  # mermaid theme, PNG background
ACC_TITLE = re.compile(r"^\s*accTitle\s*:\s*(.+?)\s*$", re.M)


def _local(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _fail(where: str, why: str):
    raise SystemExit(f"{where}: {why}")


def _kb(path: Path) -> float:
    return path.stat().st_size / 1024


def check_size(path: Path, limit_kb: int, where: str, what: str) -> None:
    if _kb(path) > limit_kb:
        _fail(where, f"{path.name} is {_kb(path):.0f} KB; {what} may be at most {limit_kb} KB (site.yaml `diagrams:`)")


def check_svg(text: str, where: str):
    """Parse and vet an SVG. Rejects (never strips) anything unsafe to inline; returns the root element."""
    try:
        root = ElementTree.fromstring(text)
    except Exception as e:  # defusedxml raises its own errors for entities and DTD tricks
        _fail(where, f"not a valid SVG: {e}")
    if _local(root.tag) != "svg":
        _fail(where, "the root element must be <svg>")
    first = next(iter(root), None)
    if first is None or _local(first.tag) != "title" or not (first.text or "").strip():
        _fail(where, "an SVG needs a non-empty <title> as its first child")
    for el in root.iter():
        tag = _local(el.tag)
        if tag in ("script", "foreignObject"):
            _fail(where, f"<{tag}> is not allowed in a diagram")
        if tag == "style" and re.search(r"@import|javascript:|url\(\s*['\"]?(?!#)", el.text or "", re.I):
            _fail(where, "<style> may only reference #ids (no @import or external url())")
        for name, value in el.attrib.items():
            attr, squashed = _local(name), re.sub(r"\s", "", value).lower()
            if attr.lower().startswith("on"):
                _fail(where, f"event handler attribute {attr}= on <{tag}> is not allowed")
            if "javascript:" in squashed or squashed.startswith("data:") or "url(data:" in squashed:
                _fail(where, f"{attr}= on <{tag}> has a javascript: or data: URL")
            if attr == "href" and tag in ("use", "image") and not value.startswith("#"):
                _fail(where, f"<{tag}> may only reference #ids in this SVG, not {value!r}")
    return root


def prefix_ids(text: str, root, prefix: str) -> str:
    """Prefix every id, and every reference to one, so two inlined diagrams can't clash."""
    ids = {el.get("id") for el in root.iter() if el.get("id")}
    if not ids:
        return text
    alt = "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))
    text = re.sub(rf"""(\sid=["'])({alt})(["'])""", rf"\g<1>{prefix}\2\3", text)
    text = re.sub(rf"(?<![\w&])#({alt})(?![\w-])", rf"#{prefix}\1", text)  # href="#x", url(#x), CSS #x

    def refs(m):
        return m.group(1) + " ".join(prefix + r if r in ids else r for r in m.group(2).split()) + m.group(3)

    return re.sub(r"""(\saria-(?:labelledby|describedby)=["'])([^"']*)(["'])""", refs, text)


def inline_svg(text: str, root, prefix: str) -> str:
    text = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", text).strip()
    title_id = next(iter(root)).get("id")
    text = prefix_ids(text, root, prefix)
    if title_id:
        title_id = prefix + title_id
    else:
        title_id = prefix + "title"
        text = re.sub(r"<title(?=[\s>])", f'<title id="{title_id}"', text, count=1)

    def open_tag(m):
        tag = re.sub(r"""\s(?:role|aria-labelledby)=(?:"[^"]*"|'[^']*')""", "", m.group(0))
        return tag[:4] + f' role="img" aria-labelledby="{title_id}"' + tag[4:]

    return re.sub(r"<svg\b[^>]*>", open_tag, text, count=1)


def _figure(inner: str, caption: str) -> str:
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return f'<figure class="diagram">{inner}{cap}</figure>'


def _img(url: str, alt: str, cls: str = "") -> str:
    cls = f' class="{cls}"' if cls else ""
    return f'<img{cls} loading="lazy" src="{html.escape(url)}" alt="{html.escape(alt)}">'


def _checked(svg: Path, where: str, limits: dict, limit_key: str, what: str) -> tuple[str, object]:
    if not svg.is_file():
        _fail(where, f"{svg.name} does not exist")
    text = svg.read_text()
    root = check_svg(text, f"{where} ({svg.name})")
    check_size(svg, limits[limit_key], where, what)
    png = svg.with_suffix(".png")
    if not png.is_file():
        _fail(where, f"{svg.name} needs a PNG fallback next to it ({png.name}), for other platforms")
    check_size(png, limits["png_kb"], where, "a PNG")
    return text, root


def diagram(svg: Path, url: str, alt: str, caption: str, page: dict, limits: dict | None = None) -> str:
    """HTML for one SVG diagram. `url` is where svg is served; svg may also be a x.light/x.dark pair."""
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    where = page.get("source", "?")
    alt = html.unescape(alt or "").strip()
    if not alt:
        _fail(where, f"diagram {svg.name} needs alt text")
    light, dark = svg.with_suffix(".light.svg"), svg.with_suffix(".dark.svg")
    if not svg.is_file() and light.is_file() and dark.is_file():
        for variant in (light, dark):
            _checked(variant, where, limits, "img_svg_kb", "an <img> SVG")
        base = url[: -len(".svg")]
        return _figure(_img(base + ".light.svg", alt, "diagram-light") + _img(base + ".dark.svg", alt, "diagram-dark"),
                       caption)
    if not svg.is_file():
        _fail(where, f"{svg.name} does not exist")
    inline = "var(--diagram-" in svg.read_text()
    limit_key, what = ("inline_svg_kb", "an inlined SVG") if inline else ("img_svg_kb", "an <img> SVG")
    text, root = _checked(svg, where, limits, limit_key, what)
    if not inline:
        return _figure(_img(url, alt), caption)
    used = page.setdefault("diagram_prefixes", set())
    stem = re.sub(r"[^\w-]", "-", svg.stem)
    prefix, n = f"{stem}-", 1
    while prefix in used:
        n += 1
        prefix = f"{stem}{n}-"
    used.add(prefix)
    return _figure(inline_svg(text, root, prefix), caption)


# ---------- Mermaid ----------

def mermaid_key(source: str) -> str:
    return hashlib.sha256((source.strip() + "\n").encode()).hexdigest()[:16]


def mermaid(source: str, page: dict, limits: dict | None = None) -> str:
    """The committed light/dark render of a Mermaid block. Fails if `make diagrams` hasn't made it."""
    where = page.get("source", "?")
    bundle = page.get("bundle")
    if bundle is None:
        _fail(where, "Mermaid diagrams need a page bundle: move the post to <section>/<slug>/index.md")
    title = ACC_TITLE.search(source)
    if not title:
        _fail(where, "add an `accTitle: …` line to each Mermaid diagram; it's the alt text and the SVG <title>")
    key = mermaid_key(source)
    base = bundle / MERMAID_DIR / key
    names = [f"{key}.{t}.{ext}" for t in THEMES for ext in ("svg", "png")]
    missing = [n for n in names if not (base.parent / n).is_file()]
    if missing:
        _fail(where, f"Mermaid diagram {key} ({title.group(1)!r}) has no render ({', '.join(missing)}); "
                     "run `make diagrams`")
    return diagram(base.with_suffix(".svg"), f"{page['url']}{MERMAID_DIR}/{key}.svg", title.group(1), "", page, limits)


def _fix_size(svg: Path) -> None:
    """mmdc writes width="100%"; give the SVG its real size so an <img> of it isn't stretched."""
    text = svg.read_text()
    m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', text)
    if m:
        w, h = (round(float(v)) for v in m.groups())
        text = re.sub(r'(<svg\b[^>]*?)\swidth="100%"', rf'\1 width="{w}" height="{h}"', text, count=1)
        svg.write_text(text)


def render_mermaid(source: str, bundle: Path, mmdc: Path, config: Path) -> list[Path]:
    """Render one block into bundle/diagrams/_mermaid/<key>.{light,dark}.{svg,png}. Skips files that exist."""
    key = mermaid_key(source)
    out_dir = bundle / MERMAID_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{key}.mmd"
        src.write_text(source.strip() + "\n")
        for name, (theme, png_bg) in THEMES.items():
            for ext, bg, extra in (("svg", "transparent", []), ("png", png_bg, ["-s", "2"])):
                dest = out_dir / f"{key}.{name}.{ext}"
                if dest.is_file():
                    continue
                cmd = [str(mmdc), "-q", "-i", str(src), "-o", str(dest), "-t", theme, "-b", bg, "-c", str(config)]
                cmd += extra
                subprocess.run(cmd, check=True)
                if ext == "svg":
                    _fix_size(dest)
                made.append(dest)
    return made


def prune_mermaid(bundle: Path, keep: set[str]) -> list[Path]:
    """Delete renders in bundle/diagrams/_mermaid/ that no block uses any more."""
    out_dir = bundle / MERMAID_DIR
    if not out_dir.is_dir():
        return []
    stale = [f for f in out_dir.iterdir() if f.is_file() and f.name.split(".", 1)[0] not in keep]
    for f in stale:
        f.unlink()
    if not any(out_dir.iterdir()):
        out_dir.rmdir()
    return stale


def scaffold(bundle: Path, name: str) -> Path:
    """`make diagram`: a starter SVG with the theme variables and <title> in place."""
    if not (bundle / "index.md").is_file():
        raise SystemExit(f"{bundle}/index.md not found: diagrams live in a page bundle (posts/<slug>/index.md)")
    svg = bundle / "diagrams" / f"{name}.svg"
    if svg.exists():
        raise SystemExit(f"{svg} already exists")
    svg.parent.mkdir(parents=True, exist_ok=True)
    svg.write_text(STARTER.replace("NAME", name))
    return svg


STARTER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 200" width="640" height="200">
  <title>NAME: replace with a one-line description (it's what screen readers say)</title>
  <desc>Optional: what the diagram shows, in a sentence or two.</desc>
  <rect x="1" y="1" width="638" height="198" rx="8"
        fill="var(--diagram-bg, #ffffff)" stroke="var(--diagram-line, #d0d7de)"/>
  <rect x="40" y="70" width="160" height="60" rx="6"
        fill="none" stroke="var(--diagram-accent, #0969da)" stroke-width="2"/>
  <text x="120" y="105" text-anchor="middle" font-family="sans-serif" font-size="16"
        fill="var(--diagram-fg, #1f2328)">Box</text>
  <text x="320" y="180" text-anchor="middle" font-family="sans-serif" font-size="12"
        fill="var(--diagram-muted, #59636e)">note</text>
</svg>
"""

PROMPT = """Draw this as a single standalone SVG for my blog (alenabraham.me), at most 100 KB:
- first child is a <title> describing the diagram in one line; add a <desc>
- colours only through these CSS variables, with the light fallback shown:
  var(--diagram-fg, #1f2328) text and strokes, var(--diagram-bg, #ffffff) background,
  var(--diagram-accent, #0969da) highlights, var(--diagram-muted, #59636e) secondary text,
  var(--diagram-line, #d0d7de) connectors and borders
- no <script>, <foreignObject>, on* attributes, external or data: URLs, web fonts or <image>
- a viewBox plus width/height; font-family sans-serif
Also export a PNG of the light version at 2x, named like the SVG with .png, at most 400 KB."""

