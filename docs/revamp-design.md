# Site revamp — design

Status: **Design** (phase 1 of 3: design → prototype → code). Date: 2026-10-19.

## 1. Current state

| Area | What's there |
|---|---|
| Hugo | Builds clean on `v0.157.0+extended` (`hugo --minify`: 63 pages, 0 warnings, ~0.2s). CI pins `hugo-version: "latest"`. |
| Theme | PaperMod submodule at `0989c28` (v7.0-70). |
| Deploy | `hugo` branch → `peaceiris/actions-gh-pages` → `gh-pages` on `abrahamalen/alen-abraham.github.io` (CNAME `alenabraham.me`). |
| Content | `posts/` (9, last one 2025-04), `daily/` (2, Mar–Apr 2025), single pages: `about`, `resume`, `now`, `dailies`, `archives`. |
| Menu | Archives · Categories · About. Resume, Now and Dailies are not in the nav. |
| Overrides | `layouts/`: `baseof`, `head`, `header`, `home_info`, `extend_head`, `list`, `archives`, `about`, `dailies`, `daily/single`, `search`, `rss.xml`, `index.json`, `opengraph`, `twitter_cards`, shortcodes `lastmod` and `mermaid`. `assets/css/`: about 15 files, most of them full copies of the theme's `common/*` and `core/*` CSS. |

## 2. Problems

1. **Forked theme files.** `head.html`, `header.html`, `baseof.html`, `main.css` and `theme-vars.css` are copies of PaperMod files that have since changed upstream (for example, `head.html` now differs from the theme by about 360 lines). Every theme bump can break things without warning, and it's unclear which lines are customisations.
2. **Weight on every page.** Mermaid 10.6 (~3 MB) and all of Font Awesome 6.4 load site-wide from `extend_head.html`. Only 1 post uses Mermaid.
3. **Navigation.** The pages that matter most (Resume, Now) can only be reached from links in the home intro. Categories and Archives sit in the nav, but there are only 9 posts.
4. **Identity.** The home title "Scale, Stabilize and Secure Systems" is generic. The default PaperMod dark look doesn't stand out. The copy disagrees with itself: `now.md` says *Senior SRE*, while `about.md` and the resume say *Senior DevOps*.
5. **Content drift.** The Now page was last edited long ago and is mostly commented out. The Twitter link (`op__trojan`) may be dead. Medium, Behance, Dev.to and Hashnode are all listed.
6. **Resume.** It's about 70 hand-written `<div>`s inside Markdown (`linkedin-exp`, styled by `timeline.css`). It's hard to edit and there's no print or PDF view.
7. **Favicons hard-coded in `baseof.html`,** duplicating what `head.html` already emits. A section like `/eyrie` therefore can't swap them.
8. **Hygiene.** `resources/_gen` and `.hugo_build.lock` are committed. CI uses `actions/checkout@v2`.

## 3. Goals / non-goals

**Goals (small revamp)**
- A clearer identity on the home page: one line saying who Alen is and what he does now, plus links to Resume, Writing and Now.
- A nav that reflects the site: **Writing · Resume · Now · About** (plus a search icon).
- A distinct visual identity through a token-level restyle (colour, type, borders), with no layout rewrite.
- Shrink the theme fork: keep only the overrides that are needed, and make each one small and documented.
- Load Mermaid and icons only where they're used.
- Leave a clean slot for `/eyrie`.
- A resume that's easier to edit and prints cleanly.

**Non-goals**
- Moving off PaperMod or Hugo, or adding a JS framework or build step.
- Rewriting or migrating old posts. URLs stay unchanged (`/posts/*`, `/resume/`, `/now/`, `/about/`, `/dailies/`).
- Building the `/eyrie` landing page, which is a separate later PR.
- Comments, a newsletter, or analytics changes (Plausible stays).

## 4. Information architecture

```
/                 Home: name, one-line role, 3 links, latest 3–5 posts
/posts/           Writing (nav label "Writing"); categories/tags stay but leave the nav
/resume/          Resume (data-driven, print stylesheet)
/now/             Now (refreshed, shows lastmod)
/about/           About + contact
/dailies/         Scrapbook: kept and linked from Writing, not in the nav
/archives/        Kept, linked from the Writing page footer
/search/          Icon in the header
/eyrie/           RESERVED: product landing page, built later
```

**`/eyrie` requirements (to design for now, build later)**
- It gets its own section, `content/eyrie/_index.md` with `layout: eyrie`, plus `layouts/eyrie/` templates.
- It needs **its own `<head>`**: Eyrie title, description, OG image, and an **Eyrie favicon set**, not the site's "ae" favicon. Two changes in the code PR make this possible:
  1. Move the favicon `<link>`s out of `baseof.html` into one partial, `partials/favicons.html`, that reads `.Params.favicon` or a section param and falls back to the site set.
  2. Let the `eyrie` section use its own `baseof` (`layouts/eyrie/baseof.html`) so it can drop the site header and footer if wanted.
- Assets go in `static/eyrie/` (favicons, OG image) so they never collide with the root ones.
- Nav: an optional "Eyrie" or "Projects" entry, added only when the page ships.

## 5. Visual direction

