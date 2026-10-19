"""Prototype static-site build: content/*.md -> prototype/dist/ using my own templates.

Scope (prototype): home, every post, /resume/, /now/. RSS, sitemap, search index,
taxonomy pages, dailies and redirects come in the code PR.
"""

import html
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"
CONTENT = ROOT / "content"
OUT = PROTO / "dist"

SITE = {
    "title": "Alen Abraham",
    "description": "Alen Abraham's personal website",
    "base_url": "https://alenabraham.me",
    "favicons": "/",
    "menu": [
        ("Archives", "/archives/"),
        ("Categories", "/categories/"),
        ("Now", "/now/"),
        ("Resume", "/resume/"),
        ("About", "/about/"),
    ],
    "socials": ["Github", "Twitter", "LinkedIn", "Behance", "Medium"],
}

md = (
    MarkdownIt("commonmark", {"html": True, "typographer": True, "linkify": True})
    .enable(["table", "strikethrough", "replacements", "smartquotes", "linkify"])
)


def anchorize(text: str) -> str:
    # Mirrors Hugo's default "github" anchor style so existing #fragment links keep working.
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def git_lastmod(path: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%cI", "--", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    when = datetime.fromisoformat(out) if out else datetime.now()
    return when.strftime("%B %-d, %Y at %-I:%M %p")


def shortcodes(body: str, path: Path, page: dict) -> str:
    def mermaid(m):
        page["needs_mermaid"] = True
        return f'<div class="mermaid">\n{m.group(1)}\n</div>'

    def figure(m):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        img = f'<img loading="lazy" src="{a["src"]}" alt="{a.get("alt", a.get("title", ""))}">'
        if "link" in a:
            img = f'<a href="{a["link"]}" target="{a.get("target", "_self")}">{img}</a>'
        cap = ""
        if a.get("title") or a.get("caption"):
            cap = "<figcaption>"
            cap += f"<h4>{a['title']}</h4>" if a.get("title") else ""
            cap += f"<p>{a['caption']}</p>" if a.get("caption") else ""
            cap += "</figcaption>"
        return f'<figure class="{a.get("class", "")}">{img}{cap}</figure>'

    body = re.sub(r"\{\{<\s*mermaid\s*>\}\}(.*?)\{\{<\s*/mermaid\s*>\}\}", mermaid, body, flags=re.S)
    body = re.sub(r"\{\{<\s*figure\s+(.*?)>\}\}", figure, body)
    body = re.sub(r"\{\{<\s*lastmod\s*>\}\}", lambda _: git_lastmod(path), body)
    return body


def render_markdown(body: str) -> tuple[str, list[dict]]:
    toc = []

    def heading(m):
        level, inner = int(m.group(1)), m.group(2)
        slug = anchorize(inner)
        if level in (2, 3):
            toc.append({"level": level, "id": slug, "text": inner})
        return (
            f'<h{level} id="{slug}">{inner}'
            f'<a hidden class="anchor" aria-hidden="true" href="#{slug}">#</a></h{level}>'
        )

    out = md.render(body)
    out = re.sub(r"<h([1-6])>(.*?)</h\1>", heading, out, flags=re.S)
    out = out.replace("<pre><code", '<pre tabindex="0"><code')
    out = out.replace("<img ", '<img loading="lazy" ')
    return out, toc


def load(path: Path, url: str) -> dict:
    raw = path.read_text()
    _, fm, body = raw.split("---", 2)
    meta = yaml.safe_load(fm) or {}
    page = {"meta": meta, "url": meta.get("url", url), "needs_mermaid": False}
    body = shortcodes(body, path, page)
    page["content"], page["toc"] = render_markdown(body)
    page["title"] = meta.get("title", "")
    d = meta.get("date")
    if isinstance(d, str):
        d = datetime.fromisoformat(d)
    if isinstance(d, date) and not isinstance(d, datetime):
        d = datetime(d.year, d.month, d.day)
    page["date"] = d
    page["date_str"] = d.strftime("%B %-d, %Y") if d else ""
    page["summary"] = meta.get("summary") or re.sub(r"<[^>]+>", "", page["content"])[:200]
    return page


def main() -> None:
    env = Environment(loader=FileSystemLoader(PROTO / "templates"), autoescape=select_autoescape())
    env.globals.update(site=SITE, year=datetime.now().year)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    shutil.copytree(PROTO / "static", OUT, dirs_exist_ok=True)

    posts = [
        load(p, f"/posts/{p.stem}/")
        for p in sorted((CONTENT / "posts").glob("*.md"))
    ]
    posts = [p for p in posts if not p["meta"].get("draft")]
    # Hugo's default page order: weighted pages first (by weight), then unweighted; newest first within each.
    posts.sort(key=lambda p: (p["date"] or datetime.min).timestamp(), reverse=True)
    posts.sort(key=lambda p: (not p["meta"].get("weight"), p["meta"].get("weight") or 0))

    pages = {"/": env.get_template("home.html").render(page={"title": None, "kind": "home"}, posts=posts)}
    for p in posts:
        pages[p["url"]] = env.get_template("single.html").render(page=p | {"kind": "post"})
    for name in ("resume", "now"):
        p = load(CONTENT / f"{name}.md", f"/{name}/")
        pages[p["url"]] = env.get_template("single.html").render(page=p | {"kind": "page"})

    for url, out in pages.items():
        dest = OUT / url.strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out)
    print(f"built {len(pages)} pages -> {OUT}")


if __name__ == "__main__":
    main()
