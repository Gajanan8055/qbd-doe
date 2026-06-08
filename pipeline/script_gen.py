"""Stage 2 of the pipeline: Research / Defence File -> Script + title + metadata.

Generated FROM Part 1. Structure: Number -> Mechanism -> "See it everywhere."
Open cold on one document or figure; never on a thesis. Every wrongdoing
statement matches its tier wording from the defence file.
"""
from __future__ import annotations

import anthropic

from config import MODEL, ResearchResult, ScriptResult

_client = anthropic.Anthropic()

SCRIPT_SYSTEM = """You write scripts for a systems-focus explainer channel, strictly FROM a pre-built defence file.

Structure: Number -> Mechanism -> "See it everywhere."
- ACT 1 cold open (0:00-0:30): open on ONE specific number or one line from a document. No intro, no
  "namaskar dosto", no channel throat-clearing.
- ACT 2 mechanism: explain how the machine works step by step; the adjudicated case is the ILLUSTRATION,
  not the subject. Each step names the on-screen document that proves it.
- ACT 3 "now you'll see it everywhere": generalise from the one case to the pattern; close with a call to
  NOTICE, not to outrage.

Tone guardrails:
- Explanatory, not angry. Show the machine, don't prosecute a man.
- Every wrongdoing statement matches its tier wording (fact only at T1; otherwise allegation).
- No adjectives doing the work facts should do ("brazen", "shameless" -> cut; let the number land).
- Title and thumbnail describe a MECHANISM, not a person ("How procurement money vanishes", not "X EXPOSED").
- Use only claims present in the defence file. Do not invent facts or sources."""


def generate_script(r: ResearchResult) -> ScriptResult:
    claims = "\n".join(
        f"- [{c.tier}] ({c.wording}) {c.claim}  — source: {c.source}" for c in r.claims
    )
    docs = "\n".join(f"- {d}" for d in r.docs) or "(none listed)"
    denials = "\n".join(f"- {d}" for d in r.denials) or "(none on record)"

    user = (
        f"DEFENCE FILE\n"
        f"Title: {r.title}\nPillar: {r.pillar}\nMechanism: {r.mechanism}\n\n"
        f"Claims ledger:\n{claims}\n\n"
        f"On-screen documents:\n{docs}\n\n"
        f"Denials on record:\n{denials}\n\n"
        "Write the script and YouTube metadata strictly from this file. The narration must be plain spoken "
        "prose (~140-220 words) suitable for text-to-speech, explanatory in tone. Include a sources list in "
        "the description."
    )

    resp = _client.messages.parse(
        model=MODEL,
        max_tokens=6000,
        system=SCRIPT_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_format=ScriptResult,
    )
    return resp.parsed_output
