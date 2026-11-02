"""Structured outputs exchanged between the agents.

Fields have no defaults on purpose: strict JSON schemas (which Gemini and Claude both
follow) work best when every field is required, with "" or [] standing for "nothing".
"""

from typing import Literal

from pydantic import BaseModel

Intent = Literal["catch", "next_steps", "plan", "lookup", "revision"]
ResearcherKind = Literal["battle", "catch", "moves", "story"]


# --- Clarifier -------------------------------------------------------------------------------


class PartyEntry(BaseModel):
    species: str
    level: int
    moves: list[str]


class StateUpdate(BaseModel):
    """Run-state facts the player stated in this message; null means "not mentioned"."""

    starter: Literal["treecko", "torchic", "mudkip"] | None
    badges: list[str] | None
    rival: Literal["may", "brendan"] | None
    last_battle: str | None
    party: list[PartyEntry] | None


class RuleUpdate(BaseModel):
    """Rules the player added in this message; null/[] means "not mentioned"."""

    nuzlocke: bool | None
    dupes_clause: bool | None
    level_caps: bool | None
    monotype: str | None
    no_legendaries: bool | None
    wild_only: bool | None
    add_banned_species: list[str]
    add_used_routes: list[str]
    add_notes: list[str]


class ClarifierDecision(BaseModel):
    action: Literal["proceed", "ask", "decline"]
    intent: Intent
    reply: str
    research_brief: str
    state_updates: StateUpdate
    rule_updates: RuleUpdate
    reject_species: list[str]
    revision_feedback: str


# --- Researchers -----------------------------------------------------------------------------


class Claim(BaseModel):
    text: str
    source_ids: list[str]


class Candidate(BaseModel):
    species: str
    where: str
    when: str
    why: str
    long_term: str
    source_ids: list[str]


class Finding(BaseModel):
    summary: str
    claims: list[Claim]
    candidates: list[Candidate]
    open_questions: list[str]


class ResearchTask(BaseModel):
    researcher: ResearcherKind
    task: str


# --- Lead ------------------------------------------------------------------------------------


class Alternative(BaseModel):
    species: str
    where: str
    why: str
    source_ids: list[str]


class Recommendation(BaseModel):
    species: str
    role: str
    horizon: Literal["core", "situational"]  # a keeper through the Champion, or an answer to one fight
    where: str
    when: str
    why: str
    long_term: str
    source_ids: list[str]
    alternatives: list[Alternative]


class Step(BaseModel):
    title: str
    detail: str
    source_ids: list[str]


class BattleNote(BaseModel):
    battle_id: str
    note: str
    source_ids: list[str]


class LeadDraft(BaseModel):
    intent: Intent
    headline: str
    recommendations: list[Recommendation]
    steps: list[Step]
    battle_notes: list[BattleNote]
    assumptions: list[str]
    follow_up_questions: list[str]
    unresolved: list[str]
