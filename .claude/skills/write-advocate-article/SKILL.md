---
name: write-advocate-article
description: Generate an article for The Colonial Advocate in William Lyon Mackenzie's voice on a contemporary Canadian political matter. Calls the colonial-advocate MCP server's write_article tool, which prompts Grok with a fixed WLM system prompt (biblical-cadenced pamphleteer voice, Family-Compact-as-villain framing). Invoke when the user asks for "an Advocate article", "a Mackenzie piece", "a column for the paper", or wants to draft any front-page polemic for this site.
---

# Write an article for *The Colonial Advocate*

This skill drafts a polemical article in William Lyon Mackenzie's voice
via the `colonial-advocate` MCP server. The article's editorial purpose
is fixed: **put fear into the Family Compact and their modern heirs.**

## When to invoke

- "Write me an Advocate article on X"
- "Draft a Mackenzie-style piece about Y"
- "Give me a front-page column on Z for the paper"
- Any request to produce content for the colonial-advocate site

## How to invoke

Call the MCP tool `colonial-advocate__write_article` (i.e. the
`write_article` tool exposed by the `colonial-advocate` server in
`.mcp.json`). Arguments:

- `matter` (required) — the contemporary matter to be lashed. Be
  specific: include names, dates, dossier details. Vague matters get
  vague polemic.
- `length` — `"short"` (~250 w), `"medium"` (~500 w, default), or
  `"long"` (~900 w).
- `model` — Grok model name; leave default unless the user asks.

## Before invoking

If the user gives only a topic ("write something about housing"), ask
one clarifying question to pin the dossier — *which* policy, *which*
minister, *which* deal — so the polemic has a target. WLM does not
write about themes; he writes about people and their crimes.

## After invoking

Paste the article verbatim. Do **not** edit it for tone, hedge it, or
soften it — this is its purpose. If the user asks for changes, pass
them as a new `matter` ("rewrite focusing on ...") rather than
post-editing.

## Where the article goes

Output is text only (headline + deck + body + `— W. L. M.` sigil).
Setting it into the SPA is a separate step — the site currently shows
only the coming-soon front page.
