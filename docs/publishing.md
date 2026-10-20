# Publishing: diagrams and cross-posting

Status: **§1 diagrams built (phase 1)** and **scheduling built** (§3); interactive diagrams and cross-posting are still design only. Date: 2026-10-20.

I'm going to blog regularly. Posts need good diagrams, and they should reach readers on other platforms without me copying things around by hand. The site stays the canonical home: every copy points back to `alenabraham.me` with a canonical URL.

This builds on [build.md](build.md): my own Python build, plain static HTML, zero JS by default.

## 1. Diagrams

One pipeline, three kinds:

| Kind | Source in the post folder | On my site | On other platforms |
|---|---|---|---|
| **Mermaid** | a ` ```mermaid ` fenced block | SVG rendered at build time, so no Mermaid JS on the page | PNG, linked by absolute URL |
| **Designed SVG** | `diagrams/<name>.svg`, e.g. made with Claude | inlined SVG (themeable) or `<img>` | PNG, linked by absolute URL |
| **Interactive** (optional) | `diagrams/<name>.html` plus a static fallback | sandboxed `<iframe>`, with the fallback image for no-JS readers | the static PNG plus a "see the interactive version" link |

**As built (phase 1):** page bundles; Markdown and `{{< diagram >}}` SVGs, inlined with CSS variables or as `<img>`, plus light/dark pairs; `make diagrams` with committed Mermaid renders; `make diagram` scaffolding; the build rules below, except per-diagram limit overrides. The Mermaid post is converted and loads no JS. **Not yet:** interactive diagrams, raising a size limit per diagram in front matter. Code: `site/diagrams.py`, tests: `site/tests/test_diagrams.py`.

### Post layout

To keep diagrams next to the post, I'll move posts that have diagrams to a folder ("page bundle"). The build will support both shapes, and the URL doesn't change:

```
content/posts/my-post.md                  # still fine for posts without diagrams
content/posts/my-post/index.md            # → /posts/my-post/
content/posts/my-post/diagrams/flow.svg   # → /posts/my-post/diagrams/flow.svg
content/posts/my-post/diagrams/flow.png   #   fallback for other platforms
```

The URL parity check keeps passing, because existing URLs don't move.

### Mermaid: rendered at build time

- I write ` ```mermaid ` in Markdown. The existing `{{< mermaid >}}` shortcode keeps working as an alias.
- `make diagrams` renders each block with `@mermaid-js/mermaid-cli`, pinned to an exact version in `site/package.json` with a lockfile. It renders twice, once with a light theme and once with a dark theme, into SVG and PNG.
- Output is keyed by a hash of the block's source and **committed** under `diagrams/_mermaid/<sha>.{light,dark}.{svg,png}`. That keeps `make build` Python-only: Node and Chromium are only needed when a diagram actually changes.
- `make build` fails with "run `make diagrams`" if a block has no rendered output, so a stale render can't ship silently. CI only checks that the renders exist; it never needs Node.
- Result: the Mermaid post stops loading about 3 MB of JS, and the CDN script goes from the head template.

