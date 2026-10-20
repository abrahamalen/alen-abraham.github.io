"""Pure helpers in build.py, plus the build's refusal of content it would get wrong."""

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SITE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_DIR))

import build  # noqa: E402


def post(title: str, date: str | None = "2024-01-01", **extra: str) -> str:
    lines = [f"title: {title}"] + ([f"date: {date}"] if date else []) + [f"{k}: {v}" for k, v in extra.items()]
    return "---\n" + "\n".join(lines) + "\n---\nBody.\n"


def heading_ids(markdown: str) -> list[str]:
    _, toc = build.render_markdown(markdown, {"lastmod": None})

    def walk(nodes):
        for n in nodes:
            yield n["id"]
            yield from walk(n["children"])

    return list(walk(toc))


class AnchorizeTest(unittest.TestCase):
    def test_matches_hugo_github_style(self):
        cases = [
            ("Hello World", "hello-world"),
            ("Big O: what & why?", "big-o-what--why"),
            ("<code>make</code> targets", "make-targets"),
            ("Tom &amp; Jerry", "tom--jerry"),
            ("already-dashed_word", "already-dashed_word"),
            ("Ünïcode Wörds", "ünïcode-wörds"),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                self.assertEqual(build.anchorize(text), want)


class UrlizeTest(unittest.TestCase):
    def test_lowercases_and_dashes_spaces(self):
        cases = [("UI UX", "ui-ux"), ("  padded ", "padded"), ("ui/ux", "ui/ux"), ("qure.ai", "qure.ai")]
        for term, want in cases:
            with self.subTest(term=term):
                self.assertEqual(build.urlize(term), want)


class TermTitleTest(unittest.TestCase):
    def test_capitalises_at_word_slash_and_hyphen_boundaries(self):
        cases = [
            ("ui/ux", "Ui/Ux"),
            ("qure.ai", "Qure.ai"),
            ("site-reliability", "Site-Reliability"),
            ("big o notation", "Big O Notation"),
            ("", ""),
        ]
        for term, want in cases:
            with self.subTest(term=term):
                self.assertEqual(build.term_title(term), want)


class BuildTocTest(unittest.TestCase):
    @staticmethod
    def shape(nodes) -> list:
        return [(n["id"], BuildTocTest.shape(n["children"])) for n in nodes]

    def test_nests_under_the_shallowest_level(self):
        h = lambda level, id_: {"level": level, "id": id_, "text": id_}  # noqa: E731
        cases = [
            ([], []),
            ([h(2, "a"), h(2, "b")], [("a", []), ("b", [])]),
            ([h(2, "a"), h(3, "a1"), h(3, "a2"), h(2, "b")], [("a", [("a1", []), ("a2", [])]), ("b", [])]),
            ([h(3, "x"), h(2, "y")], [("x", []), ("y", [])]),  # a deeper first heading stays top-level
            ([h(2, "a"), h(4, "deep"), h(3, "mid")], [("a", [("deep", []), ("mid", [])])]),
        ]
        for headings, want in cases:
            with self.subTest(ids=[x["id"] for x in headings]):
                self.assertEqual(self.shape(build.build_toc(headings)), want)


class AutoSummaryTest(unittest.TestCase):
    def test_cuts_at_the_first_paragraph_end_past_the_word_limit(self):
        short = "<p>one two three</p>"
        long_p = "<p>" + " ".join(["w"] * build.SUMMARY_WORDS) + "</p>"
        cases = [
            ("short page, no truncation", short, ("one two three", False)),
            ("exactly the limit, nothing after", long_p, (" ".join(["w"] * build.SUMMARY_WORDS), False)),
            ("limit reached, more follows", long_p + short, (" ".join(["w"] * build.SUMMARY_WORDS), True)),
            ("limit reached in second paragraph", short + long_p, (build.plain_text(short + long_p), False)),
            ("heading anchors are dropped", '<h2>T<a hidden class="anchor" href="#t">#</a></h2>', ("T", False)),
        ]
        for name, content, want in cases:
            with self.subTest(name):
                self.assertEqual(build.auto_summary(content), want)


class HeadingIdTest(unittest.TestCase):
    def test_ids_are_unique(self):
        cases = [
            ("# Foo\n# Bar", ["foo", "bar"]),
            ("# Foo\n# Foo\n# Foo", ["foo", "foo-1", "foo-2"]),
            ("# Foo\n# Foo\n# Foo 1", ["foo", "foo-1", "foo-1-1"]),
            ("# Foo 1\n# Foo\n# Foo", ["foo-1", "foo", "foo-2"]),
        ]
        for markdown, want in cases:
            with self.subTest(markdown=markdown):
                self.assertEqual(heading_ids(markdown), want)

    def test_anchor_link_points_at_the_heading(self):
        html, _ = build.render_markdown("## Hello *World*", {"lastmod": None})
        self.assertIn('<h2 id="hello-world">Hello <em>World</em><a hidden class="anchor"', html)
        self.assertIn('href="#hello-world"', html)


class ContentErrorsTest(unittest.TestCase):
    """A throwaway site root: its own content/ and an empty static/, with the real templates and config."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for d in ("content/posts", "content/daily", "static"):
            (self.root / d).mkdir(parents=True)
        for name, value in (("ROOT", self.root), ("CONTENT", self.root / "content")):
            patcher = mock.patch.object(build, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, rel: str, text: str) -> None:
        (self.root / "content" / rel).write_text(text)

    def build(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(out=self.root / "public", eyrie_lock=None, cache=self.root / "cache")

    def test_clean_content_builds(self):
        self.write("posts/a.md", post("A", tags='["ui ux"]'))
        self.build()
        self.assertTrue((self.root / "public/tags/ui-ux/index.html").is_file())

    def test_two_outputs_at_one_url_fail_the_build(self):
        cases = [
            ("tags that urlize alike",
             {"posts/a.md": post("A", tags='["ui ux"]'), "posts/b.md": post("B", tags='["ui-ux"]')},
             r"/tags/ui-ux/ is produced twice: by tags term 'ui ux' and by tags term 'ui-ux'"),
            ("page url equal to a section", {"posts/a.md": post("A"), "about.md": post("About", None, url="/posts/")},
             r"/posts/ is produced twice: by content/about.md and by section 'posts'"),
        ]
        for name, files, message in cases:
            with self.subTest(name):
                for rel, text in files.items():
                    self.write(rel, text)
                with self.assertRaisesRegex(SystemExit, message):
                    self.build()
                for rel in files:
                    (self.root / "content" / rel).unlink()

    def test_undated_post_or_daily_fails_with_its_path(self):
        for rel in ("posts/undated.md", "daily/undated.md"):
            with self.subTest(rel):
                self.write(rel, post("Undated", date=None))
                with self.assertRaisesRegex(SystemExit, f"content/{rel}: .*`date:`"):
                    self.build()
                (self.root / "content" / rel).unlink()

    def test_undated_top_level_page_is_fine(self):
        self.write("now.md", post("Now", date=None))
        self.build()
        self.assertTrue((self.root / "public/now/index.html").is_file())


if __name__ == "__main__":
    unittest.main()
