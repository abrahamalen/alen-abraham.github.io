# Analytics Setup

This website uses [Plausible Analytics](https://plausible.io) for privacy-friendly visitor statistics.

## Features

- **Privacy-focused**: No cookies, GDPR compliant
- **Lightweight**: Tiny script (~1KB)
- **Open source**: Transparent and trustworthy
- **Simple metrics**: Only tracks what's necessary

## Implementation

The Plausible script is added to the site via the `layouts/partials/extend_head.html` file:

```html
<!-- Plausible Analytics - Privacy-friendly analytics -->
<script defer data-domain="alenabraham.me" src="https://plausible.io/js/script.js"></script>
```

## Dashboard Access

To access the analytics dashboard:

1. Go to [https://plausible.io/alenabraham.me](https://plausible.io/alenabraham.me)
2. Log in with your Plausible credentials

## Custom Events

If you want to track specific events (like button clicks or form submissions), you can add custom event tracking:

```javascript
// Example: Track a custom event
plausible('Download', {props: {method: 'Direct'}});
```

## Exclusions

Analytics tracking is applied to all pages by default. If you need to exclude certain pages or sections, you can use Hugo's conditional templates:

```html
{{- if not .Params.excludeAnalytics -}}
<script defer data-domain="alenabraham.me" src="https://plausible.io/js/script.js"></script>
{{- end -}}
```

Then in your content front matter, you can add:

```yaml
---
title: "Privacy Policy"
excludeAnalytics: true
---
``` 