### Option A: PaperMod tweaks (light touch)
Keep the PaperMod look. Change the accent colour, switch the default theme to `auto`, swap the home title for a real intro, tidy the nav and drop the custom heading sizes.
- **Pros:** about a day of work, near-zero risk, nothing to maintain.
- **Cons:** it still looks like the thousands of other PaperMod sites, so problem 4 isn't solved.

### Option B: Nexus-style "paper and ink" (recommended)
Bring in the Nexus visual language as a **token layer over PaperMod**:
- **Colour:** a warm paper background (`#f6f3ec`-ish), ink text (`#1c1a17`), one muted accent, and **1px hairline borders** in place of shadows and filled cards. Dark mode becomes a warm charcoal with the same hairlines, not PaperMod's grey.
- **Type:** **Geist** for UI and body, **Instrument Serif** for page titles and the home name, and Geist Mono for code. All are self-hosted in `static/fonts/` (no Google Fonts request, which matches the privacy stance).
- **Eyebrow labels:** small uppercase, letter-spaced labels above titles and sections (`WRITING · 2025`, `NOW`, `EXPERIENCE`).
- **Layout:** stays PaperMod's, at the same widths. Post lists become hairline-ruled rows (date · title · tag) instead of cards.
- **Pros:** a distinctive look, and it matches Eyrie's Nexus-style UI, so `/eyrie` and the main site feel related while keeping separate brands.
- **Cons:** about 2–3× the CSS work of Option A. Fonts add roughly 60–90 KB (woff2, subset). Contrast must be checked in both themes.

**Recommendation: B, scoped to tokens and typography plus 3 templates** (home, list, single headers). That gets most of the identity gain for a small diff. A is the fallback if the prototype shows that B fights PaperMod too much.

## 6. How theme changes are done

- **Never edit `themes/PaperMod`.** The submodule stays pinned. Bumping it is a separate, explicit change.
- **CSS:** all new styling goes in `assets/css/extended/*.css`, which PaperMod bundles automatically after its own CSS:
  - `tokens.css`: colours, fonts, spacing and border variables, overriding `--theme`, `--primary` and so on for both `:root` and `.dark`.
  - `typography.css`, `home.css`, `lists.css`, `resume.css` (which replaces `timeline.css`), and `print.css`.
- **Delete the copied theme CSS** (`assets/css/common/*`, `core/theme-vars.css`) where `extended/` can do the job instead. That removes about 900 lines of fork.
- **Layouts:** override only through PaperMod's extension points (`extend_head.html`, `extend_footer.html`, `home_info.html`) and small single-purpose partials. Re-sync `head.html`, `header.html` and `baseof.html` with the pinned theme, then reapply the diff as a minimal patch. A comment at the top of each overridden file will name the theme commit it was copied from and what changed.
- **Mermaid:** load it only when a page sets `mermaid: true` in front matter (or the shortcode is used). Icons: use PaperMod's built-in SVG social icons and drop Font Awesome.
- **Resume:** move it to `data/resume.yaml` plus a `layouts/resume/` template, so updates become YAML edits instead of `<div>` surgery.

## 7. Conflict risk with the WIP resume branch

- `feature/update-resume` has **no commits beyond `hugo`**: it was merged via #1 and #36. The diff `hugo...feature/update-resume` is empty.
- The only local WIP is **uncommitted edits inside the submodule** (`themes/PaperMod/layouts/partials/templates/{opengraph,twitter_cards}.html`). The site already overrides both files at the repo root, so those submodule edits are currently **shadowed and have no effect**. The revamp won't touch either path.
- **Real risk: the resume.** Moving the resume to `data/resume.yaml` (section 6) would conflict with any further resume edits. Mitigation: do the resume data migration **last**, in its own code PR, after Alen confirms the resume WIP is done or moves those edits to the repo-root override.

## 8. Follow-up PRs (not stacked, each targets `hugo`)

1. **Prototype PR:** a static `prototype/` page (or a `/_proto/` draft page with `build.render: never` in production) showing Option B tokens on home, post list, a post, and the resume. It includes light and dark screenshots in the PR description. No changes to live layouts.
2. **Code PR(s)**, opened one at a time after the prototype is approved:
   - 2a. Tokens, fonts, nav/IA changes, home intro, the favicon partial and the `/eyrie` slot, conditional Mermaid, dropping Font Awesome, re-syncing overrides with the theme, and pinning Hugo in CI.
   - 2b. Resume moved to data plus a print stylesheet (after the WIP is confirmed done).
   - Later: the `/eyrie` landing page (Eyrie branding and favicon), as its own PR.

## Open questions

1. Is Option B (paper and ink) OK, or does Alen prefer Option A?
2. Default theme: keep **dark** by default, or switch to **auto** or light? Paper-and-ink reads best in light.
3. Nav labels: "Writing" or "Blog"? Should Dailies stay public?
4. Socials: are Twitter (`op__trojan`), Behance and Medium still live and wanted?
5. Title: "Senior DevOps" or "Senior SRE" everywhere?
6. Is the resume WIP finished? What are the uncommitted submodule edits to `opengraph` and `twitter_cards` meant to do? They're shadowed today.
7. Should `/eyrie` share the site header and footer, or be fully standalone?
