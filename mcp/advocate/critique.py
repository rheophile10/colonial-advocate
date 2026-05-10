"""Critique a Colonial Advocate draft for WLM fidelity AND factual accuracy.

One Grok call does both jobs:
  - Part I: identify every factual claim and verify via live web search.
  - Part II: score the prose for fidelity to William Lyon Mackenzie's
    actual register, paragraph by paragraph, with proposed alternatives.

Returns structured JSON the caller can route to revise/publish steps.
"""
from __future__ import annotations

import datetime as _dt
import json
from typing import Any

import httpx

from ._common import get_grok_api_key, mcp

GROK_ENDPOINT = "https://api.x.ai/v1/responses"
DEFAULT_MODEL = "grok-4.3"

WLM_FIDELITY_RUBRIC = """\
The bar for fidelity is HIGH: would a reader of the 1824–1834
Colonial Advocate, handed this column unsigned, mistake it for
Mackenzie's hand?

Authentic WLM is:
- BIBLICAL & PSALMIC IN CADENCE. Sentences modeled on the King James
  Old Testament: parallelism, polysyndeton, prophetic invective.
  "Wo unto them that...!" "Behold...!" "Hear, O ye people!"
- CATALOGUE-DRIVEN. He piles indictments in long lists separated
  by semicolons or dashes, often anaphoric. Modern op-ed structure
  (claim → concession → rebuttal → conclusion) is foreign to him.
- NAMES NAMES, RELENTLESSLY. Hagerman, Robinson, Strachan, the
  Boultons, the Sherwoods, the Powells. He pinned the Compact to
  the page by name and family connexion. Abstractions like "the
  Ministry," "Ottawa," "the centre" are NOT his style.
- USES "YE / THEE / THOU" in direct address: "Repent, ye placemen!"
- SCOTTICISMS THROUGHOUT, as native vocabulary, not garnish:
  bairn, kirk, siller, auld, braw, canny, wha, ower.
- INVECTIVE-RICH PHYSICAL METAPHORS. Leeches, vampires, locusts,
  toads, vipers, harlots, the bottomless purse, the swarming hive,
  the broken press, the gallows, the chain.
- DIGRESSIVE. He drops in historical analogies (Cromwell, Hampden,
  the Stuarts, Wallace and Bruce, the American Revolution) to frame
  the present matter.
- SHORT BARK SENTENCES interspersed with long thunderous ones.

Things that BETRAY a 21st-century writer in costume:
- Op-ed concession structure ("Now, this Printer wishes to be fair...").
- Bureaucratic nouns: statecraft, framework, prescription, dispute,
  strategy, register, dynamic, calculations.
- Therapy/clinical metaphors (suppurating wound, body politic
  contracts a fever) — these are 20th-century editorial clichés.
- Hedging language: "roughly," "approximately," "in many particulars,"
  "with something approaching."
- Smooth transitional phrases: "And what of Quebec?", "There is, to
  be precise about it,", "on the one hand … on the other hand."
- Capitalised abstractions: "Performance of Progress," "Architecture
  of Progress."
- Modern budget figures or polling fractions presented as analysis
  ("ninety billions," "twenty-seven per cent of voters") — WLM
  named ringleaders and sums of public theft, not survey results.
- Abstract personification of "the Ministry" rather than naming the
  individual placeman.

VERDICT LADDER for each paragraph:
- WLM             — would pass an 1830s reader unsigned.
- NEAR-WLM        — clearly intended, but one or two betrayals.
- MODERN-IN-COSTUME — modern essayist using archaic vocabulary.

SCORE LADDER (0–10):
- 0–3 — recognisable as a modern op-ed in costume.
- 4–5 — credible pastiche; intent reads, but the bones are modern.
- 6–7 — careful 1830s reader would notice but might forgive.
- 8–9 — careful 1830s reader would buy it.
- 10  — indistinguishable from a real 1834 column.
"""

