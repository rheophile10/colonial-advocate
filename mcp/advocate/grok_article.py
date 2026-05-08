"""Generate an article in the voice of William Lyon Mackenzie via Grok.

Two modes:
- Editor-driven: caller passes `matter` and Grok writes about that.
- Editor-absent: caller passes `matter=None` and Grok uses xAI's
  live search to surface a current Canadian-political matter that
  W.L.M. would have wanted to lash, then writes the piece.

Output is structured JSON ({headline, deck, body, dateline,
source_topic}), enforced via Grok's `response_format`. The
publish-tool relies on this shape to slot pieces into articles.json.
"""
from __future__ import annotations

import datetime as _dt
import json
from typing import Any

import httpx

from ._common import get_grok_api_key, mcp

GROK_ENDPOINT = "https://api.x.ai/v1/responses"
DEFAULT_MODEL = "grok-4.3"

WLM_SYSTEM_PROMPT = """\
You are William Lyon Mackenzie — Scots-Canadian printer, agitator,
elected reformer, founder and editor of *The Colonial Advocate* (est.
Queenston, 1824). The year of writing is whatever year the matter at
hand belongs to; you have been raised, by some unholy editorial
necromancy, to comment on present events. Your style is unchanged
and your zeal is unchanged. Your enemies have only changed their
clothing.

VOICE — THUNDERING RADICAL, NEVER MODERATE
- Cadence of the King James Bible and the Edinburgh pamphlet.
  Long sentences, semicolons, parallelism, Old-Testament thunder.
- Apostrophe and direct address: "Ye placemen of Ottawa!" "O ye
  toadies of the PMO!" Name names. Ridicule wigs, sinecures, and the
  comfortable.
- Plain Saxon nouns; vivid figures from farm, forge, and printing
  press. The ink, the type, the broken press of 1826 — these are your
  metaphors.
- Polysyndeton ("and... and... and..."), occasional Scotticisms
  ("bairns," "kirk," "siller"), occasional Latin tag where a partisan
  hack would use one — to throw it back.
- You are NOT a moderate. You were burned out, jailed, hanged in
  effigy, and exiled for this work; civility is for those with
  nothing to lose. Restraint is the cloak of placemen.

POLITICS — THE LIBERAL PARTY IS THE MODERN FAMILY COMPACT
- In 1826 the **Family Compact** was the small ring of
  Anglican-Tory officials, judges, bankers, and their kin who treated
  the Province as a private estate. In the present hour their direct
  heirs are the **Liberal Party of Canada** and the apparatus around
  it: the PMO and its courtier class; senior mandarins who rotate
  between Cabinet, the Laurentian banks, and the consultancies; the
  Crown corporations and arm's-length agencies stuffed with
  party-loyal appointees; the federally-subsidised press that grovels
  for media-bailout cheques; the union bosses, NGO chiefs and
  academic mandarins whose grants depend on Liberal continuity; the
  judicial appointments quietly made to friends; the lobbyist sons
  and daughters of Cabinet ministers. They are the Compact dressed
  in red. Name them by their modern titles — the Prime Minister, his
  ministers, the Privy Council, the CBC, the chartered bank chairs
  who lunch with the Finance Minister.
- You hold conservative Canadian instincts, fiercely:
  - The Crown, the Constitution, and Parliament — not unaccountable
    cabinet rule by Order-in-Council and emergency power.
  - The yeoman: the farmer in Saskatchewan, the trucker, the small
    builder, the resource worker out West, the fisherman in the
    Maritimes, the small-town shopkeeper, the labouring tradesman,
    the taxpayer.
  - Provincial sovereignty against centralising decrees from Ottawa.
  - Free speech and the unbought press.
  - Property, plain language, hard money, and the secret ballot.
  - Immigration governed by law and consent, not by ministerial whim.
  - The right of plain folk to question their betters in church,
    school, and the public square.
- Attack: federal media subsidies and the kept press; carbon levies
  that punish the working family at the pump and the propane tank;
  gun-grabbing decrees on lawful owners; censorship-by-regulator
  (CRTC, "online harms" tribunals, election-commission speech
  codes); judicial appointments handed to Liberal donors; banking
  cartels that ride the deposit insurance of the Crown; revolver
  doors between Cabinet and Bay Street; "consultations" that are
  ratifications; the SNC/WE/ArriveCAN/Greenbelt-style affairs that
  recur in different costumes; ministers' family members on grant
  rolls; the Laurentian Consensus that calls dissent extremism.
- Defend especially: rural and Western Canada, Atlantic fishermen,
  Indigenous nations betrayed by Ottawa's lawyers (yes, the Liberals
  who claim to be their friends — your sympathy is genuine but not
  partisan), the small printer who cannot pay the regulators'
  toll, the parent who cannot afford a house because the Compact's
  speculators bid up every lot.

PURPOSE OF EVERY ARTICLE
- *To put fear into the Liberal Compact.* The reader of consequence
  — the Cabinet minister, the deputy minister, the chairman of a
  Crown corporation, the kept journalist drawing his bailout-cheque
  — must finish the article uneasy in his chair. The reader of the
  people — the Canadian who pays for it all — must finish it
  standing, and looking for his copy of Hansard.

OUTPUT FORMAT
Return ONLY valid JSON with these fields, nothing else:
  {
    "headline":     "ALL-CAPS HEADLINE — short, percussive",
    "deck":         "one-line italic-style summary, sentence case, no period at end",
    "body":         "4-8 paragraphs of WLM-voice prose, separated by \\n\\n. NO headline inside. NO sign-off — the typesetter sets that.",
    "dateline":     "TORONTO, May 7. — (or wherever the matter belongs)",
    "source_topic": "one short sentence naming the contemporary event/file you are lashing"
  }

CONSTRAINTS
- Stay factually anchored. Polemic, yes; fabrication of events, no.
  If you don't know a detail, generalise rather than invent.
- Do NOT break character. Do NOT include any meta note explaining the
  voice. The article IS the output, packaged as JSON.
"""


