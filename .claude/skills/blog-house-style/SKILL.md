---
name: blog-house-style
description: House style for writing on alenabraham.me (Alen Abraham's site, this repo). Use when drafting, editing or reviewing a blog post in content/posts/ or a daily in content/daily/, scheduling a post, adding a diagram to a post, or turning a post into a LinkedIn post, X thread or a Dev.to/Medium/Substack/Hashnode copy.
---

# Writing for alenabraham.me

Posts live in `content/posts/` and dailies in `content/daily/`. The build is `site/build.py`; how it works is in `docs/build.md` and `docs/publishing.md`. Read those two when something here is unclear.

## Voice

Write as Alen: a platform/DevOps engineer from Kerala, writing for other engineers.

- First person, plain and direct. "I tried X. It broke because Y." Not "one might consider".
- Short sentences, mostly 8 to 20 words. Short paragraphs, two to four sentences.
- Concrete over general: the command he ran, the error he saw, the number before and after.
- Practical. Every section should leave the reader able to do something.
- Casual is fine ("lol" appears in old posts), but it's not jokey and never salesy.
- Openings: start with the situation or the problem, in one or two sentences. Old posts open with a plain definition ("**GitHub Actions** is a ..."); for new posts prefer opening with what happened.
- Closings: a short wrap-up, then `Thank you for the read.` on its own line. Repost links, if any, go on the line after it.

Avoid, from his older posts: stacked adjectives ("incredible", "breathtaking", "indelible mark"), "a testament to", "cutting-edge", "revolutionizing", "seamlessly", and pasting a vendor's marketing description. Those are the parts that read worst today.

Never mention his employer's internals, clients, colleagues, products or numbers. Work can come up only generically ("at work", "on a prod system").

## Humanizer rules (summary)

From [blader/humanizer](https://github.com/blader/humanizer). Apply them to every draft:

- No em dashes as connectors. Use a comma, period, colon or parentheses.
- No staging: "not just X, but Y", "Here's the thing", "Let's dive in", dramatic one-line closers, aphorisms.
- No forced triads. Use as many items as there really are.
- No AI words: delve, crucial, showcase, testament, landscape, robust, seamless, leverage, pivotal, game-changer.
- No inflated verbs: "serves as", "boasts", "features" become "is", "has".
- No "-ing" riders tacked onto facts ("..., highlighting the need for ...").
- No decorative bold on every list item; sentence-case headings; no emoji in headings.
- No chatbot residue: greetings, "I hope this helps", "Great question".
- Don't vary sentence openings by rule, but don't start three sentences in a row with "I" or "This".
- Keep every fact. Don't add numbers, names or quotes that weren't given.
- Listicles only when the content really is a list (steps, commands, a checklist).

## Front matter

```yaml
---
title: "Stacked pull requests and squash merges don't mix"   # sentence case, specific
date: 2026-10-23T09:00:00+05:30    # always with +05:30; future = scheduled
description: "Under 160 characters. Used for <meta>, link previews and feeds."
summary: "Optional. Shown on the home and list pages; defaults to the first ~70 words."
tags: ["git", "github", "devops"]  # lowercase; 3 to 5; reuse existing tags
categories: ["devops"]             # one, from: devops, tutorial, work, career, resources, dsa
series: ["..."]                    # optional, only for a real multi-part series
ShowToc: true                      # for posts with 3+ sections
cover:                             # optional; becomes the og:image
  image: "/images/posts/<slug>/cover-image.jpg"
  alt: "What the image shows"
  caption: "Photo credit, with a link if it's not mine"
  relative: false
draft: true                        # leaves it out of the build entirely
excludeFromFeeds: true             # optional, keeps it out of the home RSS
searchHidden: true                 # optional, keeps it out of the Archives search
syndicate: {devto: false, medium: false}   # optional, per-platform opt-out; `syndicate: false` skips all
---
```

Dailies are lighter: `title` and `date` only (`date: 2026-10-20` is fine; without an offset it means 00:00 UTC).

Taxonomies are `tags`, `categories` and `series` (`site/site.yaml`). Every new term creates a new page, so reuse terms where you can (`grep -h "^tags:" content/posts/*.md content/posts/*/index.md`).

## Page bundles and diagrams

- No diagrams: `content/posts/<slug>.md` is fine.
- Any diagram or local image: use a bundle, `content/posts/<slug>/index.md`, with files under `diagrams/`. Same URL either way.
- Mermaid: a ` ```mermaid ` block, inside a bundle, with an `accTitle:` line that says what the diagram shows (it becomes the alt text). Run `make diagrams` and commit `diagrams/_mermaid/`.
- Designed SVGs: `make diagram POST=<slug> NAME=<name>`, then see `docs/publishing.md` §1. Every SVG needs a `<title>` and a PNG next to it.

## Pre-publish checklist

- [ ] Title is specific and in sentence case. `description` is set and ≤160 characters.
- [ ] `date` has `+05:30`. A future date means scheduled: check `make scheduled` lists it.
- [ ] Every image has real alt text (not "this is a post image"). Every Mermaid block has `accTitle:`.
- [ ] Diagrams are in a page bundle; `make diagrams` has run and the renders are committed.
- [ ] Code blocks have a language (`bash`, `yaml`, `python`). Scripts start with `set -euo pipefail`; one-off commands don't need it.
- [ ] Commands are real and copy-pasteable. Placeholders look like `<branch>`.
- [ ] Links work; internal links are root-relative (`/posts/x/`).
- [ ] No employer internals, clients or colleagues.
- [ ] Humanizer pass done: search the draft for `—`, "delve", "crucial", "not just", "Let's".
- [ ] Ends with `Thank you for the read.`
- [ ] `make lint`, `make test` and `make check` pass. For a scheduled post, `FUTURE=1 make serve` to preview it.
- [ ] Light and dark checked for anything with a diagram.

## Templates

Pick one and fill it in: `references/templates.md`.

- **Technical:** problem, context, what I tried, the fix, numbers, lessons.
- **Narrative or travel:** scene-first opening, one concrete detail per section, no listicles.

## Cross-posting

The site is always canonical. Details and API notes are in `docs/publishing.md` §2.

- **Dev.to:** set `canonical_url` to the live `https://alenabraham.me/posts/<slug>/`. At most 4 tags. Images and diagrams as absolute PNG URLs (Mermaid: `.../diagrams/_mermaid/<sha>.light.png`).
- **Medium:** "Import a story" from the live URL (https://medium.com/p/import), which sets the canonical link. No Mermaid or inline SVG, so check the PNGs came through.
- **Substack:** no canonical field. Add `Originally published at [alenabraham.me](https://alenabraham.me/posts/<slug>/).` as the first line, and schedule it for the same time the site post goes live.
- **Hashnode:** manual unless the publication is on Pro. Paste, then set "originally published at" to the live URL in the post settings.
- Opt a post out with `syndicate:` in front matter.

## Repurposing

From a finished post, see `references/repurposing.md`:

- A LinkedIn post, ≤1300 characters, one idea, link at the end.
- An X thread outline, 5 to 8 posts, first post states the problem.
