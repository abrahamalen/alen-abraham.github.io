"""Page bundles and diagrams (docs/publishing.md §1): the build's rules, and what it emits."""

import re
import sys
import unittest
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))

from test_units import TempSite, post  # noqa: E402

import diagrams  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n"
PLAIN = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>Plain</title><rect width="5" height="5"/></svg>'
)
THEMED = (
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
    '<title id="t">Themed</title><style>#a{stroke:red}</style><defs><marker id="a"/></defs>'
    '<path d="M0 0" marker-end="url(#a)" fill="var(--diagram-fg, #000)"/><use xlink:href="#a"/></svg>'
)
MERMAID = "flowchart TD\n    accTitle: Two boxes\n    A --> B\n"


def svg(body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg"><title>T</title>{body}</svg>'


class SanitizerTest(unittest.TestCase):
    def test_rejects_unsafe_svg(self):
        cases = [
            ("script", svg("<script>alert(1)</script>"), "<script> is not allowed"),
            ("foreignObject", svg("<foreignObject><div/></foreignObject>"), "<foreignObject> is not allowed"),
            ("on* attribute", svg('<rect onclick="x()"/>'), "event handler attribute onclick="),
            ("javascript: link", svg('<a href="javascript:x()"><text>x</text></a>'), "javascript: or data: URL"),
            ("data: image", svg('<image href="data:image/png;base64,AAAA"/>'), "javascript: or data: URL"),
            ("external use", svg('<use href="https://evil.example/s.svg#x"/>'), "may only reference #ids"),
            ("external image", svg('<image href="pic.png"/>'), "may only reference #ids"),
            ("style @import", svg("<style>@import url(x.css);</style>"), "<style> may only reference"),
            ("entity expansion", '<!DOCTYPE s [<!ENTITY a "aa">]><svg><title>&a;</title></svg>', "not a valid SVG"),
            ("not svg", "<html><title>x</title></html>", "root element must be <svg>"),
        ]
        for name, text, message in cases:
            with self.subTest(name), self.assertRaisesRegex(SystemExit, re.escape(message)):
                diagrams.check_svg(text, "x.svg")

    def test_title_must_be_first_and_non_empty(self):
        for text in (
            '<svg xmlns="http://www.w3.org/2000/svg"><rect/><title>Late</title></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><title> </title></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"/>',
        ):
            with self.subTest(text), self.assertRaisesRegex(SystemExit, "non-empty <title> as its first child"):
                diagrams.check_svg(text, "x.svg")

    def test_safe_svg_passes(self):
        diagrams.check_svg(THEMED, "x.svg")
        diagrams.check_svg(svg('<a href="https://alenabraham.me/"><text>ok</text></a>'), "x.svg")


class IdPrefixTest(unittest.TestCase):
    def test_ids_and_references_are_prefixed(self):
        root = diagrams.check_svg(THEMED, "x.svg")
        out = diagrams.inline_svg(THEMED, root, "flow-")
        self.assertIn('id="flow-a"', out)
        self.assertIn("#flow-a{stroke:red}", out)
        self.assertIn("url(#flow-a)", out)
        self.assertIn('xlink:href="#flow-a"', out)
        self.assertIn('<svg role="img" aria-labelledby="flow-t"', out)
        self.assertIn('<title id="flow-t">', out)
        self.assertNotIn('id="a"', out)

    def test_title_without_id_gets_one(self):
        root = diagrams.check_svg(PLAIN, "x.svg")
        out = diagrams.inline_svg(PLAIN, root, "p-")
        self.assertIn('<title id="p-title">', out)
        self.assertIn('aria-labelledby="p-title"', out)


class BundleTest(TempSite):
    def bundle(self, slug: str, body: str, files: dict[str, str | bytes] | None = None) -> Path:
        root = self.root / "content" / "posts" / slug
        (root / "diagrams").mkdir(parents=True, exist_ok=True)
        (root / "index.md").write_text(post(slug.title()).replace("Body.\n", body))
        for rel, data in (files or {}).items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data) if isinstance(data, bytes) else f.write_text(data)
        return root

    def page(self, slug: str) -> str:
        return (self.root / "public" / "posts" / slug / "index.html").read_text()

    def test_bundle_url_and_files(self):
        self.write("posts/single.md", post("Single"))
        self.bundle("flow", "See ![The flow](diagrams/x.svg) and [the PNG](diagrams/x.png).\n", {
            "diagrams/x.svg": PLAIN, "diagrams/x.png": PNG, "diagrams/x.excalidraw": "{}", "photo.jpg": b"jpg",
        })
        self.build()
        public = self.root / "public"
        for rel in ("posts/single/index.html", "posts/flow/index.html", "posts/flow/diagrams/x.svg",
                    "posts/flow/diagrams/x.png", "posts/flow/photo.jpg"):
            self.assertTrue((public / rel).is_file(), rel)
        self.assertFalse((public / "posts/flow/diagrams/x.excalidraw").exists())
        self.assertFalse((public / "posts/flow/index.md").exists())
        html = self.page("flow")
        img = '<img loading="lazy" src="/posts/flow/diagrams/x.svg" alt="The flow">'
        self.assertIn(f'<figure class="diagram">{img}', html)
        self.assertIn('href="/posts/flow/diagrams/x.png"', html)

    def test_bundle_and_single_file_at_one_url_fail(self):
        self.write("posts/dup.md", post("Dup"))
        self.bundle("dup", "Body.\n")
        with self.assertRaisesRegex(SystemExit, "/posts/dup/ is produced twice"):
            self.build()

    def test_themed_svgs_are_inlined_with_distinct_ids(self):
        body = '{{< diagram src="a.svg" alt="First" caption="One" >}}\n\n![Second](diagrams/a.svg)\n'
        self.bundle("themed", body, {"diagrams/a.svg": THEMED, "diagrams/a.png": PNG})
        self.build()
        html = self.page("themed")
        self.assertIn('id="a-a"', html)
        self.assertIn('id="a2-a"', html)
        self.assertIn("<figcaption>One</figcaption>", html)
        self.assertNotIn("<img", html.split('class="post-content"')[1].split("</article>")[0])
        # The SVG's <title> and <style> aren't prose: not in the summary.
        self.assertIn('<meta name="description" content="One">', html)

    def test_build_rules(self):
        cases = [
            ("empty alt", "![](diagrams/x.svg)\n", {"diagrams/x.svg": PLAIN, "diagrams/x.png": PNG},
             "diagram x.svg needs alt text"),
            ("shortcode without alt", '{{< diagram src="x.svg" >}}\n', {"diagrams/x.svg": PLAIN, "diagrams/x.png": PNG},
             "diagram x.svg needs alt text"),
            ("no title", "![X](diagrams/x.svg)\n", {"diagrams/x.svg": svg("").replace("<title>T</title>", ""),
                                                    "diagrams/x.png": PNG}, "non-empty <title>"),
            ("no PNG fallback", "![X](diagrams/x.svg)\n", {"diagrams/x.svg": PLAIN}, "needs a PNG fallback .*x.png"),
            ("missing file", "![X](diagrams/nope.svg)\n", {}, "nope.svg does not exist"),
            ("too big", "![X](diagrams/x.svg)\n",
             {"diagrams/x.svg": PLAIN.replace("<rect", "<!--" + "x" * 600_000 + "--><rect"), "diagrams/x.png": PNG},
             r"x.svg is \d+ KB; an <img> SVG may be at most 500 KB"),
            ("unsafe", "![X](diagrams/x.svg)\n", {"diagrams/x.svg": svg("<script/>"), "diagrams/x.png": PNG},
             "<script> is not allowed"),
        ]
        for i, (name, body, files, message) in enumerate(cases):
            with self.subTest(name):
                bundle = self.bundle(f"rule{i}", body, files)
                with self.assertRaisesRegex(SystemExit, f"content/posts/rule{i}/index.md.*{message}"):
                    self.build()
                for f in sorted(bundle.rglob("*"), reverse=True):
                    f.rmdir() if f.is_dir() else f.unlink()
                bundle.rmdir()

    def test_mermaid_needs_its_render(self):
        self.bundle("merm", f"```mermaid\n{MERMAID}```\n")
        key = diagrams.mermaid_key(MERMAID)
        with self.assertRaisesRegex(SystemExit, f"Mermaid diagram {key} .*run `make diagrams`"):
            self.build()

    def test_mermaid_needs_acc_title_and_a_bundle(self):
        self.bundle("untitled", "```mermaid\nflowchart TD\n    A --> B\n```\n")
        with self.assertRaisesRegex(SystemExit, "accTitle"):
            self.build()
        (self.root / "content/posts/untitled/index.md").unlink()
        shortcode = f"{{{{< mermaid >}}}}\n{MERMAID}{{{{< /mermaid >}}}}\n"
        shortcode = f"{{{{< mermaid >}}}}\n{MERMAID}{{{{< /mermaid >}}}}\n"
        self.write("posts/flat.md", post("Flat").replace("Body.\n", shortcode))
        with self.assertRaisesRegex(SystemExit, "content/posts/flat.md: Mermaid diagrams need a page bundle"):
            self.build()

    def test_mermaid_render_is_a_light_dark_pair(self):
        key = diagrams.mermaid_key(MERMAID)
        rendered = svg("").replace("<title>T</title>", "<title>Two boxes</title>")
        files = {f"diagrams/_mermaid/{key}.{t}.{ext}": rendered if ext == "svg" else PNG
                 for t in ("light", "dark") for ext in ("svg", "png")}
        # The shortcode and a fence with the same source share one render.
        self.bundle("pair", f"```mermaid\n{MERMAID}```\n\n{{{{< mermaid >}}}}\n{MERMAID}{{{{< /mermaid >}}}}\n", files)
        self.build()
        html = self.page("pair")
        src = f"/posts/pair/diagrams/_mermaid/{key}"
        for theme in ("light", "dark"):
            img = f'<img class="diagram-{theme}" loading="lazy" src="{src}.{theme}.svg" alt="Two boxes">'
            self.assertEqual(html.count(img), 2, theme)
        self.assertNotIn("mermaid.min.js", html)
        self.assertTrue((self.root / f"public{src}.dark.png").is_file())


if __name__ == "__main__":
    unittest.main()