As built:
- **Mermaid needs a page bundle.** The renders live in that post's `diagrams/_mermaid/`, so a post and its diagrams move and get deleted together. A single-file post with Mermaid fails the build (and `make diagrams`) with "move it to `<slug>/index.md`". I chose this over a shared `content/diagrams/_mermaid/` because a shared folder would collect orphans and publish at URLs no post owns.
- **Every block needs an `accTitle: …` line** (Mermaid's own accessibility syntax). It becomes the `<title>` of the SVG and the alt text of the `<img>`. `accDescr:` is optional and becomes `<desc>`.
- `make diagrams` runs `npm ci` in `site/`, renders only what's missing (`<sha>` is the first 16 hex chars of the SHA-256 of the block), and deletes renders no block uses any more. Labels are rendered as SVG text (`htmlLabels: false` in `site/mermaid.json`), so the renders pass the same checks as any SVG. SVGs have a transparent background; the PNGs are white (light) and #111 (dark), at 2x.
- Pinned: `@mermaid-js/mermaid-cli` 11.17.0 (the lockfile was resolved with `npm install --before` two weeks back, so no dependency is newer than that). Puppeteer downloads its own Chromium into `~/.cache/puppeteer` on the first `npm ci`.

### Designed SVGs, for example from Claude

These are the polished, hand-designed architecture, flow and sequence diagrams, like the ones an "archify"-style workflow produces: standalone HTML with inline SVG, light and dark themes, and SVG/PNG export.

**My authoring workflow:**
1. Ask Claude for the diagram, saying it should be for my blog and should use the theme variables (below).
2. Export the SVG, plus a PNG for other platforms, into `content/posts/<slug>/diagrams/`.
3. Reference it with plain Markdown, `![Request flow through the API gateway](diagrams/flow.svg)`, or the shortcode when I need options, `{{< diagram src="flow.svg" alt="…" caption="…" >}}`.
4. `make serve`, check it in light and dark, commit.

`make diagram POST=my-post NAME=flow` scaffolds the folder and a starter SVG with the theme variables and `<title>` already in place, and prints the prompt snippet to give Claude.

**Theming. The build picks one of two modes per diagram:**
- **CSS variables (preferred).** The SVG uses `fill="var(--diagram-fg, #1f2328)"` and similar, with light defaults. The build **inlines** it, so my site's `body.dark` rules switch the variables (`--diagram-fg`, `--diagram-bg`, `--diagram-accent`, `--diagram-muted`, `--diagram-line`). It's one file, it follows the theme toggle, and the page makes no extra request.
- **Two variants.** If both `flow.light.svg` and `flow.dark.svg` exist, the build emits two `<img>` tags and CSS shows the one that matches the theme. This is for SVGs I can't make variable-driven. Hidden lazy images aren't downloaded.

Mermaid renders use the two-variant mode.

The variables' light and dark values are in `site/css/extended/diagram.css`. Inlined SVGs get `role="img"` and `aria-labelledby` pointing at their title, and their `id`s prefixed with the file name (`flow-`, then `flow2-` for a second copy on the same page).

### Hand-drawn diagrams (Excalidraw)

For a sketchy, whiteboard look I use the `excalidraw` Claude skill, which drives a small CLI (`excalidraw read | apply | render`, installed from the skill's directory with `uv tool install`; PNG output needs `rsvg-convert` from `brew install librsvg`).

1. Keep the source in the bundle: `content/posts/<slug>/diagrams/<name>.excalidraw`. The build doesn't publish `.excalidraw` files.
2. Export both formats next to it: `excalidraw render diagrams/<name>.excalidraw diagrams/<name>.svg` and `… diagrams/<name>.png`.
3. Add a `<title>` as the SVG's first child (the export doesn't have one; the build will say so) and check it has no `<image>` or `data:` URLs (embedded images make the build reject it; export those diagrams as PNG only and use a normal Markdown image).
4. Reference it like any other diagram: `![Request flow, sketched](diagrams/<name>.svg)`. Excalidraw SVGs have fixed colours, so they're shown as `<img>`. For dark mode, export a dark variant as `<name>.dark.svg` (+ `.dark.png`), rename the first to `<name>.light.svg` (+ `.light.png`), and keep referencing `diagrams/<name>.svg`.

### Interactive diagrams (optional, site only)

- `diagrams/<name>.html` is a standalone page, for example with hover or step-by-step tracing. It's embedded with `{{< diagram src="flow.svg" interactive="flow.html" alt="…" >}}`.
- The site renders `<iframe sandbox="allow-scripts" loading="lazy">`. Without `allow-same-origin`, the iframe can't touch my page or cookies. The static SVG is the fallback inside `<noscript>`, and a "static version" link sits under the iframe.
- This is the only way JS gets onto a post. The page itself still ships none.

### Rules the build enforces (it fails, it doesn't warn)

| Rule | Check |
|---|---|
| **Accessible** | Every diagram image has non-empty alt text. Every SVG has a non-empty `<title>` as its first child; `<desc>` is recommended. Inlined SVGs get `role="img"` and `aria-labelledby` pointing at the title |
| **Safe to inline** | SVGs are parsed with `defusedxml`, pinned (no XXE). The build rejects `<script>`, `<foreignObject>`, any `on*` attribute, `javascript:` or `data:` URLs, and external `<use href>`/`<image href>`. It rejects rather than silently stripping, so I fix the source |
| **Size** | Inlined SVG ≤ 100 KB, `<img>` SVG ≤ 500 KB, PNG ≤ 400 KB, interactive HTML ≤ 1 MB (including inlined assets). Each limit lives in `site/site.yaml` and can be raised per diagram with a front matter reason |
| **Fallbacks exist** | Every SVG or interactive diagram has a PNG next to it, which syndication needs. Mermaid gets its PNG from `make diagrams` |
| **IDs don't collide** | Inlined SVGs get their `id`s prefixed with the diagram name, so two diagrams on one page can't clash |

## 2. Cross-posting (syndication)

### What each platform allows (checked October 2026)

| Platform | Automation | Canonical URL | Notes |
|---|---|---|---|
| **Dev.to** (Forem) | Yes, through `POST https://dev.to/api/articles` with an `api-key` header and a free key from dev.to/settings/extensions | `article.canonical_url` | `published: false` gives a draft. Takes Markdown and up to 4 tags. Images need absolute URLs |
| **Hashnode** | **Pro plan only now.** On 2026-05-13 Hashnode retired free GraphQL API access: "every API request, queries and mutations, now requires a Pro plan on your publication". `gql.hashnode.com` now redirects to that changelog, so the "allow-listed" reports are this. Upgrading allow-lists the publication automatically | `publishPost(input: { originalArticleURL })` | It needs a PAT and the publication ID (query `me { publications }`). GraphQL can return HTTP 200 with errors, so check `errors` |
| **Medium** | **No.** Medium stopped issuing integration tokens on 2025-01-01, and the API is unsupported. Tokens issued before then still work | "Import a story" from the live URL sets the canonical link | Manual. Doesn't render Mermaid or inline SVG, so use PNGs |
| **Substack** | **No official API.** I won't use the reverse-engineered libraries: they're fragile and risk the account | Not supported as a field. I'll add an "Originally published at …" line at the top | Manual: paste into a draft and **schedule** it for the same time the site post goes out |

**What this means:** Dev.to is the only platform I can automate for free. Hashnode is automatic only if I pay for Pro; otherwise it's manual, like Medium (paste, then set "originally published at" in the post settings).

### The flow

```
merge to main ─► build + deploy (existing job)
              └► syndicate job (new, needs: deploy)
                   1. find new posts: in public/, not yet in site/syndication.json
                   2. wait until https://alenabraham.me/posts/<slug>/ returns 200
                   3. Dev.to: create the article (canonical_url = live URL)    ─┐ auto
                      Hashnode: publishPost with originalArticleURL (if Pro) ─┘
                   4. open a GitHub issue per post: "Syndicate: <title>"        manual checklist
                   5. commit the updated site/syndication.json [skip ci]
```

- **Idempotency.** `site/syndication.json` maps each post to what it got, for example `{"/posts/x/": {"devto": {"id": 123, "url": "…"}, "hashnode": null, "issue": 45}}`. A post that's already in the file is skipped. As a second guard, before creating on Dev.to the job lists my articles and matches on `canonical_url`, so a lost state commit can't cause a duplicate.
- **Opting out per post** in front matter: `syndicate: {devto: false, medium: false}`. The default platform list lives in `site/site.yaml` under `syndication.platforms`, and commenting out a platform there switches it off everywhere, the same toggle pattern as the rest of the site. `syndicate: false` skips the post entirely.
- **The checklist issue** for the manual platforms contains:
  - the canonical URL
  - the Medium import link (`https://medium.com/p/import`) with "paste the canonical URL"
  - the Substack "new post" link with "paste, add the 'originally published' line, schedule for <publish time>"
  - Hashnode steps, if it isn't automated
  - the post rendered for pasting (Markdown and HTML, in collapsible blocks), with every image and diagram as an absolute `https://alenabraham.me/…` PNG URL
  - one checkbox per platform

  Closing the issue is my "done" signal.
- **Secrets** are GitHub Actions secrets on **`abrahamalen/alen-abraham.github.io` only**: `DEVTO_API_KEY`, plus `HASHNODE_PAT` and `HASHNODE_PUBLICATION_ID` if I go Pro. The job runs only when `github.repository == 'abrahamalen/alen-abraham.github.io'` and the event is a push to `main`, so forks and PR runs never see them. The token gets `issues: write` and `contents: write`, and nothing else.
- **Failures** don't fail the deploy. The job reports what it couldn't do in the checklist issue and leaves the state file untouched for that platform, so the next run retries.

### How diagrams travel

| Diagram | On my site | Dev.to / Hashnode (API) | Medium / Substack (manual) |
|---|---|---|---|
| Mermaid | themed inline SVG | `![alt](https://alenabraham.me/…/<sha>.light.png)` | the same PNG, pasted or imported |
| Designed SVG | inline SVG with CSS variables | absolute PNG URL | absolute PNG URL |
| Interactive | sandboxed iframe | PNG plus "Interactive version on alenabraham.me →" | same |

The syndication renderer is the Markdown renderer with these rewrites turned on: relative to absolute URLs, Mermaid blocks to PNG images, SVGs to their PNGs, and shortcodes expanded. Platforms get PNGs because Medium and Substack don't render Mermaid or inline SVG, and Dev.to and Hashnode handle PNG more reliably than SVG.

## 3. Later (not in this phase)

- **Scheduling (built, 2026-10-20; see "Scheduling a post" in [build.md](build.md)).** Posts get a future `date`, the build skips future-dated posts, and a daily scheduled CI run (03:30 UTC, 09:00 IST) rebuilds and deploys. Still to do with syndication: the syndicate job fires on the run where a post first appears, which is its publish day, and the Substack checklist uses that date for scheduling.
- Updating copies when I edit a post: a Dev.to `PUT` plus a checklist note for the manual platforms.
- Webmentions or "also on" links under posts, pointing to the copies.

## 4. Plan, one PR per phase

1. **Diagrams** (phase 1 built; interactive diagrams and per-diagram limit overrides to do):
   - page bundles
   - `make diagrams` (pinned mermaid-cli, committed renders)
   - the `diagram` shortcode and Markdown image support
   - inlining with CSS variables
   - the build checks (alt/title, sanitiser, sizes, fallbacks)
   - converting the existing Mermaid post, with before/after screenshots
   - documenting the Claude workflow
2. **Syndication:**
   - the syndication renderer
   - the `syndicate` CI job for Dev.to (Hashnode behind a config flag if I go Pro)
   - `site/syndication.json`
   - checklist issues
   - front matter opt-outs
   - a dry-run mode (`make syndicate-dry-run`) that prints what it would do
3. **Scheduling**: built (future-dated posts are skipped, daily deploy at 09:00 IST).

## Open questions

1. **Which platforms do I actually post to?** Hashnode and Dev.to are already linked from my About page, Medium is in the home socials, and Substack is new. Which of these do I have accounts on and want to keep?
2. **Hashnode Pro:** is automating Hashnode worth the Pro subscription, or is a manual checklist step fine?
3. **Dev.to:** publish immediately, or create drafts that I publish by hand?
4. **Medium:** does my account have a legacy integration token from before 2025-01-01? If so, I could automate Medium with it while it lasts.
5. **Substack:** do I have a publication yet? If so, which one, and should posts go to email subscribers or web only?
6. ~~**Committed Mermaid renders**~~: yes, committed under each bundle's `diagrams/_mermaid/` (about 0.8 MB for the Mermaid post's four diagrams, PNGs included; a reader downloads only the SVG for their theme, about 90 KB for the whole post).
