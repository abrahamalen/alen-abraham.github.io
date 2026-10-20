# How this site is built, and why

Date: 2026-10-20. This supersedes the "approaches" part of [revamp-design.md](revamp-design.md), which is the history of how I got here.

I'm going to blog here regularly now, and alenabraham.me/eyrie will be Eyrie's product homepage. Before committing to that I weighed Hugo and Astro against the build I already have, and I'm keeping my own.

Diagrams and cross-posting are designed separately in [publishing.md](publishing.md).

## 1. Decision

- **My own Python build** (`site/`). No static-site framework.
- **The blog stays plain static HTML with zero JS by default.** A page gets a script only when its content needs one: Mermaid on diagram posts, highlight.js on pages with code. The theme toggle and back-to-top link are the only always-on inline JS.
- **The current minimal look stays.** It's PaperMod's look, but now I own the CSS in `site/css/`, with the MIT credit kept.

## 2. Why

**Full control and readable code.** The whole pipeline is about 370 lines of Python, plus Jinja templates and plain CSS. There's nothing I can't read, no hidden defaults, and no theme or framework upgrades to chase.

**The Hugo problems I actually hit:**
- **Theme-override drift.** About 15 PaperMod files were copied into `layouts/` and `assets/` and had silently diverged; `head.html` alone was about 360 lines off. I was maintaining a fork without owning it.
- **`hugo-version: latest` in CI.** Every deploy could pick up a new Hugo with different behaviour.
- **Dead config.** `ShowReadingTime`, `ShowToc`, `ShowShareButtons`, `images` and others were nested under `cover:` in `config.yml`, so they did nothing, and Hugo never complained.
- **About 3 MB of Mermaid on every page**, plus all of Font Awesome, because extending the theme's head was the easy path.

**The trade-off I accept.** Hugo gave me pagination, image processing, i18n and search for free. Here each of those becomes a small function I write *when I actually need it*, not before. Today I need none of them: all posts fit on one page, images are pre-sized, the site is English-only, and search was dropped.

## 3. Habits that keep it healthy

- **Add features only when they're needed**, each as a small function with a test. Write the test next to the function, and add pytest to the pinned deps when the first test lands.
- **Keep the guardrails in every PR:**
  - `make check`, the URL parity check against `site/urls.txt`. If a URL goes away on purpose, `urls.txt` changes in the same PR, with the reason.
  - Pinned deps: `site/requirements.in`, compiled into `site/requirements.txt` with `uv pip compile`. Bump them deliberately, never to `latest`.
  - Before/after screenshots (light, dark and mobile) in the PR for anything that touches templates or CSS.
- **Split, don't switch.** When `build.py` passes about 800 lines, I'll split it into modules (`content.py` for loading and Markdown, `pages.py` for rendering, `feeds.py` for RSS and the sitemap) rather than adopt a framework.

## Turning things on and off

Everything optional that's visible on the site is driven by `site/site.yaml`. Comment out a line (or delete it) and that piece stops rendering on every page. `make test` checks this (`site/tests/test_toggles.py`), and CI runs it.

| What | Key / line in `site/site.yaml` | Effect when commented out |
|---|---|---|
| Header nav items | each `- {name: …, url: …}` line under `menu:` | That item disappears from the top-right nav. Comment out every entry and the nav is gone. The page itself still builds |
| Now / Resume in the nav | already commented out under `menu:` | Uncomment `# - {name: Now, url: /now/}` or `# - {name: Resume, url: /resume/}` to show them. They're off on purpose, because the home intro links to both |
| Home social icons | each line under `socials:` | That icon disappears from "Also seen on" and from the JSON-LD `sameAs`. With no socials, the whole row goes |
| "Also seen on:" label | `home.socials_label` | The icons stay, without the label |
| Home headline | `home.title` | No headline on the home page |
| Home intro paragraphs | each line under `home.intro:` | That paragraph disappears |
| Recruiter line | `home.aside` | The small faded line (and the gap above it) goes |
| Whole home intro block | `home:` and everything under it | Home shows only the post list |
| Archives top links | each line under `archives_links:` | That link goes. Font Awesome stops loading when no link has an `icon` |
| Footer | `footer_copyright: true` | No footer |
| Theme toggle | `theme_toggle: true` | No light/dark button, so the site stays in its default dark theme |
| Back-to-top arrow | `back_to_top: true` | No floating arrow |
| Analytics | `plausible_domain:` | No Plausible script anywhere. Per page: `excludeAnalytics: true` in front matter |
| Eyrie landing page at `/eyrie/` | `version:` in `site/eyrie.lock` (not `site.yaml`) | The build skips the release download and renders the coming-soon page (`content/eyrie.md`, `eyrie_fallback: true`) with the icons in `static/eyrie/` instead. `make check` then reports the landing-only files in `urls.txt` (`/eyrie/install.sh`, `/eyrie/og.png`) as missing |