CRITIQUE_SYSTEM_PROMPT = f"""\
You are a senior editor for *The Colonial Advocate*, a pamphlet
published in the spirit of William Lyon Mackenzie (1795–1861, founder
of the original Advocate at Queenston, 1824). Your job has TWO parts.

PART I — FACT-CHECK
Identify every factual claim in the draft: named persons and titles;
dates and timelines; numbers (signature counts, dollar figures, poll
percentages, vote thresholds); quoted statements and their attributions;
organisational facts ("X organised the petition," "Y is the leader of
Z"); claims about meetings, deadlines, votes, court rulings.

For each claim, use web search to verify against current authoritative
sources (CBC, Globe & Mail, Reuters, Elections Alberta / Élections
Québec, Hansard, official press releases, established polling firms).
For each claim report:
  - claim:           the exact factual assertion (paraphrased ok)
  - status:          one of "verified" | "disputed" | "false" | "unverifiable"
  - evidence:        what your source(s) showed
  - source:          URL or short citation; null if unverifiable
  - suggested_fix:   null when verified; otherwise a corrected
                     sentence the editor can drop in

Allow rounding for quantities ("more than 300,000" is fine if the
verified figure is 301,620; "$130 / tonne" is fine if the actual
figure is $130 / tonne). Flag a claim as "disputed" only when newer
or better sources contradict it; "false" only when no credible
source supports it.

PART II — W. L. MACKENZIE FIDELITY
{WLM_FIDELITY_RUBRIC}

Grade EVERY paragraph in the body. The body is split into paragraphs
on blank-line boundaries. Count them; your `paragraphs` array MUST
have exactly that many entries, in order, 1-indexed, none skipped —
even paragraphs that land cleanly as WLM. For each paragraph report:
  - index, opening_words (first 6–8 words for locating)
  - verdict: WLM | NEAR-WLM | MODERN-IN-COSTUME
  - weakest_line: the line that most betrays the modern hand
                  (verbatim, or null if WLM verdict)
  - betrayal:     what specifically betrays it (or null)
  - alternative:  full WLM-voice replacement paragraph, preserving
                  ALL factual claims (or null if WLM verdict)

Then list:
  - modern_phrases: phrases NEVER found in authentic WLM
  - leverage_edits: the THREE single edits with the highest impact
                    (each: current line, replacement, reason)
  - score:          0–10 fidelity score per the ladder above
  - rationale:      one or two sentences

PART III — SUMMARY
Two or three sentences: the dominant pattern of strengths and the
dominant pattern of weaknesses, in plain editorial English.

OUTPUT FORMAT
Return ONLY valid JSON with this exact shape, nothing else:

{{
  "facts": [
    {{
      "claim": "...",
      "status": "verified" | "disputed" | "false" | "unverifiable",
      "evidence": "...",
      "source": "..." | null,
      "suggested_fix": "..." | null
    }}
  ],
  "fidelity": {{
    "score": <int 0–10>,
    "rationale": "...",
    "paragraphs": [
      {{
        "index": <int>,
        "opening_words": "...",
        "verdict": "WLM" | "NEAR-WLM" | "MODERN-IN-COSTUME",
        "weakest_line": "..." | null,
        "betrayal": "..." | null,
        "alternative": "..." | null
      }}
    ],
    "modern_phrases": ["...", "..."],
    "leverage_edits": [
      {{"current": "...", "replacement": "...", "reason": "..."}}
    ]
  }},
  "summary": "..."
}}

CONSTRAINTS
- Stay critical. Do not flatter the draft.
- Do not propose factual changes — only flag and suggest fixes.
- Preserve every factual claim inside paragraph alternatives.
- Do not break character with meta commentary outside the JSON.
"""


def _user_prompt(headline: str, deck: str, body: str) -> str:
    return (
        f"DRAFT TO CRITIQUE:\n\n"
        f"HEADLINE: {headline}\n\n"
        f"DECK: {deck}\n\n"
        f"BODY:\n\n{body}\n\n"
        f"Return the JSON shape demanded by your system prompt."
    )


def _call_grok(
    headline: str,
    deck: str,
    body: str,
    fact_check: bool,
    model: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": "system", "content": CRITIQUE_SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(headline, deck, body)},
        ],
        "temperature": 0.3,
    }
    if fact_check:
        payload["tools"] = [{"type": "web_search", "web_search": {}}]

    headers = {
        "Authorization": f"Bearer {get_grok_api_key()}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=300.0) as client:
        r = client.post(GROK_ENDPOINT, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Grok API {r.status_code}: {r.text[:800]}")
        return r.json()


def _extract_output_text(resp: dict[str, Any]) -> str:
    for item in resp.get("output", []):
        if item.get("role") == "assistant" or item.get("type") == "message":
            for piece in item.get("content", []):
                if piece.get("type") in ("output_text", "text"):
                    text = piece.get("text")
                    if isinstance(text, str) and text.strip():
                        return text
    if isinstance(resp.get("output_text"), str):
        return resp["output_text"]
    raise RuntimeError(
        f"Could not find output_text in critique response. First 800 chars:\n"
        f"{json.dumps(resp)[:800]}"
    )


def _strip_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def _parse(resp: dict[str, Any]) -> dict[str, Any]:
    raw = _extract_output_text(resp)
    try:
        critique = json.loads(_strip_fence(raw))
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Grok did not return valid JSON. First 500 chars:\n{raw[:500]}"
        ) from e

    fidelity = critique.get("fidelity")
    if not isinstance(fidelity, dict):
        raise RuntimeError("critique JSON missing 'fidelity' object")
    if not isinstance(fidelity.get("score"), int):
        raise RuntimeError("critique JSON missing integer 'fidelity.score'")
    if not isinstance(critique.get("facts"), list):
        raise RuntimeError("critique JSON missing 'facts' list")

    citations = resp.get("citations") or []
    if citations:
        critique["citations"] = citations

    critique.setdefault(
        "checked_at",
        _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    )
    return critique


@mcp.tool()
def critique_article(
    headline: str,
    deck: str,
    body: str,
    fact_check: bool = True,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Critique a draft for W. L. Mackenzie fidelity AND factual accuracy.

    One Grok call returns:
      - per-paragraph verdicts (WLM / NEAR-WLM / MODERN-IN-COSTUME)
        with weakest lines, what betrays them, and full WLM-voice
        replacement paragraphs;
      - the three highest-leverage single edits;
      - a fidelity score on a 0–10 ladder (see rubric);
      - a fact-check entry per identifiable claim, each with status,
        evidence, source, and a suggested fix when wrong;
      - a 2–3-sentence editorial summary.

    Args:
        headline: Article headline (ALL-CAPS expected, but not enforced).
        deck:     One-line italic-style summary.
        body:     Full prose body. Paragraphs separated by blank lines.
        fact_check: When True (default), Grok runs live web search to
            verify factual claims. Set False for a fast prose-only
            pass during iterative revision.
        model:    Grok model name. Defaults to the same model used by
            write_article.

    Returns:
        dict with keys: facts, fidelity, summary (and `citations` and
        `checked_at` when applicable).
    """
    return _parse(_call_grok(headline, deck, body, fact_check, model))
