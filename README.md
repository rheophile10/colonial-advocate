# The Colonial Advocate

A single-page web app modelled after William Lyon Mackenzie's newspaper of the same name.
The site is built with [plastron](https://github.com/rheophile10/plastron); a sibling Python
MCP generates articles in Mackenzie's tone via Grok.

## Layout

```
colonial/
├── web/        # Vite + plastron SPA (the front page)
├── mcp/        # Python MCP — Grok article generation in WLM's tone
├── images/     # Source illustrations (The Chase, etc.)
└── .vscode/    # launch configs for the dev server and the MCP
```

## Web — local dev

```sh
cd web
npm install
npm run dev      # → http://localhost:5173
```

`web/` imports plastron and `plastron-dom` directly from `../../plastron` on disk
(not via npm), so the `plastron` repo must be checked out as a sibling of this one.

## MCP — local dev

The MCP reads `GROK_API_KEY` from `../ccfr-site/.env` (or from the environment, if set).

```sh
cd mcp
uv run python server.py
```

## Secrets

`.env` files are git-ignored. The Grok key lives in `../ccfr-site/.env` for now;
move it to `mcp/.env` if you want this project self-contained.
