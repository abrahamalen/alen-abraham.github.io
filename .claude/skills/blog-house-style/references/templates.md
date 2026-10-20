# Post templates

Delete the guidance lines as you fill them in. Headings are suggestions; rename them to say what the section is about.

## Technical post

```markdown
---
title: "<What broke or what I built, specifically>"
date: YYYY-MM-DDT09:00:00+05:30
description: "<One sentence, ≤160 chars: the problem and what the reader gets.>"
tags: ["<tag>", "<tag>", "<tag>"]
categories: ["devops"]
ShowToc: true
---

<Two or three sentences. What happened, when, and why it mattered. No definitions yet.>

## The problem

<The symptom as I saw it: the error message, the failing command, the graph. Paste the real output in a code block.>

## Context

<Only what the reader needs to follow along: the setup, versions, the constraint. A small example or a diagram goes here.>

## What I tried

<What I checked first and what it ruled out. Short. Wrong turns are fine if they teach something.>

## The fix

<The commands or config, in order, copy-pasteable. Say what each one does in a sentence when it isn't obvious.>

## Numbers

<Before and after: time, size, cost, error rate. Skip this section if there are no real numbers. Never make one up.>

## Lessons

- <Something specific I'll do differently.>
- <A check or habit that would have caught it earlier.>

<One or two lines to wrap up.>

Thank you for the read.
```

## Narrative or travel post

```markdown
---
title: "<Place or moment, plainly>"
date: YYYY-MM-DDT09:00:00+05:30
description: "<≤160 chars: where, when, what it was like.>"
tags: ["travel"]
categories: ["<category>"]
cover:
  image: "/images/posts/<slug>/cover-image.jpg"
  alt: "<What's in the photo>"
  caption: "<Credit>"
  relative: false
---

<Open in the scene: a time, a place, one thing I saw or heard. No "I had the incredible opportunity".>

## <Section named after a place or moment>

<One concrete detail per section: a price, a name of a street, what the food tasted like, how long the bus took. Prose, not bullet points.>

## <Next place or moment>

<Same. If there are photos, one or two per section with real captions.>

## <What I'd tell someone going>

<Practical, in prose: when to go, what to book ahead, what I'd skip.>

Thank you for the read.
```
