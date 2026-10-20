"""Commenting out a line in site/site.yaml must remove that piece from every page."""

import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402

CONFIG = (SITE_DIR / "site.yaml").read_text()


def comment_out(text: str, needle: str) -> str:
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if needle in line and not line.lstrip().startswith("#")]
    assert len(hits) == 1, f"expected one live line containing {needle!r}, found {len(hits)}"
    lines[hits[0]] = "# " + lines[hits[0]]
    return "\n".join(lines) + "\n"


def uncomment(text: str, needle: str) -> str:
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if needle in line and line.lstrip().startswith("# -")]
    assert len(hits) == 1, f"expected one commented line containing {needle!r}, found {len(hits)}"
    lines[hits[0]] = lines[hits[0]].replace("# ", "", 1)
    return "\n".join(lines) + "\n"


class ToggleTest(unittest.TestCase):
    def build_with(self, config_text: str) -> dict[str, str]:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        cfg = tmp / "site.yaml"
        cfg.write_text(config_text)
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(config=cfg, out=tmp / "public")
        return {str(p.relative_to(tmp / "public")): p.read_text() for p in (tmp / "public").rglob("*.html")}

    @staticmethod
    def nav(html: str) -> str:
        m = re.search(r'<ul id="menu">(.*?)</ul>', html, re.S)
        return m.group(1) if m else ""

    def test_default_nav_has_no_now_or_resume(self):
        pages = self.build_with(CONFIG)
        for name, html in pages.items():
            if "page/1/" in name:
                continue  # redirect stubs have no header
            self.assertIn('title="About"', self.nav(html), name)
            self.assertNotIn('title="Now"', self.nav(html), name)
            self.assertNotIn('title="Resume"', self.nav(html), name)

    def test_commenting_out_a_menu_entry_removes_it_everywhere(self):
        pages = self.build_with(comment_out(CONFIG, "{name: About,"))
        for name, html in pages.items():
            if "page/1/" in name:
                continue
            self.assertNotIn('title="About"', self.nav(html), name)
            self.assertIn('title="Archives"', self.nav(html), name)
        self.assertIn("about/index.html", pages)  # the page itself still builds

    def test_uncommenting_now_adds_it_everywhere(self):
        pages = self.build_with(uncomment(CONFIG, "{name: Now,"))
        self.assertTrue(all('title="Now"' in self.nav(h) for n, h in pages.items() if "page/1/" not in n))

    def test_social_icon(self):
        home = self.build_with(comment_out(CONFIG, "{name: Twitter,"))["index.html"]
        self.assertNotIn("twitter.com/op__trojan", home)
        self.assertIn("github.com/abrahamalen", home)

    def test_home_aside(self):
        home = self.build_with(comment_out(CONFIG, "aside:"))["index.html"]
        self.assertNotIn("recruiter", home)

    def test_footer_toggle_and_back_to_top(self):
        text = comment_out(comment_out(comment_out(CONFIG, "footer_copyright:"), "back_to_top:"), "theme_toggle:")
        for name, html in self.build_with(text).items():
            self.assertNotIn('<footer class="footer">', html, name)
            self.assertNotIn('id="top-link"', html, name)
            self.assertNotIn('id=theme-toggle', html, name)

    def test_analytics(self):
        pages = self.build_with(comment_out(CONFIG, "plausible_domain:"))
        self.assertFalse(any("plausible.io" in h for h in pages.values()))

    def test_archives_links_and_font_awesome(self):
        archives = self.build_with(comment_out(CONFIG, "{name: Dailies,"))["archives/index.html"]
        self.assertNotIn("archives-categories", archives)
        self.assertNotIn("font-awesome", archives)


if __name__ == "__main__":
    unittest.main()
