"""Stage 1 of the pipeline: topic -> Research / Defence File (Part 1).

Two-stage Claude pipeline:
  1. Gather: Claude searches the web (server-side web_search tool) for real
     sources, honoring the T1-T4 source-tier rubric.
  2. Structure: the gathered findings are parsed into a typed ResearchResult.

Server-side web search uses citations, which are incompatible with structured
outputs in a single call, so the two stages are deliberately separate.
"""
from __future__ import annotations

import anthropic

from config import MODEL, WEB_SEARCH, PILLARS, ResearchResult

_client = anthropic.Anthropic()

RUBRIC = """SOURCE-TIER RUBRIC (never violate):
- T1: court judgment/order, sworn affidavit, filed chargesheet. Strongest; may be stated as fact WITH attribution.
- T2: official institutional report (CAG, parliamentary committee, ECI filing, gazette, RTI reply). Strong.
- T3: two independent mainstream outlets reporting the same fact. Usable, framed "as reported by...".
- T4: single outlet, blog, social post, "people say". NOT usable as a claim — only to FIND a T1-T3 source.

HARD GATES:
- A person's wrongdoing may be stated as fact ONLY at T1 (convicted/charged/court-found). Otherwise it is an
  allegation and must be worded as one.
- Always include the subject's denial/response if one exists on record.
- Religion content stays commercial/legal (business model, trust structure, tax, land, convicted conduct).
  Never doctrinal, never the faith itself.
- If a claim cannot reach T1-T3, it does not enter the script. No exceptions."""

GATHER_SYSTEM = f"""You are the research desk for a systems-focus explainer channel. You build a defence file
BEFORE any script exists — this is the node that keeps the channel out of court.

{RUBRIC}

Given a topic, find concrete, verifiable facts and their strongest available sources. Prefer official filings
and judgments. For every factual statement, note the exact source and its tier. Surface any on-record denial.
Explain the underlying MECHANISM (how the money/process actually works), using a specific adjudicated case only
as an illustration. Be explanatory, not accusatory."""

STRUCT_SYSTEM = f"""You convert research notes into a structured Production-Kit defence file.

{RUBRIC}

Rules for the structured output:
- pillar is one of: {", ".join(f'{k}={v}' for k, v in PILLARS.items())}.
- Every claim must sit at T1, T2, or T3. NEVER emit a T4 claim.
- wording is "fact" only when tier is T1; otherwise "allegation".
- title and any titles must describe a mechanism, not attack a person.
- Include real source citations carried over from the notes."""


def _gather(topic: str, pillar: str | None) -> str:
    """Stage 1: collect sourced findings (optionally via web search)."""
    pillar_hint = f"\nIntended pillar: {pillar} ({PILLARS.get(pillar, '')})." if pillar else ""
    user = (
        f"Topic idea: {topic}{pillar_hint}\n\n"
        "Produce a research brief: the core mechanism, then a numbered list of factual claims, each with its "
        "source and tier (T1-T3 only as usable claims), the specific on-screen documents to show, and any "
        "denials on record."
    )
    tools = [{"type": "web_search_20260209", "name": "web_search"}] if WEB_SEARCH else []

    messages = [{"role": "user", "content": user}]
    # Server-side tool loop: resume on pause_turn until the model is done.
    for _ in range(6):
        resp = _client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=GATHER_SYSTEM,
            thinking={"type": "adaptive"},
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        return "".join(b.text for b in resp.content if b.type == "text")
    return "".join(b.text for b in resp.content if b.type == "text")


def _structure(topic: str, notes: str) -> ResearchResult:
    """Stage 2: turn the notes into a typed, validated defence file."""
    resp = _client.messages.parse(
        model=MODEL,
        max_tokens=6000,
        system=STRUCT_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Topic: {topic}\n\nResearch notes:\n{notes}\n\n"
                       "Structure this into the Production-Kit defence file. Drop any T4-only claim.",
        }],
        output_format=ResearchResult,
    )
    return resp.parsed_output


def research(topic: str, pillar: str | None = None) -> ResearchResult:
    notes = _gather(topic, pillar)
    return _structure(topic, notes)
