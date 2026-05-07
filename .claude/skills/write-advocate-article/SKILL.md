---
name: write-advocate-article
description: Generate and publish an article for The Colonial Advocate in William Lyon Mackenzie's voice — Grok picks the matter from current Canadian news (or the user supplies one), writes in WLM's biblical-cadenced pamphleteer voice, and the result is appended to the SPA's articles.json. Invoke when the user asks for "an Advocate article", "a Mackenzie piece", "a column", "publish a new edition", or any front-page polemic for this site.
---

# Write & publish for *The Colonial Advocate*

This skill drafts a polemical article in William Lyon Mackenzie's voice
via the `colonial-advocate` MCP server. The article's editorial purpose
is fixed: **put fear into the Family Compact and their modern heirs.**

## Two tools, two purposes

The `colonial-advocate` MCP exposes:

- **`write_article`** — generates the article, returns JSON
  `{headline, deck, body, dateline, source_topic, citations?}`.
  Does NOT touch the site. Use when the user wants to read or edit
  the piece before it goes to press.
- **`publish_article`** — calls `write_article` internally then
  appends the result to `web/public/articles.json` (the SPA's data
  source). Use when the user wants a new edition on the site.

Default to **`publish_article`** unless the user explicitly wants a
preview-only draft.

## When to invoke

- "Publish a new Advocate article" → `publish_article()` (no args, Grok picks)
- "Write me a piece on X" → `publish_article(matter="X")`
- "Draft something but don't publish it yet" → `write_article(...)`
- "Show me what Grok would write about today" → `write_article()`

## Arguments

- `matter` — optional. Leave **omitted** to let Grok use live news
  search and pick whatever current Canadian-political matter would
  most have provoked W.L.M. (this is the preferred mode and the one
  the user has explicitly asked for as default). Pass a string to
  force a specific topic.
- `length` — `"short"` (~250 w), `"medium"` (~500 w, default),
  `"long"` (~900 w).
- `slug` (publish_article only) — override the auto-generated URL slug.

## After publishing

The MCP returns `next_steps` with the exact rebuild & push commands.
Run them so the new edition deploys:

```sh
cd web && npm run build
cd .. && git add docs web/public/articles.json
git commit -m 'Publish: <headline>'
git push
```

Pages picks it up automatically; live in ~60 s.

## Voice fidelity

The system prompt fixes the voice. Do **not** edit the body for tone,
hedge it, or soften it. If the user asks for changes, re-run with a
sharper `matter` rather than post-editing.
