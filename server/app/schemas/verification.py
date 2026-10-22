from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import AliasChoices, BaseModel, Field, field_validator


class ClaimVerdictLabel(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient evidence"


class StageName(str, Enum):
    EXTRACTED = "extracted"
    CLAIMS = "claims"
    EVIDENCE = "evidence"
    VERDICT = "verdict"
    CARD = "card"


STAGE_ORDER: list[StageName] = [
    StageName.EXTRACTED,
    StageName.CLAIMS,
    StageName.EVIDENCE,
    StageName.VERDICT,
    StageName.CARD,
]

STAGE_ORDER_MAP: dict[str, int] = {
    StageName.EXTRACTED.value: 1,
    StageName.CLAIMS.value: 2,
    StageName.EVIDENCE.value: 3,
    StageName.VERDICT.value: 4,
    StageName.CARD.value: 5,
}


class RVPackData(BaseModel):
    transcript: str = ""
    on_screen: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""
    sections_found: list[str] = Field(default_factory=list)


class RVPackInput(BaseModel):
    content: str = Field(
        ...,
        description="Complete .rvpack text containing TRANSCRIPT, ON_SCREEN, and META sections.",
    )
    reel_id: int | None = Field(default=None, description="Optional existing user_reel_id to link with.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": (
                    "---TRANSCRIPT---\n"
                    "National AI Hackathon 2026 organized by IIT Bombay.\n"
                    "Registration fee is ₹500.\n"
                    "Application deadline is 15th December 2026.\n"
                    "Open to all engineering students.\n"
                    "Cash prize pool worth ₹5,00,000 and direct internship interviews.\n"
                    "---ON_SCREEN---\n"
                    "IIT Bombay AI Hackathon 2026\n"
                    "Apply online at https://iitb.ac.in/hackathon\n"
                    "Registration Fee: ₹500\n"
                    "---META---\n"
                    "author: IIT Bombay\n"
                    "title: IIT Bombay AI Hackathon 2026\n"
                    "category: hackathon\n"
                ),
                "reel_id": None,
            }
        }
    }

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Content must be a string containing .rvpack text.")
        stripped = v.strip()
        if not stripped:
            raise ValueError(
                "Content cannot be empty. Please provide valid .rvpack text containing "
                "TRANSCRIPT, ON_SCREEN, and META sections."
            )
        if len(stripped) < 10:
            raise ValueError("Content is too short to be a valid .rvpack package.")
        return v


class DeadlineInfo(BaseModel):
    raw: str | None = None
    date: str | None = None  # ISO format: YYYY-MM-DD
    year_ambiguous: bool = False
    ambiguity_reason: str | None = None
    reminder_eligible: bool = False
    vault_reminder_status: Literal["not_connected", "ready_to_connect", "connected"] = "not_connected"


