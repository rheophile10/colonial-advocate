"""Publish a generated article into the SPA's articles.json.

`web/public/articles.json` is the source of truth for what the front
page renders. The MCP is the only writer. After publishing, the user
runs `cd web && npm run build && git push` to deploy.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any

from ._common import PROJECT_ROOT, mcp
from .grok_article import write_article

ARTICLES_PATH = PROJECT_ROOT / "web" / "public" / "articles.json"


def _slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text)
    ascii_ = norm.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_).strip("-")
    return slug[:80] or "article"


def _load() -> list[dict[str, Any]]:
    if not ARTICLES_PATH.exists():
        return []
    raw = ARTICLES_PATH.read_text()
    if not raw.strip():
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise RuntimeError(
            f"{ARTICLES_PATH} is not a JSON array; got {type(data).__name__}"
        )
    return data


def _save(articles: list[dict[str, Any]]) -> None:
    ARTICLES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTICLES_PATH.write_text(
        json.dumps(articles, indent=2, ensure_ascii=False) + "\n"
    )


def _ensure_unique_slug(base: str, existing: list[dict[str, Any]]) -> str:
    used = {a.get("slug") for a in existing}
    if base not in used:
        return base
    n = 2
    while f"{base}-{n}" in used:
        n += 1
    return f"{base}-{n}"


@mcp.tool()
def publish_article(
    matter: str | None = None,
    length: str = "medium",
    slug: str | None = None,
) -> dict[str, Any]:
    """Generate an article and append it to web/public/articles.json.

    The front page reads articles.json at runtime; after publishing,
    rebuild and push to deploy:

        cd web && npm run build
        git add ../docs ../web/public/articles.json
        git commit -m "Publish: <headline>"
        git push

    Args:
        matter: Editor's brief. If omitted, Grok uses live news search
            to pick the matter itself (preferred — lets the editor's
            ghost wander the wires for what would have lit him up).
        length: "short" | "medium" | "long".
        slug: Override the auto-generated URL slug. Default derives
            from the headline.

    Returns:
        The article entry that was appended (with id, slug, and
        published_at fields filled in), plus `articles_path` and a
        `next_steps` hint.
    """
    article = write_article(matter=matter, length=length)

    articles = _load()
    base_slug = _slugify(slug or article["headline"])
    final_slug = _ensure_unique_slug(base_slug, articles)

    entry = {
        "id": str(uuid.uuid4()),
        "slug": final_slug,
        "headline": article["headline"],
        "deck": article.get("deck", ""),
        "body": article["body"],
        "dateline": article.get("dateline", ""),
        "source_topic": article.get("source_topic", ""),
        "byline": "W. L. M.",
        "published_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }
    if article.get("citations"):
        entry["citations"] = article["citations"]

    # Newest first — the front page reads in array order.
    articles.insert(0, entry)
    _save(articles)

    return {
        "article": entry,
        "articles_path": str(ARTICLES_PATH),
        "total_articles": len(articles),
        "next_steps": (
            "Rebuild the SPA and push: "
            "`cd web && npm run build && cd .. && "
            "git add docs web/public/articles.json && "
            f"git commit -m 'Publish: {entry['headline']}' && git push`"
        ),
    }
