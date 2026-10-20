"""Pure helpers in build.py, plus the build's refusal of content it would get wrong."""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
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


class TempSite(unittest.TestCase):
    """A throwaway site root: its own content/ and an empty static/, with the real templates and config."""

    def setUp(self):
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("FUTURE", None)
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

    def outputs(self) -> dict[str, str]:
        out = self.root / "public"
        return {str(p.relative_to(out)): p.read_text() for p in out.rglob("*") if p.is_file()}


class ContentErrorsTest(TempSite):
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


class SchedulingTest(TempSite):
    NOW = datetime(2026, 10, 20, 3, 30, tzinfo=UTC)

    def test_is_scheduled(self):
        cases = [
            ("posts", "2026-10-21", True),
            ("daily", "2026-10-20T09:01:00+05:30", True),
            ("posts", "2026-10-20T09:00:00+05:30", False),  # exactly now
            ("posts", "2026-10-20", False),  # midnight UTC, earlier today
            ("posts", "2020-01-01", False),
            ("", "2999-01-01", False),  # top-level pages are never held back
        ]
        for section, date, want in cases:
            with self.subTest(section=section, date=date):
                page = {"section": section, "date": build.parse_date(date)}
                self.assertEqual(build.is_scheduled(page, self.NOW), want)

    def write_both(self) -> None:
        past = (datetime.now(UTC) - timedelta(minutes=1)).isoformat(timespec="seconds")
        self.write("posts/live.md", post("Live Post", past, tags='["shared"]'))
        self.write("posts/later.md", post("Zebra Future Post", "2999-01-01", tags='["shared", "zebratag"]'))
        self.write("daily/later.md", post("Zebra Future Daily", "2999-01-02"))
        self.write("archives.md", post("Archives", None, layout="archives"))

    def test_future_posts_are_in_no_output(self):
        self.write_both()
        self.build()
        files = self.outputs()
        for path in ("posts/later/index.html", "daily/later/index.html", "tags/zebratag/index.html"):
            self.assertNotIn(path, files)
        leaks = [path for path, text in files.items() if "Zebra" in text or "zebratag" in text or "/later/" in text]
        self.assertEqual(leaks, [])
        lists = ("index.html", "index.xml", "sitemap.xml", "index.json", "posts/index.html", "tags/shared/index.html")
        for path in lists:
            self.assertIn("/posts/live/", files[path], path)

    def test_future_1_includes_them(self):
        self.write_both()
        os.environ["FUTURE"] = "1"
        self.build()
        files = self.outputs()
        for path in ("posts/later/index.html", "daily/later/index.html", "tags/zebratag/index.html"):
            self.assertIn(path, files)
        for path in ("index.html", "index.xml", "sitemap.xml", "index.json", "tags/shared/index.html"):
            self.assertIn("/posts/later/", files[path], path)

    def test_scheduled_lists_upcoming_soonest_first(self):
        self.write_both()
        self.write("posts/draft.md", post("Draft", "2999-01-01", draft="true"))
        got = [(d.date().isoformat(), path, title) for d, path, title in build.scheduled(datetime.now(UTC))]
        self.assertEqual(got, [
            ("2999-01-01", "content/posts/later.md", "Zebra Future Post"),
            ("2999-01-02", "content/daily/later.md", "Zebra Future Daily"),
        ])



class LastUpdatedTest(TempSite):
    def test_about_and_lastmod_use_the_page_date_not_the_build_time(self):
        self.write("about.md", '---\ntitle: About\nlayout: about\ndate: 2023-01-01\n---\nhi\n')
        self.write("now.md", '---\ntitle: Now\nurl: /now/\ndate: 2024-02-03\n---\nUpdated {{< lastmod >}}\n')
        self.build()
        out = self.outputs()
        self.assertIn("Last updated <time datetime=\"2023-01-01T00:00:00+00:00\">January 1, 2023</time>",
                      out["about/index.html"])
        self.assertIn("Updated February 3, 2024 at 12:00 AM", out["now/index.html"])


if __name__ == "__main__":
    unittest.main()