# --- STAGE 2: CLAIMS ITEMS ---
class ClaimItem(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: Literal["organizer", "deadline", "fee", "eligibility", "reward", "event", "general"] = "general"
    source_section: Literal["TRANSCRIPT", "ON_SCREEN", "META", "COMBINED"] = "COMBINED"
    quote: str | None = None
    is_fee_warning_claim: bool = False


# --- STAGE 4: VERDICT ITEM ---
class ClaimVerdictItem(BaseModel):
    claim_id: str
    claim_text: str
    verdict: ClaimVerdictLabel
    explanation: str
    cited_sources: list[str] = Field(default_factory=list)
    is_fee_warning_claim: bool = False

    @field_validator("verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, v: Any) -> Any:
        if isinstance(v, str):
            normalized = v.strip().lower().replace("_", " ").replace("-", " ")
            for label in ClaimVerdictLabel:
                if label.value == normalized:
                    return label
        return v


# --- STAGE 1: EXTRACTED ---
class ExtractedStagePayload(BaseModel):
    title: str = ""
    organizer: str = ""
    author: str | None = Field(default=None, description="Social media content creator / publisher (distinct from event organizer).")
    category: str = "other"
    deadline: DeadlineInfo = Field(default_factory=DeadlineInfo)
    fee_raw: str | None = None
    has_fee: bool = False
    is_fee_warning: bool = False
    fee_warning_message: str | None = None
    eligibility: str | None = None
    reward_or_benefit: str | None = None
    mode: str | None = None
    location: str | None = None
    links: list[str] = Field(default_factory=list)
    source_quotes: dict[str, str] = Field(default_factory=dict)
    sections_found: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    claims: list[ClaimItem] = Field(default_factory=list)


# --- GEMINI STRUCTURED EXTRACTION SCHEMAS ---
class GeminiClaimAnalysis(BaseModel):
    title: str = Field(description="Strict title of the opportunity/event.")
    organizer: str = Field(description="Actual organizer of the event, or 'Unverified organizer' if not explicitly stated.")
    author: str | None = Field(default=None, description="The social media account / creator from metadata.")
    category: str = Field(default="other", description="Category: hackathon, internship, scholarship, competition, course, job, government_scheme, event, other.")
    deadline_raw: str | None = Field(default=None, description="Raw deadline mention from text.")
    deadline_date: str | None = Field(default=None, description="ISO YYYY-MM-DD date if unambiguous, else None.")
    year_ambiguous: bool = Field(default=False, description="True if deadline lacks explicit year or is ambiguous.")
    ambiguity_reason: str | None = Field(default=None, description="Reason if date/year is ambiguous.")
    has_fee: bool = Field(default=False, description="True if any registration or application fee is required.")
    is_fee_warning: bool = Field(default=False, description="True if fee is detected.")
    fee_raw: str | None = Field(default=None, description="Raw fee amount/currency mentioned, e.g. '₹500'.")
    fee_warning_message: str | None = Field(default=None, description="Neutral caution message regarding the fee.")
    eligibility: str | None = Field(default=None, description="Eligibility criteria mentioned.")
    reward_or_benefit: str | None = Field(default=None, description="Prize pool, stipend, or rewards mentioned.")
    mode: str | None = Field(default=None, description="online, offline, or hybrid.")
    links: list[str] = Field(default_factory=list, description="Extracted URLs.")
    source_quotes: dict[str, str] = Field(default_factory=dict, description="Key quotes from reel.")
    claims: list[ClaimItem] = Field(default_factory=list, description="Decomposed factual claims requiring verification.")
    search_queries: list[str] = Field(default_factory=list, description="2 to 3 targeted web search queries.")


class GeminiVerdictEvaluation(BaseModel):
    claim_verdicts: list[ClaimVerdictItem] = Field(
        description="Evaluations for each claim.",
        validation_alias=AliasChoices("claim_verdicts", "claims", "claim_evaluations"),
    )
    overall_verdict: ClaimVerdictLabel = Field(
        description="Overall verdict grounded in claim findings.",
        validation_alias=AliasChoices("overall_verdict", "verdict"),
    )
    summary: str = Field(
        description="Grounded summary of the verification outcome.",
        validation_alias=AliasChoices("summary", "explanation", "verdict_summary"),
    )
    scam_warnings: list[str] = Field(default_factory=list, description="Scam warnings or neutral fee cautions.")
    has_scam_warning: bool = Field(default=False, description="True if fee caution or scam warning is present.")
    fraudulent_detected: bool = Field(default=False, description="True only if concrete fraud/hoax is verified by credible evidence.")

    @field_validator("overall_verdict", mode="before")
    @classmethod
    def normalize_overall_verdict(cls, v: Any) -> Any:
        if isinstance(v, str):
            normalized = v.strip().lower().replace("_", " ").replace("-", " ")
            for label in ClaimVerdictLabel:
                if label.value == normalized:
                    return label
        return v


class ClaimsStagePayload(BaseModel):
    claims: list[ClaimItem] = Field(default_factory=list)
    total_claims: int = 0
    contains_fee_claim: bool = False


# --- STAGE 3: EVIDENCE ---
class EvidenceItem(BaseModel):
    id: str
    claim_ids: list[str] = Field(default_factory=list)
    url: str
    title: str = ""
    snippet: str = ""
    domain: str = ""
    domain_trust: Literal["high", "official_match", "platform", "third_party", "risky"] = "third_party"
    source_type: Literal[
        "official_organizer",
        "trusted_institution",
        "reputable_media",
        "unrelated_institution",
        "generic_directory",
        "third_party",
        "social_media",
        "unverified_suspicious",
    ] = "third_party"
    source_label: str = "Third-party source"
    retrieved_at: str | None = None


class EvidenceStagePayload(BaseModel):
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    queries_used: list[str] = Field(default_factory=list)
    official_domains: list[str] = Field(default_factory=list)
    search_status: str = Field(default="unavailable", description="'completed', 'unconfigured', 'failed', or 'no_results'")
    search_notes: str | None = None


# --- STAGE 4: VERDICT ---
class VerdictStagePayload(BaseModel):
    claim_verdicts: list[ClaimVerdictItem] = Field(default_factory=list)
    overall_verdict: ClaimVerdictLabel
    summary: str
    verification_method: str = Field(
        default="Gemini AI analysis + web search",
        description="Transparent verification method used, e.g. 'Gemini AI analysis + web search', 'Gemini AI analysis only (external web search unavailable)'.",
    )
    scam_warnings: list[str] = Field(default_factory=list)
    has_scam_warning: bool = False
    fraudulent_detected: bool = False  # True only if concrete fraud/hoax is verified, NOT from fee alone


# --- STAGE 5: CARD ---
class OpportunityCardPayload(BaseModel):
    card_id: str
    run_id: str
    user_reel_id: int | None = None
    title: str
    organizer: str
    author: str | None = Field(default=None, description="Social media content creator / publisher.")
    category: str
    overall_verdict: ClaimVerdictLabel
    badge: str
    verification_method: str = "Gemini AI analysis + web search"
    scam_warnings: list[str] = Field(default_factory=list)
    claims_summary: list[ClaimVerdictItem] = Field(default_factory=list)
    official_links: list[str] = Field(default_factory=list)
    deadline: DeadlineInfo = Field(default_factory=DeadlineInfo)
    can_save_reminder: bool = False
    vault_reminder_action: dict[str, Any] | None = None
    stages_verified: list[str] = Field(default_factory=list)
    created_at: str


# --- PERSISTED STAGE RECORD ---
class StageRecordOut(BaseModel):
    id: str
    run_id: str
    stage_name: str
    stage_order: int
    status: Literal["completed", "failed", "in_progress"] = "completed"
    payload: dict[str, Any]
    created_at: str


# --- RUN MODELS ---
class VerificationRunOut(BaseModel):
    id: str
    user_id: str
    user_reel_id: int | None = None
    input_type: str = "rvpack"
    status: Literal["in_progress", "completed", "failed"] = "in_progress"
    current_stage: str = "extracted"
    completed_stages: list[str] = Field(default_factory=list)
    stages: list[StageRecordOut] = Field(default_factory=list)
    card: OpportunityCardPayload | None = None
    persistence_backend: str | None = Field(
        default=None,
        description="The storage backend used for persistence ('supabase' or 'development_file_fallback').",
    )
    created_at: str
    updated_at: str


class VaultReminderConnectIn(BaseModel):
    reel_id: int | None = None
    label: str | None = None
    event_date: str | None = None  # Explicit user date (YYYY-MM-DD) if year was ambiguous


class VaultReminderConnectOut(BaseModel):
    success: bool
    saved_date_id: int | None = None
    reel_id: int | None = None
    label: str
    event_date: str
    status: str
    message: str
