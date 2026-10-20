"""Commenting out a line in site/site.yaml must remove that piece from every page."""

import contextlib
import hashlib
import io
import re
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402

CONFIG = (SITE_DIR / "site.yaml").read_text()
LANDING = "<!doctype html><title>Eyrie landing</title>"


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
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def build_with(self, config_text: str, lock_text: str | None = None) -> dict[str, str]:
        """Build into a temp dir. No lock (the default) means the /eyrie/ artifact step is off."""
        cfg = self.tmp / "site.yaml"
        cfg.write_text(config_text)
        lock = None
        if lock_text is not None:
            lock = self.tmp / "eyrie.lock"
            lock.write_text(lock_text)
        out = self.tmp / "public"
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(config=cfg, out=out, eyrie_lock=lock, cache=self.tmp / "cache")
        return {str(p.relative_to(out)): p.read_text() for p in out.rglob("*.html")}

    def cached_landing(self, version: str = "9.9.9") -> str:
        """Put a fake landing tarball in the build cache, so no network is needed. Returns its sha256."""
        src = self.tmp / "landing"
        (src / "assets").mkdir(parents=True)
        (src / "index.html").write_text(LANDING)
        (src / "assets" / "app.js").write_text("")
        tarball = self.tmp / "cache" / "eyrie" / f"eyrie-landing-{version}.tar.gz"
        tarball.parent.mkdir(parents=True)
        with tarfile.open(tarball, "w:gz") as tar:
            for f in ("index.html", "assets/app.js"):
                tar.add(src / f, arcname=f)
        return hashlib.sha256(tarball.read_bytes()).hexdigest()

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


    def test_eyrie_lock_serves_the_landing_page(self):
        sha = self.cached_landing()
        pages = self.build_with(CONFIG, f"version: 9.9.9\nsha256: {sha}\n")
        self.assertEqual(pages["eyrie/index.html"], LANDING)
        self.assertTrue((self.tmp / "public" / "eyrie" / "assets" / "app.js").is_file())
        self.assertFalse((self.tmp / "public" / "eyrie" / "site.webmanifest").exists())  # fallback icons stay out

    def test_commented_out_eyrie_lock_falls_back_to_coming_soon(self):
        sha = self.cached_landing()
        pages = self.build_with(CONFIG, f"# version: 9.9.9\nsha256: {sha}\n")
        self.assertIn("Coming soon", pages["eyrie/index.html"])

    def test_eyrie_hash_mismatch_fails_the_build(self):
        self.cached_landing()
        # The cached file doesn't match, so the build re-downloads; stub that with a bad body.
        with mock.patch.object(build.urllib.request, "urlopen", return_value=io.BytesIO(b"not it")):
            with self.assertRaisesRegex(SystemExit, "does not match"):
                self.build_with(CONFIG, f"version: 9.9.9\nsha256: {'0' * 64}\n")

    def test_site_pages_under_eyrie_fail_the_build(self):
        sha = self.cached_landing()
        out = self.tmp / "public"
        (out / "eyrie").mkdir(parents=True)
        (out / "eyrie" / "index.html").write_text("rendered by the site")
        tarball = build.fetch_eyrie({"version": "9.9.9", "sha256": sha}, self.tmp / "cache")
        with self.assertRaisesRegex(SystemExit, "landing page owns"):
            build.unpack_eyrie(tarball, out)


if __name__ == "__main__":
    unittest.main()
