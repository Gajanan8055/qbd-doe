"""Shared settings and data models for the Production Kit pipeline."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# ── Settings ──────────────────────────────────────────────────────────────
MODEL = os.getenv("PIPELINE_MODEL", "claude-opus-4-8")
WEB_SEARCH = os.getenv("PIPELINE_WEB_SEARCH", "true").lower() == "true"
HOST = os.getenv("PIPELINE_HOST", "0.0.0.0")
PORT = int(os.getenv("PIPELINE_PORT", "8001"))
CORS = [o.strip() for o in os.getenv("PIPELINE_CORS", "*").split(",")]
OUTPUT_DIR = Path(os.getenv("PIPELINE_OUTPUT_DIR", "./output")).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YOUTUBE_CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS", "./client_secret.json")
YOUTUBE_TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", "./youtube_token.json")

PILLARS = {
    "1": "Money",
    "2": "Hypocrisy gap",
    "3": "Economics of faith",
    "4": "Why nothing happens",
}

Tier = Literal["T1", "T2", "T3", "T4"]
Wording = Literal["fact", "allegation"]


# ── Data models (mirror Production_Kit.md) ─────────────────────────────────
class Claim(BaseModel):
    claim: str = Field(description="The factual statement exactly as it will be said on screen.")
    tier: Tier = Field(description="Source tier: T1 court/affidavit, T2 official report, T3 two outlets, T4 single/social.")
    source: str = Field(description="Full citation plus link or document reference.")
    wording: Wording = Field(description="'fact' only if T1 court-found; otherwise 'allegation'.")


class ResearchResult(BaseModel):
    title: str = Field(description="Working title describing a mechanism, not a person.")
    pillar: str = Field(description="One of '1','2','3','4'.")
    mechanism: str = Field(description="The core mechanism this video explains, in one sentence.")
    claims: List[Claim] = Field(description="Every factual claim, each backed at T1–T3. Never include T4 as a claim.")
    docs: List[str] = Field(description="Specific on-screen documents (report page, judgment para, affidavit line).")
    denials: List[str] = Field(description="Subject responses / denials on record, if any.")
    legal_notes: str = Field(description="Short note confirming wording matches tiers and religion stays commercial/legal.")


class MechanismStep(BaseModel):
    step: str = Field(description="One step of how the machine works.")
    doc: str = Field(description="The on-screen document that proves this step.")


class ScriptResult(BaseModel):
    youtube_title: str = Field(description="A mechanism-focused YouTube title, not 'X EXPOSED'.")
    cold_artifact: str = Field(description="The one number or document line to open cold on (0:00–0:30).")
    promise: str = Field(description="What the viewer will understand by the end.")
    steps: List[MechanismStep] = Field(description="The 2–4 step mechanism walk-through (Act 2).")
    illustrative: str = Field(description="The T1-only illustrative case and which step it proves.")
    pattern_general: str = Field(description="The pattern stated generally (Act 3).")
    other_places: str = Field(description="1–2 other places the same mechanism shows up (T1–T3).")
    close: str = Field(description="Closing line — a call to notice, not to outrage.")
    narration: str = Field(description="The full spoken narration, plain prose, ~140–220 words, explanatory not angry.")
    description: str = Field(description="YouTube description including a sources list.")
    tags: List[str] = Field(description="8–15 relevant YouTube tags, mechanism/topic focused.")


# ── Validation: the Production Kit safety model ─────────────────────────────
def gate_research(r: ResearchResult) -> List[str]:
    """Return a list of blocking issues. Empty list => Part 1 is clean."""
    issues: List[str] = []
    if not r.title.strip():
        issues.append("Working title is empty.")
    if r.pillar not in PILLARS:
        issues.append(f"Pillar must be one of {list(PILLARS)}.")
    if not r.claims:
        issues.append("Claims ledger is empty.")
    for i, c in enumerate(r.claims, 1):
        if c.tier == "T4":
            issues.append(f"Claim {i} is T4 — T4 cannot enter the script (find a T1–T3 source instead).")
        if not c.source.strip():
            issues.append(f"Claim {i} has no source citation.")
        if c.tier != "T1" and c.wording == "fact":
            issues.append(f"Claim {i} is below T1 but worded as fact — must be an allegation.")
    return issues
