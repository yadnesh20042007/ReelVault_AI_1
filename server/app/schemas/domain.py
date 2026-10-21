from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Category(str, Enum):
    internship = "internship"
    hackathon = "hackathon"
    competition = "competition"
    course = "course"
    scholarship = "scholarship"
    government_scheme = "government_scheme"
    job = "job"
    event = "event"
    other = "other"


class Verdict(str, Enum):
    OFFICIAL_CONFIRMED = "official_confirmed"
    FOUND_UNOFFICIAL = "found_unofficial"
    CONFLICTING = "conflicting"
    NOT_FOUND = "not_found"
    SUSPICIOUS = "suspicious"


class PostRef(BaseModel):
    platform: Literal["instagram", "youtube", "tiktok"]
    shortcode: str
    canonical_url: str


class FetchedPost(BaseModel):
    platform: Literal["instagram", "youtube", "tiktok"]
    shortcode: str
    url: str | None = None
    transcript: str | None = None
    caption: str | None = None
    author: str | None = None
    posted_at: datetime | None = None
    language_hint: str | None = None
    raw: dict = Field(default_factory=dict)


class Classification(BaseModel):
    is_opportunity: bool
    category: Category
    reason: str


class EvStr(BaseModel):
    value: str | None = None
    quote: str | None = None


class EvDate(BaseModel):
    value: date | None = None
    quote: str | None = None


class Extracted(BaseModel):
    title: EvStr = Field(default_factory=EvStr)
    organizer: EvStr = Field(default_factory=EvStr)
    deadline_raw: EvStr = Field(default_factory=EvStr)
    deadline: EvDate = Field(default_factory=EvDate)
    deadline_ambiguous: bool = False
    eligibility: EvStr = Field(default_factory=EvStr)
    reward: EvStr = Field(default_factory=EvStr)
    mode: EvStr = Field(default_factory=EvStr)
    location: EvStr = Field(default_factory=EvStr)
    links: list[EvStr] = Field(default_factory=list)


class FieldCheck(BaseModel):
    field: str
    status: Literal["matched", "mismatch", "unverified"]
    official_value: str | None = None


class ClaimCheck(BaseModel):
    claim: str
    status: Literal["verified", "unverified", "false", "misleading"]
    evidence: str | None = None
    source_url: str | None = None


class VerdictDraft(BaseModel):
    verdict: Verdict
    official_urls: list[str] = Field(default_factory=list)
    supporting_urls: list[str] = Field(default_factory=list)
    field_checks: list[FieldCheck] = Field(default_factory=list)
    claim_checks: list[ClaimCheck] = Field(default_factory=list)
    official_deadline: date | None = None
    official_deadline_quote: str | None = None
    scam_signals: list[str] = Field(default_factory=list)
    sources_verified: bool = False
    summary: str


class VerificationResult(BaseModel):
    verdict: Verdict
    summary: str
    official_urls: list[str]
    supporting_urls: list[str]
    field_status: dict[str, str]
    official_deadline: date | None
    scam_signals: list[str]
    guard_notes: list[str]
    sources_verified: bool = False
    claim_checks: list[ClaimCheck] = Field(default_factory=list)


class Claim(BaseModel):
    text: str
    source_urls: list[str]


class SourceEvidence(BaseModel):
    url: str
    content: str
    source_type: Literal["page", "search_result"] = "page"


class ResearchReport(BaseModel):
    eligibility: list[Claim] = Field(default_factory=list)
    timeline: list[Claim] = Field(default_factory=list)
    how_to_apply: list[Claim] = Field(default_factory=list)
    past_editions: list[Claim] = Field(default_factory=list)
    selection_criteria: list[Claim] = Field(default_factory=list)
    red_flags: list[Claim] = Field(default_factory=list)
    related_links: list[str] = Field(default_factory=list)
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