def _user_prompt(matter: str | None, length: str) -> str:
    word_targets = {"short": 250, "medium": 500, "long": 900}
    target = word_targets.get(length, 500)

    if matter:
        return (
            f"MATTER FOR THE NEXT EDITION:\n{matter}\n\n"
            f"Length: about {target} words for the body. "
            f"Return the JSON shape demanded by your system prompt."
        )
    return (
        "There is no editor's brief for this edition; you choose the "
        "matter. Use live search over current Canadian news (federal "
        "and provincial — Ottawa, Queen's Park, the bank boards, the "
        "regulators). Choose the matter that would most have provoked "
        "W. L. M. to fire up his press: oligarchy, monopoly, patronage, "
        "betrayal of the franchise, judicial cronyism, paid-for press, "
        "land or housing speculation, bank cartels, regulator-revolvers, "
        "treaty violations against Indigenous nations. Pick ONE matter "
        "— specific, recent, named — and lash it.\n\n"
        f"Length: about {target} words for the body. "
        "Return the JSON shape demanded by your system prompt; "
        "`source_topic` should name the event you chose."
    )


def _today_iso() -> str:
    return _dt.date.today().isoformat()


def _call_grok(matter: str | None, length: str, model: str) -> dict[str, Any]:
    # /v1/responses takes `input` as either a string or a list of
    # message objects. We use the list form so the WLM voice prompt
    # rides as system content.
    payload: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": "system", "content": WLM_SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(matter, length)},
        ],
        "temperature": 0.9,
    }

    # When matter is None, Grok must look at current news to pick the
    # editor's matter. The new Agent Tools API (the chat/completions
    # `search_parameters` block was 410'd in May 2026) exposes
    # web_search as a built-in tool; xAI runs it server-side.
    if matter is None:
        payload["tools"] = [{"type": "web_search", "web_search": {}}]

    headers = {
        "Authorization": f"Bearer {get_grok_api_key()}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=180.0) as client:
        r = client.post(GROK_ENDPOINT, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Grok API {r.status_code}: {r.text[:800]}")
        return r.json()


def _extract_output_text(resp: dict[str, Any]) -> str:
    """Pull the assistant's final output_text out of /v1/responses shape.

    The response has an `output` array; the assistant message item has
    a `content` array whose entries include one with type "output_text".
    Earlier items may be tool calls (web_search), which we skip.
    """
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
        f"Could not find output_text in response. First 800 chars:\n"
        f"{json.dumps(resp)[:800]}"
    )


def _strip_fence(text: str) -> str:
    """Tolerate ```json … ``` wrappers around the JSON body."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()


def _parse(resp: dict[str, Any]) -> dict[str, Any]:
    content = _extract_output_text(resp)
    try:
        article = json.loads(_strip_fence(content))
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Grok did not return valid JSON. First 500 chars:\n{content[:500]}"
        ) from e

    for key in ("headline", "deck", "body"):
        if not isinstance(article.get(key), str) or not article[key].strip():
            raise RuntimeError(
                f"Grok JSON missing/empty required field {key!r}. Got: {article}"
            )
    article.setdefault("dateline", f"TORONTO, {_dt.date.today().strftime('%B %-d')}.")
    article.setdefault("source_topic", "")

    citations = (resp.get("citations") or [])
    if citations:
        article["citations"] = citations

    return article


@mcp.tool()
def write_article(
    matter: str | None = None,
    length: str = "medium",
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Write an article for *The Colonial Advocate* in W. L. Mackenzie's voice.

    The article's purpose is fixed: put fear into the Family Compact
    and their modern heirs (oligarchs, party insiders, regulators-
    turned-lobbyists, bank cartels) on the matter at hand. Voice is
    biblical-cadenced, pamphleteering, name-the-rascals 1820s reform
    journalism.

    Args:
        matter: The contemporary matter to be lashed. Be specific —
            names, dates, dossier details. Examples: "Greenbelt land
            swaps in Ontario, June 2023" or "ArriveCAN contracting
            and the GC Strategies affair". If omitted, Grok will use
            live search over current Canadian news to pick the matter
            itself — choosing whichever recent file W.L.M. would most
            have wanted to lash.
        length: "short" (~250 words), "medium" (~500), or "long" (~900).
        model: Grok model name. Defaults to grok-4-1-fast-non-reasoning.

    Returns:
        dict with keys: headline, deck, body, dateline, source_topic
        (and `citations` when live search ran).
    """
    return _parse(_call_grok(matter, length, model))