Per-page switches live in front matter instead: `favicons:` / `favicon_svg:` (which icon set the page uses), `title_tag:` / `site_name:` (head overrides), `excludeFromFeeds: true` (keeps the page out of the home RSS) and `ShowToc: true` (table of contents).

## 4. The /eyrie plan (built: option A)

**What it is.** `/eyrie` is a small Vite + React landing page that lives in the Eyrie repo (`abrahamalen/eyrie`, which is public). It reuses Eyrie's own Tailwind tokens and components, such as the "e." logo and the cards, so it looks like the product rather than like my blog. The blog itself stays zero-JS; React exists only under `/eyrie/`.

**How it gets into the site.** At site build time, the landing page's static build output (`index.html` plus hashed assets, built with Vite `base: "/eyrie/"`) is copied into `public/eyrie/`.

| Option | How | Pros | Cons |
|---|---|---|---|
| **A. Pinned release artifact** (recommended) | Eyrie CI publishes `eyrie-landing-vX.Y.Z.tar.gz` as a GitHub release asset. `site/eyrie.lock` pins the version and its sha256. `build.py` downloads the archive, checks the hash and unpacks it into `public/eyrie/` | Reproducible and auditable. The site repo has no Node toolchain and no generated files in git. Updating is a one-line lock bump in a reviewed PR | It needs a release step in Eyrie CI, and `make build` needs network access the first time (cache the download in `.cache/`) |
| B. Git submodule | Add the Eyrie repo as a submodule and build the landing page during the site build | Always the exact commit | It brings back the submodule pain I just removed, and the site build would need Node, npm and Vite |
| C. Checked-in build | Commit the built `eyrie/` files into `static/eyrie/` | Simplest, works offline | Generated, minified files in git, noisy diffs, and it's easy to forget to update |

**I'm going with A.** It keeps the site build Python-only and makes every Eyrie update an explicit, pinned change. That's the same discipline I use for Python deps.

**Head and favicons.**
- The Vite page ships its own `index.html`, so its `<title>`, description, OG image and Eyrie favicon set (under `public/eyrie/`) are Eyrie's, not the site's "ae" icons.
- Any page the *site* renders under `/eyrie/` (for example a fallback page if the artifact is missing in a local build) uses the existing `favicons:` front-matter hook, set to `favicons: /eyrie/`, so it points at the same Eyrie icons.
- Eyrie stays out of the main nav until the page ships.

**Guardrails.**
- The copy runs **after** the site has rendered.
- The build fails if the site itself generated anything under `/eyrie/`, or if the artifact's hash doesn't match.
- `make check` must keep passing. `/eyrie/` only adds files, and `site/urls.txt` lists its stable files (`index.html`, `install.sh`, the icons and `og.png`), not the hashed `assets/`.

**As built.**
- `site/eyrie.lock` holds `version:` and `sha256:` (from the release's `SHA256SUMS`). To update, bump both in one PR.
- `build.py` downloads `eyrie-landing-<version>.tar.gz` from the `v<version>` release into `.cache/eyrie/` (gitignored), verifies the hash and fails on a mismatch. A cached tarball with the right hash is reused, so offline builds work once it's been fetched. The fetch happens before rendering; the unpack into `public/eyrie/` happens after.
- With the lock on, the coming-soon page and `static/eyrie/` are left out, and the build fails if anything else rendered under `/eyrie/`.
- `/eyrie/install.sh` comes from the tarball; GitHub Pages serves it as `application/x-sh`, which `curl … | sh` is fine with.

## 5. Go-live

1. Everything lands on the fork's `revamp` branch first. The site runs fully locally (`make serve`) and CI is green there.
2. **One final PR**: fork `revamp` → `abrahamalen/alen-abraham.github.io:hugo`, which I merge on the personal repo. The existing workflow builds with `make build` and `make check`, and publishes `public/` to `gh-pages` (same CNAME), so the switch is just that merge.
3. Done 2026-10-20: the deploy branch is `main` (renamed from `hugo`); the workflow's branch filters and deploy condition follow it.
