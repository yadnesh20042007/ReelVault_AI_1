import concurrent.futures
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.db import repo as main_repo
from app.db import verification_repo
from app.errors import AppError, PipelineError, ProviderTimeout
from app.llm import (
    ModelQuotaError,
    _is_key_or_quota_error,
    get_llm,
    is_auth_error,
    is_invalid_argument_error,
    is_not_found_error,
    is_quota_or_rate_limit_error,
)
from app.schemas.verification import (
    ClaimItem,
    ClaimVerdictItem,
    ClaimVerdictLabel,
    ClaimsStagePayload,
    DeadlineInfo,
    EvidenceItem,
    EvidenceStagePayload,
    ExtractedStagePayload,
    GeminiClaimAnalysis,
    GeminiVerdictEvaluation,
    OpportunityCardPayload,
    RVPackData,
    StageName,
    STAGE_ORDER,
    STAGE_ORDER_MAP,
    VerdictStagePayload,
)
from app.services.rvpack_parser import parse_rvpack
from app.services.tools.domain_rules import (
    GENERIC_OPPORTUNITY_TERMS,
    STOP,
    check_domain,
    classify_source,
    is_generic_root_url,
    verify_official_registration_link,
)

log = logging.getLogger("verification_workflow")

# Shared thread pool for bounded LLM invocations to avoid thread churn
_LLM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="gemini_llm_worker",
)


def _classify_gemini_error(exc: Exception) -> tuple[bool, int, str, str]:
    """Classify exception to determine if it is a transient, retryable Gemini error.
    
    Returns:
        (is_transient: bool, status_code: int, error_code: str, user_friendly_message: str)
    """
    if isinstance(exc, (concurrent.futures.TimeoutError, TimeoutError)):
        return (
            True,
            504,
            "gemini_timeout",
            "Gemini model request timed out (504 DEADLINE_EXCEEDED). You can retry or resume this verification run.",
        )

    msg = str(exc).lower()

    # 1. 504 / DEADLINE_EXCEEDED / Timeout
    if any(k in msg for k in ("504", "deadline_exceeded", "deadline exceeded", "timed out", "timeout")):
        return (
            True,
            504,
            "gemini_timeout",
            "Gemini model request timed out (504 DEADLINE_EXCEEDED). You can retry or resume this verification run.",
        )

    # 2. Authentication / Key errors (evaluated before quota to prevent misclassifying invalid keys)
    if is_auth_error(exc):
        return (
            False,
            401,
            "gemini_auth_error",
            "Invalid or unauthenticated Gemini API key. Please verify your GEMINI_API_KEY credentials.",
        )

    # 3. Model Not Found / Unsupported Model Identifier (404)
    if is_not_found_error(exc):
        return (
            False,
            404,
            "gemini_model_not_found",
            f"Configured Gemini model not found or unsupported ({exc}).",
        )

    # 4. Bad request / Invalid Argument (400)
    if is_invalid_argument_error(exc):
        return (
            False,
            400,
            "gemini_invalid_argument",
            f"Invalid request parameters to Gemini model: {exc}",
        )

    # 5. Distinguish malformed output / schema parse failures: these are NOT transient provider errors
    is_schema_parse = any(p in msg for p in ("schema parse", "outputparser", "jsondecodeerror", "validation error"))
    if is_schema_parse:
        return False, 422, "malformed_model_output", f"Model produced malformed or invalid output: {exc}"

    # 6. 429 / Rate limit / Resource exhausted across all models
    if is_quota_or_rate_limit_error(exc):
        return (
            True,
            429,
            "gemini_rate_limited",
            "Gemini API quota or rate limit reached across all available models. Please wait for quota refresh and resume.",
        )

    # 7. 503 / 502 / Service unavailable / Server errors
    if any(k in msg for k in ("503", "unavailable", "service unavailable", "serviceunavailable", "502", "bad gateway")):
        return (
            True,
            503,
            "gemini_unavailable",
            "Gemini service temporarily unavailable (503). Please retry in a few moments.",
        )

    return False, 500, "gemini_error", str(exc)


def _parse_and_validate_structured_output(raw_output: Any, schema: type[BaseModel]) -> Any:
    """Safely parse and validate model output into the requested Pydantic schema."""
    if raw_output is None:
        raise AppError(
            f"Gemini returned None instead of a structured {schema.__name__} response. "
            "This typically indicates the model produced an empty response. "
            "Retry or check model availability.",
            status=422,
            code="malformed_model_output",
        )

    if isinstance(raw_output, schema):
        return raw_output

    if isinstance(raw_output, dict):
        try:
            return schema.model_validate(raw_output)
        except ValidationError as exc:
            raise AppError(
                f"Model output did not conform to schema {schema.__name__}: {exc}",
                status=422,
                code="malformed_model_output",
            ) from exc

    # Handle AIMessage or objects with tool_calls
    tool_calls = getattr(raw_output, "tool_calls", None)
    if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
        tc = tool_calls[0]
        args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)
        if isinstance(args, dict):
            try:
                return schema.model_validate(args)
            except ValidationError as exc:
                raise AppError(
                    f"Model tool call arguments did not conform to schema {schema.__name__}: {exc}",
                    status=422,
                    code="malformed_model_output",
                ) from exc
        elif isinstance(args, str) and args.strip():
            try:
                data = json.loads(args)
                return schema.model_validate(data)
            except Exception as exc:
                raise AppError(
                    f"Model tool call arguments could not be parsed as valid JSON: {exc}",
                    status=422,
                    code="malformed_model_output",
                ) from exc

    content = getattr(raw_output, "content", raw_output)
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
        content = "\n".join(parts)

    if not isinstance(content, str) or not content.strip():
        raise AppError(
            f"Model returned an empty or whitespace response instead of a structured {schema.__name__}.",
            status=422,
            code="malformed_model_output",
        )

    cleaned = content.strip()
    if "```" in cleaned:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if m:
            cleaned = m.group(1).strip()

    try:
        data = json.loads(cleaned)
    except Exception as exc:
        m = re.search(r"(\{[\s\S]*\})", cleaned)
        if m:
            try:
                data = json.loads(m.group(1))
            except Exception:
                raise AppError(
                    f"Model produced malformed JSON that could not be decoded: {exc}",
                    status=422,
                    code="malformed_model_output",
                ) from exc
        else:
            raise AppError(
                f"Model produced malformed JSON that could not be decoded: {exc}",
                status=422,
                code="malformed_model_output",
            ) from exc

    if not isinstance(data, dict):
        raise AppError(
            f"Expected JSON object for schema {schema.__name__}, got {type(data).__name__}.",
            status=422,
            code="malformed_model_output",
        )

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise AppError(
            f"Model output missing required fields or invalid for schema {schema.__name__}: {exc}",
            status=422,
            code="malformed_model_output",
        ) from exc


def _invoke_structured_llm(
    client: Any,
    schema: type[BaseModel],
    messages: list[dict],
    fallback_kind: str = "fast",
    timeout_s: float | None = None,
    max_retries: int = 1,
    backoff_s: float = 1.0,
) -> Any:
    """Invoke LLM with structured output, supporting bounded timeout, single bounded retry, and KeyPool failover.
    
    NOTE ON THREAD SAFETY & CANCELLATION:
    In Python's threading model, worker threads cannot be asynchronously terminated or killed from
    the outside while executing blocking I/O (pthread_cancel does not exist in Python). Calling
    future.cancel() prevents pending tasks from starting, but cannot kill an already-running thread.
    True network cancellation and deadline bounding are enforced by the underlying client socket-level
    timeout (e.g., gemini_http_timeout_s=30.0 on MonitoredChatGoogleGenerativeAI and ChatGoogleGenerativeAI),
    which causes the OS socket to abort and raise DeadlineExceeded/TimeoutError. The executor result timeout
    acts as an upper-bound watchdog (e.g., workflow_watchdog_timeout_s=35.0) providing headroom so
    ReelVault's workflow is never blocked indefinitely, without falsely claiming the underlying thread was killed.
    """
    settings = get_settings()
    watchdog_timeout = timeout_s if timeout_s is not None else getattr(settings, "workflow_watchdog_timeout_s", 35.0)
    http_timeout = getattr(settings, "gemini_http_timeout_s", 30.0)

    def _execute():
        if client is None:
            if not settings.get_all_gemini_keys():
                raise AppError(
                    "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment to perform verification.",
                    status=503,
                    code="llm_unconfigured",
                )
            llm = get_llm(fallback_kind, timeout=http_timeout)
            try:
                structured_llm = llm.with_structured_output(schema)
                res = structured_llm.invoke(messages)
            except ValidationError as exc:
                raise AppError(
                    f"Model output missing required fields or invalid for schema {schema.__name__}: {exc}",
                    status=422,
                    code="malformed_model_output",
                ) from exc
            except (NotImplementedError, AttributeError):
                res = llm.invoke(messages)
            return _parse_and_validate_structured_output(res, schema)

        if hasattr(client, "with_structured_output"):
            try:
                structured = client.with_structured_output(schema)
            except (NotImplementedError, AttributeError):
                structured = None
            if structured is not None:
                try:
                    res = structured.invoke(messages)
                except ValidationError as exc:
                    raise AppError(
                        f"Model output missing required fields or invalid for schema {schema.__name__}: {exc}",
                        status=422,
                        code="malformed_model_output",
                    ) from exc
                if res is not None:
                    return _parse_and_validate_structured_output(res, schema)

        res = client.invoke(messages)
        return _parse_and_validate_structured_output(res, schema)

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        future = _LLM_EXECUTOR.submit(_execute)
        try:
            return future.result(timeout=watchdog_timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            last_exc = exc
            log.warning(
                "LLM execution watchdog timed out after %.1fs on attempt %d/%d. "
                "Underlying worker thread cannot be forcefully cancelled in Python; "
                "abandoning future and relying on client socket-level timeout (%.1fs) for transport termination.",
                watchdog_timeout, attempt + 1, max_retries + 1, http_timeout,
            )
            is_transient, status_code, err_code, user_msg = _classify_gemini_error(exc)
            if is_transient and attempt < max_retries:
                log.warning(
                    "Transient Gemini watchdog timeout on attempt %d/%d; retrying once after %.1fs bounded backoff...",
                    attempt + 1, max_retries + 1, backoff_s,
                )
                time.sleep(backoff_s)
                continue
            if is_transient:
                log.error("Gemini call watchdog timed out after %d retry: %s", attempt, exc)
                raise AppError(user_msg, status=status_code, code=err_code) from exc
            raise
        except Exception as exc:
            future.cancel()
            last_exc = exc
            is_transient, status_code, err_code, user_msg = _classify_gemini_error(exc)

            if is_transient and attempt < max_retries:
                log.warning(
                    "Transient Gemini error on attempt %d/%d (%s); retrying once after %.1fs bounded backoff...",
                    attempt + 1, max_retries + 1, exc, backoff_s,
                )
                time.sleep(backoff_s)
                continue

            if is_transient:
                log.error("Gemini call failed with transient error after %d retry: %s", attempt, exc)
                raise AppError(user_msg, status=status_code, code=err_code) from exc

            if isinstance(exc, AppError):
                raise

            log.error("Gemini call failed with non-transient error: %s", exc)
            raise

    if last_exc:
        raise last_exc

_URL_REGEX = re.compile(
    r"https?://[^\s)\]>\"',]+|(?:www\.)[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}(?:/[-\w@:%_+.~#?&/=]*)?",
    re.IGNORECASE,
)

# Month names regex for date parsing
_MONTH_REGEX = (
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan\.?|feb\.?|mar\.?|apr\.?|may|jun\.?|jul\.?|aug\.?|sep\.?|sept\.?|oct\.?|nov\.?|dec\.?)"
)
_MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_DEADLINE_KW_REGEX = re.compile(
    r"(?:deadline|last\s+date|apply\s+by|apply\s+before|register\s+by|register\s+before|due\s+date|registration\s+ends|ends\s+on|closes\s+on|submission\s+deadline)\s*(?:is|:|-)?\s*([^\n.,;]+)",
    re.IGNORECASE,
)

_GENERIC_ACCOUNT_NAMES = {"instagram", "user", "admin", "admin user", "unknown", "reel", "official"}

SOCIAL_DOMAINS = {
    "instagram.com", "instagr.am", "youtube.com", "youtu.be",
    "tiktok.com", "facebook.com", "fb.com", "twitter.com",
    "x.com", "reddit.com", "linkedin.com", "threads.net", "t.me",
}

GENERIC_DIRECTORIES = {
    "unstop.com", "devfolio.co", "devpost.com", "eventbrite.com", "eventbrite.in",
    "hackerearth.com", "knowafest.com", "allevents.in", "meetup.com", "reddit.com",
    "quora.com", "medium.com", "ycombinator.com", "dare2compete.com", "geeksforgeeks.org",
    "internshala.com", "opportunitydesk.org", "youthop.com",
}

EXTRACTION_SYSTEM_PROMPT = """You are ReelVault's expert factual extraction and claim analysis engine.
Your task is to analyze student opportunities and event announcements from social media reels (.rvpack content) with strict semantic accuracy.

Input sections include:
- TRANSCRIPT: Spoken audio from the reel.
- ON_SCREEN: Text detected visually on video frames.
- META: Post metadata (platform, url, author/creator, title).

Guidelines for Semantic Extraction:
1. Title: Identify the specific, genuine title of the opportunity/event.
2. Organizer vs Content Creator (CRITICAL):
   - META author is merely the social media account/creator, NOT automatically the event organizer.
   - Do NOT assume the Instagram handle or author is the event organizer unless explicit text in transcript or on-screen states that relationship.
   - Only set the organizer if explicitly announced (e.g., "Organized by X", "Conducted by X", "Presented by X").
   - If the organizer is unknown or not explicitly stated, return "Unverified organizer".
3. Category: Choose accurately from [hackathon, internship, scholarship, competition, course, job, government_scheme, event, other].
4. Deadline & Ambiguity:
   - Extract any deadline mention.
   - If a posting date is provided in META (e.g. posted: 2026-10-05) and the announcement specifies a month and day (e.g. 31 Oct), resolve the calendar year using the posting date context (e.g. 2026-10-31), set year_ambiguous=False, and populate deadline_date (YYYY-MM-DD).
   - If a specific calendar year is missing or ambiguous and cannot be resolved, set year_ambiguous=True and ambiguity_reason explaining that the year is not stated.
   - Only leave deadline_date as null if the date and year cannot be unambiguously resolved.
5. Registration Fee & Neutral Caution:
   - Check if a fee or payment is required (e.g. ₹500, Rs. 500, $50).
   - If a fee is present, set has_fee=True, is_fee_warning=True, and extract fee_raw.
   - Generate a strictly neutral caution message:
     "Registration fee detected ({fee_raw}). Verify the organizer's identity, official event page, payment recipient, and refund policy before paying. A fee alone does not establish fraud."
   - Never assume that charging a fee implies fraud or that legitimate opportunities are always free.
6. Factual Claims to Verify:
   - Decompose the announcement into distinct, falsifiable claims (claim_id: "c1", "c2", ...).
   - Claim types: "organizer", "deadline", "fee", "eligibility", "reward", "event", "general".
   - Include direct quotes or references from the transcript/on-screen text.
7. Targeted Web Search Queries:
   - Formulate at most 2 concise, highly targeted search queries to verify these specific claims against external sources (e.g. exact event name + organizer + "official", or registration details).
8. Output Format:
   - Return a strictly valid JSON object matching the GeminiClaimAnalysis schema.
   - Do not include markdown code block formatting or any surrounding conversational text.
"""

VERDICT_SYSTEM_PROMPT = """You are ReelVault's evidence evaluation and verdict engine.
Your task is to evaluate extracted factual claims against the externally retrieved search evidence.

You are provided with:
1. The extracted announcement details and factual claims.
2. The list of retrieved web evidence items (each with id, url, domain, source_type, title, and snippet).

Verdict Guidelines:
1. Assign exactly one of the four allowed verdict labels to EACH claim:
   - "supported": Credible supplied evidence directly corroborates the specific claim.
   - "partially supported": Some meaningful parts are corroborated, but material details remain uncertain or from secondary platforms.
   - "contradicted": Credible supplied evidence directly conflicts with the claim (e.g. reported as scam, fake, different organizer, or official page states registration is free).
   - "insufficient evidence": Available evidence does not establish whether the claim is true.
2. Reject Irrelevant Sources & Separate Claims (CRITICAL):
   - Do NOT accept a source merely because its domain has .edu or .ac.in or contains keywords like 'hackathon', 'IIT', or 'AI'.
   - Reject unrelated institutions, generic landing pages, irrelevant directories, and pages about different events as evidence for the target event.
   - Evaluate every claim separately: an article confirming the organizer exists (e.g. a university's general homepage or history) does NOT corroborate the registration fee or deadline!
   - Pages for different past editions (e.g. 2024 vs 2026) or similar-named events do NOT corroborate the current event.
3. Evidence Grounding & Citation Integrity:
   - ONLY cite URLs that are present in the provided evidence items.
   - Lack of evidence is NOT proof of fraud. An event absent from search results is NOT proven fake; mark it "insufficient evidence".
   - A syntactically valid date is NOT evidence that the deadline is true.
   - An unrelated search result mentioning the institution or a similar event does NOT support the claim.
4. Fee & Scam Assessment:
   - A registration fee alone (e.g., ₹500) must NEVER automatically trigger a "contradicted" or fraud verdict.
   - A legitimate event may charge a fee. If a fee is required, provide the neutral caution.
   - Only flag fraudulent_detected=True if concrete, credible external evidence reveals an impersonation, hoax, scam warning, or fraudulent registration page.
5. Overall Verdict & Official Status:
   - "supported": ONLY when core claims are directly corroborated by primary official organizer sources for this exact event.
   - "partially supported": When secondary sources corroborate key details, but primary organizer verification is missing.
   - "contradicted": When credible evidence conflicts with core claims.
   - "insufficient evidence": When evidence is insufficient to verify the opportunity.
6. Summary:
   - Grounded summary distinguishing: what the reel claims, what independent sources corroborate, what is contradicted, and what remains unverified.
7. Output Format:
   - Return a strictly valid JSON object matching the GeminiVerdictEvaluation schema with this structure:
     {
       "claim_verdicts": [
         {
           "claim_id": "c1",
           "claim_text": "Claim text here",
           "verdict": "supported" | "partially supported" | "contradicted" | "insufficient evidence",
           "explanation": "Brief factual explanation citing sources",
           "cited_sources": ["https://..."],
           "is_fee_warning_claim": false
         }
       ],
       "overall_verdict": "supported" | "partially supported" | "contradicted" | "insufficient evidence",
       "summary": "Grounded summary of findings",
       "scam_warnings": [],
       "has_scam_warning": false,
       "fraudulent_detected": false
     }
   - The fields "claim_verdicts", "overall_verdict", and "summary" are strictly REQUIRED.
   - Every claim provided in the input MUST have an evaluation item in "claim_verdicts".
   - Use only the allowed verdict strings: "supported", "partially supported", "contradicted", "insufficient evidence".
   - Do not include markdown code block formatting or any surrounding conversational text.
"""


_PLACEHOLDER_DATE_TERMS = {
    "date unavailable", "unavailable", "not specified", "not announced",
    "none", "null", "n/a", "unknown", "tbd", "to be announced", "tba",
    "soon", "closing soon", "ends soon", "coming soon", "no deadline",
}


def _parse_deadline(raw_text: str, meta: dict[str, Any] | None = None) -> DeadlineInfo:
    """Extract deadline from raw text, explicitly detecting ambiguous year vs unambiguous date.
    
    If year is not stated in raw text, attempts to resolve calendar year from post metadata (e.g. posted date).
    Normalizes relative dates ONLY when the source date is reliably known.
    Never substitutes current date or invents deadlines.
    """
    if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
        return DeadlineInfo(
            raw=None,
            date=None,
            year_ambiguous=False,
            ambiguity_reason=None,
            reminder_eligible=False,
            vault_reminder_status="not_connected",
        )

    raw_clean = raw_text.strip()
    if raw_clean.lower() in _PLACEHOLDER_DATE_TERMS:
        return DeadlineInfo(
            raw=None,
            date=None,
            year_ambiguous=False,
            ambiguity_reason=None,
            reminder_eligible=False,
            vault_reminder_status="not_connected",
        )

    match = _DEADLINE_KW_REGEX.search(raw_clean)
    if not match:
        month_match = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_REGEX})(?:\s+(\d{{4}}))?\b", raw_clean, re.IGNORECASE)
        if not month_match:
            month_match = re.search(rf"\b({_MONTH_REGEX})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{{4}}))?\b", raw_clean, re.IGNORECASE)
        if not month_match:
            # Check for relative date mention in raw_clean directly
            rel_m = re.search(r"\b(\d{1,3})\s+days?\s*(?:left|remaining|more)?\b", raw_clean, re.IGNORECASE)
            if not rel_m:
                rel_m = re.search(r"\b(?:closes?|ends?|expires?|in)\s+(\d{1,3})\s+days?\b", raw_clean, re.IGNORECASE)
            rel_w_m = re.search(r"\b(\d{1,2})\s+weeks?\s*(?:left|remaining|more)?\b", raw_clean, re.IGNORECASE)
            if not rel_w_m:
                rel_w_m = re.search(r"\b(?:closes?|ends?|expires?|in)\s+(\d{1,2})\s+weeks?\b", raw_clean, re.IGNORECASE)

            if rel_m or rel_w_m:
                candidate = (rel_m or rel_w_m).group(0).strip()
                days_delta = int(rel_m.group(1)) if rel_m else int(rel_w_m.group(1)) * 7
                if meta and isinstance(meta, dict):
                    posted_val = str(meta.get("posted") or meta.get("date") or meta.get("post_date") or meta.get("created_at") or "").strip()
                    posted_iso_m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})", posted_val)
                    if posted_iso_m:
                        try:
                            base_dt = datetime(int(posted_iso_m.group(1)), int(posted_iso_m.group(2)), int(posted_iso_m.group(3)))
                            resolved_dt = base_dt + timedelta(days=days_delta)
                            return DeadlineInfo(
                                raw=candidate,
                                date=resolved_dt.strftime("%Y-%m-%d"),
                                year_ambiguous=False,
                                reminder_eligible=True,
                                vault_reminder_status="ready_to_connect",
                            )
                        except ValueError:
                            pass
                return DeadlineInfo(
                    raw=candidate,
                    date=None,
                    year_ambiguous=False,
                    ambiguity_reason=f"Relative deadline '{candidate}' lacks a reliably known source date; explicit user confirmation required.",
                    reminder_eligible=False,
                    vault_reminder_status="not_connected",
                )

            return DeadlineInfo(
                raw=None,
                date=None,
                year_ambiguous=False,
                ambiguity_reason=None,
                reminder_eligible=False,
                vault_reminder_status="not_connected",
            )
        candidate = month_match.group(0).strip()
    else:
        candidate = match.group(1).strip()
        candidate = re.split(r"[.!?\n]", candidate)[0].strip()

    candidate = re.sub(r"^(?:apply\s+)?(?:before|by|on|is|ends|ends\s+on)\s+", "", candidate, flags=re.IGNORECASE).strip()

    if candidate.lower() in _PLACEHOLDER_DATE_TERMS or re.match(r"^(?:none|n/?a|null|unknown|tbd|tba|soon|not\s+specified|date\s+unavailable)$", candidate.lower()):
        return DeadlineInfo(
            raw=None,
            date=None,
            year_ambiguous=False,
            ambiguity_reason=None,
            reminder_eligible=False,
            vault_reminder_status="not_connected",
        )

    # Relative date parsing in candidate
    rel_m = re.search(r"\b(\d{1,3})\s+days?\s*(?:left|remaining|more)?\b", candidate, re.IGNORECASE)
    if not rel_m:
        rel_m = re.search(r"\b(?:closes?|ends?|expires?|in)\s+(\d{1,3})\s+days?\b", candidate, re.IGNORECASE)
    rel_w_m = re.search(r"\b(\d{1,2})\s+weeks?\s*(?:left|remaining|more)?\b", candidate, re.IGNORECASE)
    if not rel_w_m:
        rel_w_m = re.search(r"\b(?:closes?|ends?|expires?|in)\s+(\d{1,2})\s+weeks?\b", candidate, re.IGNORECASE)

    if rel_m or rel_w_m:
        days_delta = int(rel_m.group(1)) if rel_m else int(rel_w_m.group(1)) * 7
        if meta and isinstance(meta, dict):
            posted_val = str(meta.get("posted") or meta.get("date") or meta.get("post_date") or meta.get("created_at") or "").strip()
            posted_iso_m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})", posted_val)
            if posted_iso_m:
                try:
                    base_dt = datetime(int(posted_iso_m.group(1)), int(posted_iso_m.group(2)), int(posted_iso_m.group(3)))
                    resolved_dt = base_dt + timedelta(days=days_delta)
                    return DeadlineInfo(
                        raw=candidate,
                        date=resolved_dt.strftime("%Y-%m-%d"),
                        year_ambiguous=False,
                        reminder_eligible=True,
                        vault_reminder_status="ready_to_connect",
                    )
                except ValueError:
                    pass
        return DeadlineInfo(
            raw=candidate,
            date=None,
            year_ambiguous=False,
            ambiguity_reason=f"Relative deadline '{candidate}' lacks a reliably known source date; explicit user confirmation required.",
            reminder_eligible=False,
            vault_reminder_status="not_connected",
        )

    # ISO format: YYYY-MM-DD
    iso_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", candidate)
    if iso_match:
        try:
            d_obj = datetime.strptime(iso_match.group(0), "%Y-%m-%d")
            return DeadlineInfo(
                raw=candidate,
                date=d_obj.strftime("%Y-%m-%d"),
                year_ambiguous=False,
                reminder_eligible=True,
                vault_reminder_status="ready_to_connect",
            )
        except ValueError:
            pass

    # Day Month Year
    dmy = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_REGEX})\s+(\d{{4}})\b", candidate, re.IGNORECASE)
    if dmy:
        day = int(dmy.group(1))
        m_str = dmy.group(2).lower().rstrip(".")
        month = _MONTH_MAP.get(m_str, 1)
        year = int(dmy.group(3))
        try:
            d_obj = datetime(year, month, day)
            return DeadlineInfo(
                raw=candidate,
                date=d_obj.strftime("%Y-%m-%d"),
                year_ambiguous=False,
                reminder_eligible=True,
                vault_reminder_status="ready_to_connect",
            )
        except ValueError:
            pass

    mdy = re.search(rf"\b({_MONTH_REGEX})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s*)(\d{{4}})\b", candidate, re.IGNORECASE)
    if mdy:
        m_str = mdy.group(1).lower().rstrip(".")
        month = _MONTH_MAP.get(m_str, 1)
        day = int(mdy.group(2))
        year = int(mdy.group(3))
        try:
            d_obj = datetime(year, month, day)
            return DeadlineInfo(
                raw=candidate,
                date=d_obj.strftime("%Y-%m-%d"),
                year_ambiguous=False,
                reminder_eligible=True,
                vault_reminder_status="ready_to_connect",
            )
        except ValueError:
            pass

    # Ambiguous year check (e.g. "31 Oct" or "15th November" without a year)
    dm_no_year = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_REGEX})\b", candidate, re.IGNORECASE)
    if not dm_no_year:
        dm_no_year = re.search(rf"\b({_MONTH_REGEX})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", candidate, re.IGNORECASE)

    if dm_no_year:
        resolved_year = None
        year_provenance = None

        # 1. Check if posting date in meta resolves the ambiguous year
        if meta and isinstance(meta, dict):
            posted_val = str(meta.get("posted") or meta.get("date") or meta.get("post_date") or meta.get("created_at") or "").strip()
            post_year_m = re.search(r"\b(20\d\d)\b", posted_val)
            if post_year_m:
                resolved_year = int(post_year_m.group(1))
                year_provenance = f"spoken in reel transcript; year resolved from post metadata ({resolved_year})"

            # 2. Check title or opportunity name in meta
            if not resolved_year:
                title_val = str(meta.get("title") or meta.get("name") or "").strip()
                title_year_m = re.search(r"\b(20\d\d)\b", title_val)
                if title_year_m:
                    resolved_year = int(title_year_m.group(1))
                    year_provenance = f"spoken in reel transcript; year resolved from contextual event evidence ({resolved_year})"

            # 3. Check contextual text passed in meta
            if not resolved_year:
                ctx_val = str(meta.get("context_text") or meta.get("caption") or meta.get("transcript") or "").strip()
                ctx_year_m = re.search(r"\b(20\d\d)\b", ctx_val)
                if ctx_year_m:
                    resolved_year = int(ctx_year_m.group(1))
                    year_provenance = f"spoken in reel transcript; year resolved from contextual event evidence ({resolved_year})"

        # 4. Check full raw_clean / raw_text passed into _parse_deadline
        if not resolved_year and raw_clean:
            clean_year_m = re.search(r"\b(20\d\d)\b", raw_clean)
            if clean_year_m:
                resolved_year = int(clean_year_m.group(1))
                year_provenance = f"spoken in reel transcript; year resolved from contextual event evidence ({resolved_year})"

        if resolved_year:
            g1 = dm_no_year.group(1).lower().rstrip(".")
            g2 = dm_no_year.group(2).lower().rstrip(".")
            if g1 in _MONTH_MAP:
                month = _MONTH_MAP[g1]
                day = int(re.sub(r"\D", "", g2) or "1")
            else:
                day = int(re.sub(r"\D", "", g1) or "1")
                month = _MONTH_MAP.get(g2, 1)
            try:
                d_obj = datetime(resolved_year, month, day)
                return DeadlineInfo(
                    raw=candidate,
                    date=d_obj.strftime("%Y-%m-%d"),
                    year_ambiguous=False,
                    reminder_eligible=True,
                    vault_reminder_status="ready_to_connect",
                    provenance=year_provenance,
                    year_resolved_from=f"contextual evidence ({resolved_year})",
                )
            except ValueError:
                pass

        return DeadlineInfo(
            raw=candidate,
            date=None,
            year_ambiguous=True,
            ambiguity_reason="Year not specified in source text (e.g. '" + dm_no_year.group(0) + "'); explicit user confirmation required before scheduling Vault reminder.",
            reminder_eligible=False,
            vault_reminder_status="not_connected",
            provenance="spoken in reel transcript; year ambiguous",
        )

    return DeadlineInfo(
        raw=candidate,
        date=None,
        year_ambiguous=False,
        ambiguity_reason="Date format is unparseable as an absolute date; explicit user confirmation required.",
        reminder_eligible=False,
        vault_reminder_status="not_connected",
    )


def is_substantively_relevant(
    ev_title: str,
    ev_snippet: str,
    ev_url: str,
    source_type: str,
    extracted: ExtractedStagePayload,
) -> tuple[bool, str]:
    """Determine whether evidence substantively pertains to the specific target opportunity.
    Works generally across hackathons, scholarships, internships, jobs, grants, competitions, courses, etc.
    Rejects:
    - Generic directory homepages that do not match the target opportunity.
    - Reputable but unrelated institutions (e.g. mit.edu for IIT Bombay event or Stanford fellowship).
    - Different events with similar names or different past years (e.g. 2024 vs 2026).
    - Phishing or unverified lookalikes.
    """
    text_corpus = f"{ev_title} {ev_snippet} {ev_url}".lower()

    # Rejection 0: Unverified suspicious or lookalike domains
    if source_type == "unverified_suspicious":
        return False, "Unverified, deceptive lookalike, or suspicious source domain."

    # Directly submitted links from the package are retained as submitted source links
    if any(ev_url.lower() == u.lower() for u in extracted.links):
        return True, "Direct link submitted with announcement."

    _extracted_title = extracted.title if isinstance(extracted.title, str) else ""
    _extracted_org = extracted.organizer if isinstance(extracted.organizer, str) else ""
    title_tokens = [
        w for w in re.findall(r"[a-z0-9]+", _extracted_title.lower())
        if len(w) >= 3 and w not in STOP and w not in GENERIC_OPPORTUNITY_TERMS
    ]

    organizer_clean = _extracted_org.strip()
    organizer_tokens = [
        w for w in re.findall(r"[a-z0-9]+", organizer_clean.lower())
        if len(w) >= 3 and w not in STOP and organizer_clean not in ("", "Unverified organizer")
    ]

    # Check 1: Unrelated institution rejection
    if source_type == "unrelated_institution":
        # Unrelated institutions must not be accepted unless they explicitly discuss the target opportunity AND organizer
        has_title = bool(title_tokens and any(t in text_corpus for t in title_tokens))
        has_org = bool(organizer_tokens and any(t in text_corpus for t in organizer_tokens))
        if not (has_title and has_org):
            return False, "Unrelated institution domain not hosting or corroborating the target opportunity."

    # Check 2: Generic directory rejection
    if source_type == "generic_directory":
        # A generic directory must explicitly mention distinct title tokens of the specific opportunity
        matched_title_count = sum(t in text_corpus for t in title_tokens) if title_tokens else 0
        if title_tokens and matched_title_count == 0:
            return False, "Generic directory listing does not reference the target opportunity."

    # Check 3: Edition / Year mismatch check
    target_year = None
    target_year_match = re.search(r"\b(202[0-9])\b", f"{extracted.title} {extracted.deadline.raw or ''} {extracted.deadline.date or ''}")
    if target_year_match:
        target_year = target_year_match.group(1)

    if target_year:
        ev_years = set(re.findall(r"\b(202[0-9])\b", ev_title.lower()))
        if ev_years and target_year not in ev_years:
            return False, f"Evidence references a different edition/year ({list(ev_years)[0]}) instead of target {target_year}."

    # Check 4: Opportunity disambiguation & generic root domain rejection
    if title_tokens:
        has_title_match = any(t in text_corpus for t in title_tokens)
        is_root = is_generic_root_url(ev_url)
        if is_root and not has_title_match:
            return False, "Generic homepage does not reference the target opportunity."
        has_org_match = bool(organizer_tokens and any(t in text_corpus for t in organizer_tokens))
        if not has_title_match and not (has_org_match and source_type == "official_organizer" and not is_root):
            return False, "Search result does not match distinct opportunity identifiers or organizer."

    return True, "Relevant external evidence."


def match_evidence_to_claims(
    ev_title: str,
    ev_snippet: str,
    ev_url: str,
    source_type: str,
    claims: list[ClaimItem],
    extracted: ExtractedStagePayload,
) -> list[str]:
    """Associate evidence with specific claims using strict substantive criteria across all opportunity types."""
    is_rel, _ = is_substantively_relevant(ev_title, ev_snippet, ev_url, source_type, extracted)
    if not is_rel:
        return []

    text_corpus = f"{ev_title} {ev_snippet} {ev_url}".lower()

    _title_str = extracted.title if isinstance(extracted.title, str) else ""
    _org_str = extracted.organizer if isinstance(extracted.organizer, str) else ""
    title_words = [
        w for w in re.findall(r"[a-z0-9]+", _title_str.lower())
        if len(w) >= 3 and w not in STOP and w not in GENERIC_OPPORTUNITY_TERMS
    ]
    org_words = [
        w for w in re.findall(r"[a-z0-9]+", _org_str.lower())
        if len(w) >= 3 and w not in STOP and _org_str not in ("", "Unverified organizer")
    ]

    matched_ids: list[str] = []
    for c in claims:
        if c.claim_type == "organizer":
            if extracted.organizer != "Unverified organizer" and (
                source_type == "official_organizer"
                or (org_words and any(t in text_corpus for t in org_words))
            ):
                matched_ids.append(c.claim_id)
        elif c.claim_type == "event":
            # Event claim must have title words in text or official organizer source discussing opportunity
            if title_words and any(t in text_corpus for t in title_words):
                matched_ids.append(c.claim_id)
            elif source_type == "official_organizer" and (org_words and any(t in text_corpus for t in org_words)):
                matched_ids.append(c.claim_id)
        elif c.claim_type == "deadline":
            deadline_terms = ["deadline", "last date", "apply by", "due date", "closes", "ends on", "submission", "closing date", "registration ends"]
            has_date = False
            if extracted.deadline.date and extracted.deadline.date in text_corpus:
                has_date = True
            elif extracted.deadline.raw:
                raw_toks = [w for w in re.findall(r"[a-z0-9]+", extracted.deadline.raw.lower()) if len(w) >= 2 and w not in STOP]
                if len(raw_toks) >= 2 and all(w in text_corpus for w in raw_toks):
                    has_date = True
            elif any(dt in text_corpus for dt in deadline_terms):
                has_date = True
            if has_date:
                matched_ids.append(c.claim_id)
        elif c.claim_type == "fee":
            fee_terms = ["fee", "registration", "charge", "free", "cost", "₹", "rs", "inr", "usd", "$", "tuition", "payment"]
            if any(ft in text_corpus for ft in fee_terms):
                matched_ids.append(c.claim_id)
        elif c.claim_type == "eligibility":
            elig_terms = ["eligibility", "eligible", "students", "criteria", "open to", "branches", "who can apply", "prerequisites", "qualifications", "cgpa", "degree", "branch"]
            if any(et in text_corpus for et in elig_terms):
                matched_ids.append(c.claim_id)
        elif c.claim_type == "reward":
            reward_terms = ["prize", "cash", "pool", "stipend", "reward", "lakh", "swags", "certificate", "salary", "grant", "funding", "scholarship", "allowance"]
            if any(rt in text_corpus for rt in reward_terms):
                matched_ids.append(c.claim_id)
        elif c.claim_type == "general":
            # General claim: matches if substantive words from the claim appear in evidence
            claim_toks = [w for w in re.findall(r"[a-z0-9]+", c.claim_text.lower()) if len(w) >= 3 and w not in STOP]
            if claim_toks and any(t in text_corpus for t in claim_toks):
                matched_ids.append(c.claim_id)

    return matched_ids


def _is_usable_url(u: Any) -> bool:
    """Validate that u is a usable external URL, rejecting None, 'none', 'null', and placeholders."""
    if not u or not isinstance(u, str):
        return False
    cleaned = u.strip().lower()
    if cleaned in ("none", "null", "n/a", "no", "false", "undefined", "http://none", "https://none", "none/", "null/"):
        return False
    if cleaned.startswith(("http://none", "https://none", "http://null", "https://null")):
        return False
    # Reject strings without a dot (no domain extension)
    if not re.search(r"^[a-zA-Z0-9+.-]+://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", cleaned) and not re.search(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", cleaned):
        return False
    return True


# --- STAGE 1: EXTRACTED ---
def run_extracted_stage(
    rvpack: RVPackData,
    llm_client: Any = None,
) -> ExtractedStagePayload:
    """Stage 1: Semantic extraction & claim decomposition via Gemini API (Call 1)."""
    meta_author = (
        rvpack.meta.get("author")
        or rvpack.meta.get("creator")
        or rvpack.meta.get("source")
        or rvpack.meta.get("account")
        or ""
    ).strip() or None
    meta_organizer = (rvpack.meta.get("organizer") or "").strip() or None

    prompt_sections = [
        "Analyze the following .rvpack opportunity package and provide structured claim analysis:\n",
        f"---TRANSCRIPT---\n{rvpack.transcript or '(None)'}\n",
        f"---ON_SCREEN---\n{rvpack.on_screen or '(None)'}\n",
        f"---META---\n{rvpack.meta or '(None)'}",
    ]
    # Only append raw text if none of the parsed sections contained content
    if not rvpack.transcript and not rvpack.on_screen and not rvpack.meta and rvpack.raw_text:
        prompt_sections.append(f"\n---RAW TEXT---\n{rvpack.raw_text}")

    prompt_user = "\n".join(prompt_sections)

    try:
        analysis: GeminiClaimAnalysis = _invoke_structured_llm(
            client=llm_client,
            schema=GeminiClaimAnalysis,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_user},
            ],
            fallback_kind="fast",
        )
    except AppError:
        raise
    except Exception as exc:
        is_transient, status_code, err_code, user_msg = _classify_gemini_error(exc)
        if is_transient:
            log.warning("Gemini claim analysis encountered transient error: %s", exc)
            raise AppError(user_msg, status=status_code, code=err_code) from exc
        log.exception("Gemini claim analysis call failed: %s", exc)
        raise RuntimeError(f"Gemini claim analysis failed: {exc}") from exc

    # Defensive guard: should never be None after _invoke_structured_llm (which now raises AppError
    # for None responses), but guard here as a belt-and-suspenders safety net.
    if analysis is None:
        raise AppError(
            "Gemini returned no structured analysis. Cannot proceed with verification.",
            status=422,
            code="malformed_model_output",
        )

    combined_text = f"{rvpack.transcript}\n{rvpack.on_screen}\n{rvpack.raw_text}"

    # 1. Author vs Organizer distinction
    # analysis.author is Optional[str]; meta_author may also be None when neither
    # the META section nor the model response provided a creator handle.
    analysis_author_raw = analysis.author
    if not isinstance(analysis_author_raw, str):
        analysis_author_raw = None
    author = meta_author or (analysis_author_raw.strip() if analysis_author_raw else None) or None
    organizer = (analysis.organizer if isinstance(analysis.organizer, str) else "").strip()
    if not organizer or organizer.lower() in _GENERIC_ACCOUNT_NAMES or (author and organizer.lower() == author.lower()):
        explicit_org = None
        for pat in [re.compile(r"(?:organized\s+by|organizer|conducted\s+by|presented\s+by|hosted\s+by)\s*[:\-\–]?\s*([A-Za-z0-9&.,'’\s]{2,60})", re.IGNORECASE)]:
            m = pat.search(combined_text)
            if m:
                cand = m.group(1).strip()
                cand = re.split(r"[,;.\n]|(?:\b(?:fee|deadline|apply|registration|register|prize|link|http)\b)", cand, flags=re.IGNORECASE)[0].strip()
                if cand and not cand.startswith(("@", "http://", "https://", "www.")) and cand.lower() not in _GENERIC_ACCOUNT_NAMES:
                    explicit_org = cand
                    break
        organizer = explicit_org or meta_organizer or "Unverified organizer"

    # 2. Deadline validation safeguard
    raw_deadline = analysis.deadline_raw
    deadline_date = analysis.deadline_date
    year_ambiguous = analysis.year_ambiguous
    ambiguity_reason = analysis.ambiguity_reason

    # Resolve deadline using contextual evidence and meta if deadline_date is missing or marked ambiguous
    deadline_provenance = None
    year_resolved_from = None

    if (not deadline_date or year_ambiguous) and (raw_deadline or combined_text):
        meta_context = dict(rvpack.meta or {})
        if "context_text" not in meta_context:
            meta_context["context_text"] = combined_text
        if "title" not in meta_context and analysis.title:
            meta_context["title"] = analysis.title
        parsed_dl = _parse_deadline(raw_deadline or combined_text, meta_context)
        if parsed_dl.date and not parsed_dl.year_ambiguous:
            deadline_date = parsed_dl.date
            raw_deadline = raw_deadline or parsed_dl.raw
            year_ambiguous = False
            ambiguity_reason = None
            deadline_provenance = parsed_dl.provenance
            year_resolved_from = parsed_dl.year_resolved_from
        else:
            deadline_provenance = parsed_dl.provenance
            year_resolved_from = parsed_dl.year_resolved_from

    if not raw_deadline and not deadline_date:
        meta_context = dict(rvpack.meta or {})
        if "context_text" not in meta_context:
            meta_context["context_text"] = combined_text
        if "title" not in meta_context and analysis.title:
            meta_context["title"] = analysis.title
        parsed_dl = _parse_deadline(combined_text, meta_context)
        deadline_info = parsed_dl
    else:
        is_valid_date = False
        if deadline_date and not year_ambiguous:
            try:
                datetime.strptime(deadline_date, "%Y-%m-%d")
                is_valid_date = True
                if not deadline_provenance:
                    deadline_provenance = "explicitly stated in source text"
                    year_resolved_from = "explicit date text"
            except ValueError:
                is_valid_date = False
                year_ambiguous = True
                ambiguity_reason = f"Invalid date format: {deadline_date}"
                deadline_date = None

        deadline_info = DeadlineInfo(
            raw=raw_deadline,
            date=deadline_date if is_valid_date else None,
            year_ambiguous=year_ambiguous,
            ambiguity_reason=ambiguity_reason,
            reminder_eligible=is_valid_date and not year_ambiguous,
            vault_reminder_status="ready_to_connect" if (is_valid_date and not year_ambiguous) else "not_connected",
            provenance=deadline_provenance,
            year_resolved_from=year_resolved_from,
        )

    # 3. Registration Fee neutral caution safeguard
    has_fee = bool(analysis.has_fee)
    is_fee_warning = bool(analysis.is_fee_warning)
    fee_raw = analysis.fee_raw
    fee_warning_message = analysis.fee_warning_message

    # Fallback fee detection if LLM missed it
    if not has_fee:
        fee_match = re.search(r"(?:₹|rs\.?|inr)\s*(\d+(?:,\d+)*(?:\.\d+)?)|(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:₹|rs\.?|inr|rupees)", combined_text, re.IGNORECASE)
        fee_kw = re.search(r"(?:fee|registration\s+fee|pay\s+(?:₹|rs\.?|inr)?\s*\d+|registration\s+charge|pay\s*₹?\d+)", combined_text, re.IGNORECASE)
        if fee_match and fee_kw:
            has_fee = True
            is_fee_warning = True
            if not fee_raw:
                fee_raw = fee_match.group(0).strip()

    if has_fee:
        is_fee_warning = True
        fee_warning_message = (
            f"Registration fee detected{f' ({fee_raw})' if fee_raw else ''}. "
            "Verify the organizer's identity, official event page, payment recipient, and refund policy before paying. "
            "A fee alone does not establish fraud."
        )

    # 4. URLs
    urls: list[str] = []
    seen_urls: set[str] = set()
    for u in (analysis.links or []):
        if not _is_usable_url(u):
            continue
        norm = u if u.startswith(("http://", "https://")) else f"https://{u}"
        if norm.lower() not in seen_urls:
            seen_urls.add(norm.lower())
            urls.append(norm)
    for m in _URL_REGEX.finditer(combined_text):
        u = m.group(0).rstrip(".,;:!?)'\"")
        if not _is_usable_url(u):
            continue
        norm = u if u.startswith(("http://", "https://")) else f"https://{u}"
        if norm.lower() not in seen_urls:
            seen_urls.add(norm.lower())
            urls.append(norm)
    meta_url = rvpack.meta.get("url") if isinstance(rvpack.meta, dict) else None
    if _is_usable_url(meta_url):
        norm = meta_url if meta_url.startswith(("http://", "https://")) else f"https://{meta_url}"
        if norm.lower() not in seen_urls:
            seen_urls.add(norm.lower())
            urls.append(norm)

    # 5. Claims list
    claims = analysis.claims or []
    if not claims:
        cid = 1
        if organizer and organizer != "Unverified organizer":
            claims.append(ClaimItem(claim_id=f"c{cid}", claim_text=f"The opportunity is organized by {organizer}.", claim_type="organizer"))
            cid += 1
        else:
            claims.append(ClaimItem(claim_id=f"c{cid}", claim_text="The opportunity organizer is unverified in the submitted announcement.", claim_type="organizer"))
            cid += 1
        claims.append(ClaimItem(claim_id=f"c{cid}", claim_text=f"Announces a {analysis.category} titled '{analysis.title}'.", claim_type="event"))
        cid += 1
        if deadline_info.raw:
            claims.append(ClaimItem(claim_id=f"c{cid}", claim_text=f"Application deadline is stated as '{deadline_info.raw}'.", claim_type="deadline"))
            cid += 1
        if has_fee:
            claims.append(ClaimItem(claim_id=f"c{cid}", claim_text=f"Registration fee of {fee_raw or 'required amount'} is charged.", claim_type="fee", is_fee_warning_claim=True))
            cid += 1

    # 6. Search queries (strictly bounded to max 2 targeted queries)
    search_queries = analysis.search_queries or []
    if not search_queries:
        target_org = organizer if organizer != "Unverified organizer" else ""
        search_queries = [f"{target_org} {analysis.title or 'opportunity'} official".strip()]
        if has_fee:
            search_queries.append(f"{target_org} {analysis.title or 'opportunity'} registration fee".strip())
    search_queries = search_queries[:2]

    return ExtractedStagePayload(
        title=(analysis.title if isinstance(analysis.title, str) else "").strip() or "Student Opportunity Announcement",
        organizer=organizer,
        author=author,
        category=(analysis.category if isinstance(analysis.category, str) else "").strip() or "other",
        deadline=deadline_info,
        fee_raw=fee_raw,
        has_fee=has_fee,
        is_fee_warning=is_fee_warning,
        fee_warning_message=fee_warning_message,
        eligibility=analysis.eligibility,
        reward_or_benefit=analysis.reward_or_benefit,
        mode=analysis.mode,
        location=None,
        links=urls,
        source_quotes=analysis.source_quotes or {},
        sections_found=rvpack.sections_found,
        search_queries=search_queries,
        claims=claims,
    )


# --- STAGE 2: CLAIMS ---
def run_claims_stage(
    extracted: ExtractedStagePayload,
    rvpack: RVPackData,
    llm_claims: list[ClaimItem] | None = None,
) -> ClaimsStagePayload:
    """Stage 2: Package decomposed factual claims from Call 1."""
    claims_list = llm_claims or extracted.claims
    return ClaimsStagePayload(
        claims=claims_list,
        total_claims=len(claims_list),
        contains_fee_claim=extracted.has_fee,
    )


# --- STAGE 3: EVIDENCE ---
def run_evidence_stage(
    claims: ClaimsStagePayload,
    extracted: ExtractedStagePayload,
    tavily_client: Any = None,
) -> EvidenceStagePayload:
    """Stage 3: Retrieve and filter external web evidence via Tavily search with bounded timeout."""
    evidence_items: list[EvidenceItem] = []
    queries_used: list[str] = []
    official_domains: list[str] = []
    seen_urls: set[str] = set()

    # Bound search queries to at most 2 targeted queries
    queries_to_run = (extracted.search_queries or [])[:2]
    if not queries_to_run:
        target_org = extracted.organizer if extracted.organizer != "Unverified organizer" else ""
        queries_to_run = [f"{target_org} {extracted.title} official".strip()]

    settings = get_settings()
    has_tavily = bool(tavily_client or settings.tavily_api_key)
    search_status = "unconfigured"
    search_notes: str | None = None

    if has_tavily:
        try:
            from tavily import TavilyClient
            client = tavily_client or TavilyClient(api_key=settings.tavily_api_key)

            for q in queries_to_run:
                queries_used.append(q)
                # Bounded timeout of 8.0s per Tavily search query
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    search_future = executor.submit(client.search, query=q, max_results=3, search_depth="basic")
                    try:
                        resp = search_future.result(timeout=8.0)
                    except concurrent.futures.TimeoutError:
                        log.warning("Tavily search query '%s' timed out; preserving already retrieved evidence.", q)
                        search_notes = "External search attempt failed due to timeout; partial evidence preserved."
                        continue
                    except Exception as err:
                        log.warning("Tavily search query '%s' failed (%s); continuing with existing evidence.", q, err)
                        search_notes = f"External search attempt failed with error ({err}); partial evidence preserved."
                        continue

                results = resp.get("results", []) if isinstance(resp, dict) else []
                for r in results:
                    u = r.get("url")
                    if not u or u in seen_urls:
                        continue
                    seen_urls.add(u)
                    cls_info = classify_source(u, extracted.organizer, extracted.title, category=extracted.category)

                    # Substantive relevance check: reject unrelated institutions and generic directories
                    is_rel, rel_reason = is_substantively_relevant(
                        ev_title=r.get("title") or "",
                        ev_snippet=r.get("content") or "",
                        ev_url=u,
                        source_type=cls_info["source_type"],
                        extracted=extracted,
                    )
                    if not is_rel:
                        log.info("Discarding non-relevant source %s: %s", u, rel_reason)
                        continue

                    if cls_info["source_type"] == "official_organizer":
                        official_domains.append(cls_info["domain"])

                    matched_claim_ids = match_evidence_to_claims(
                        ev_title=r.get("title") or "",
                        ev_snippet=r.get("content") or "",
                        ev_url=u,
                        source_type=cls_info["source_type"],
                        claims=claims.claims,
                        extracted=extracted,
                    )

                    evidence_items.append(
                        EvidenceItem(
                            id=f"ev_{len(evidence_items)+1}",
                            claim_ids=matched_claim_ids,
                            url=u,
                            title=r.get("title") or "Search Result",
                            snippet=(r.get("content") or "")[:350],
                            domain=cls_info["domain"],
                            domain_trust=cls_info["domain_trust"],
                            source_type=cls_info["source_type"],
                            source_label=cls_info["source_label"],
                            retrieved_at=datetime.now(timezone.utc).isoformat(),
                        )
                    )

            if not search_notes:
                search_status = "completed" if queries_used else "no_results"
                search_notes = f"External web search executed with {len(queries_used)} query/queries."
            else:
                search_status = "completed" if evidence_items else "failed"

        except Exception as exc:
            log.warning("Evidence search via Tavily failed (%s); external corroboration was unavailable.", exc)
            search_status = "failed"
            search_notes = f"External search attempt failed ({exc}); external corroboration was unavailable."
    else:
        search_status = "unconfigured"
        search_notes = "External search credentials not configured; external web corroboration was unavailable."

    # Record submitted links from the package (deterministic recording, clearly marked as extracted source links)
    for u in extracted.links:
        if u not in seen_urls:
            seen_urls.add(u)
            cls_info = classify_source(u, extracted.organizer, extracted.title, category=extracted.category)
            if cls_info["source_type"] == "official_organizer":
                official_domains.append(cls_info["domain"])

            matched_claim_ids = match_evidence_to_claims(
                ev_title=f"Source link: {cls_info['domain']}",
                ev_snippet=f"Direct link submitted in announcement for '{extracted.title}'.",
                ev_url=u,
                source_type=cls_info["source_type"],
                claims=claims.claims,
                extracted=extracted,
            )

            evidence_items.append(
                EvidenceItem(
                    id=f"ev_{len(evidence_items)+1}",
                    claim_ids=matched_claim_ids,
                    url=u,
                    title=f"Extracted Source Link: {cls_info['domain']}",
                    snippet=f"Link submitted in announcement. Source type: {cls_info['source_label']}.",
                    domain=cls_info["domain"],
                    domain_trust=cls_info["domain_trust"],
                    source_type=cls_info["source_type"],
                    source_label=cls_info["source_label"],
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                )
            )

    return EvidenceStagePayload(
        evidence_items=evidence_items,
        queries_used=queries_used,
        official_domains=list(dict.fromkeys(official_domains)),
        search_status=search_status,
        search_notes=search_notes,
    )


# --- STAGE 4: VERDICT ---
def run_verdict_stage(
    claims: ClaimsStagePayload,
    evidence: EvidenceStagePayload,
    extracted: ExtractedStagePayload,
    llm_client: Any = None,
) -> VerdictStagePayload:
    """Stage 4: Grounded evidence evaluation and verdict generation via Gemini API (Call 2)."""
    claims_text_lines = []
    for c in claims.claims:
        claims_text_lines.append(f"- ID: {c.claim_id} | Type: {c.claim_type} | Text: {c.claim_text}")
    claims_formatted = "\n".join(claims_text_lines)

    ev_text_lines = []
    supplied_urls = set()
    for e in evidence.evidence_items:
        supplied_urls.add(e.url)
        ev_text_lines.append(
            f"- ID: {e.id} | URL: {e.url} | Domain: {e.domain} | Source Type: {e.source_type} | Title: {e.title}\n  Snippet: {e.snippet}"
        )
    evidence_formatted = "\n".join(ev_text_lines) if ev_text_lines else "No external search evidence retrieved."

    user_prompt = (
        f"Evaluate the following claims against the provided evidence:\n\n"
        f"---EXTRACTED OPPORTUNITY---\n"
        f"Title: {extracted.title}\n"
        f"Organizer: {extracted.organizer}\n"
        f"Author (Social Creator): {extracted.author}\n"
        f"Category: {extracted.category}\n"
        f"Deadline: {extracted.deadline.raw} (ISO: {extracted.deadline.date}, Ambiguous: {extracted.deadline.year_ambiguous})\n"
        f"Has Fee: {extracted.has_fee} (Raw: {extracted.fee_raw})\n\n"
        f"---CLAIMS TO EVALUATE---\n{claims_formatted}\n\n"
        f"---RETRIEVED EVIDENCE (ONLY CITE THESE SOURCES)---\n{evidence_formatted}\n\n"
        f"Search Status: {evidence.search_status}\n"
        f"Search Notes: {evidence.search_notes}\n\n"
        f"Output requirement: Return valid JSON containing 'claim_verdicts', 'overall_verdict', and 'summary'."
    )

    try:
        evaluation: GeminiVerdictEvaluation = _invoke_structured_llm(
            client=llm_client,
            schema=GeminiVerdictEvaluation,
            messages=[
                {"role": "system", "content": VERDICT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            fallback_kind="main",
        )
    except AppError:
        raise
    except Exception as exc:
        is_transient, status_code, err_code, user_msg = _classify_gemini_error(exc)
        if is_transient:
            log.warning("Gemini verdict evaluation encountered transient error: %s", exc)
            raise AppError(user_msg, status=status_code, code=err_code) from exc
        log.exception("Gemini verdict evaluation call failed: %s", exc)
    if evaluation is None:
        raise AppError(
            "Gemini returned no structured verdict evaluation. Cannot proceed with verification.",
            status=422,
            code="malformed_model_output",
        )

    # Citation safety filter: only URLs actually supplied to the model are allowed
    cleaned_claim_verdicts: list[ClaimVerdictItem] = []
    for cv in (evaluation.claim_verdicts or []):
        valid_citations = [u for u in cv.cited_sources if u in supplied_urls]
        cleaned_claim_verdicts.append(
            ClaimVerdictItem(
                claim_id=cv.claim_id,
                claim_text=cv.claim_text,
                verdict=cv.verdict,
                explanation=cv.explanation,
                cited_sources=valid_citations,
                is_fee_warning_claim=cv.is_fee_warning_claim,
            )
        )

    # Ensure all claims from stage 2 are accounted for
    evaluated_claim_ids = {cv.claim_id for cv in cleaned_claim_verdicts}
    for c in claims.claims:
        if c.claim_id not in evaluated_claim_ids:
            cleaned_claim_verdicts.append(
                ClaimVerdictItem(
                    claim_id=c.claim_id,
                    claim_text=c.claim_text,
                    verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
                    explanation="External evidence was insufficient to corroborate or contradict this claim.",
                    cited_sources=[],
                    is_fee_warning_claim=c.is_fee_warning_claim,
                )
            )

    # Fee neutral caution safeguard
    scam_warnings = list(evaluation.scam_warnings or [])
    has_scam_warning = bool(evaluation.has_scam_warning or extracted.has_fee)
    if extracted.has_fee:
        neutral_caution = (
            f"Registration fee detected{f' ({extracted.fee_raw})' if extracted.fee_raw else ''}. "
            "Verify the organizer's identity, official event page, payment recipient, and refund policy before paying. "
            "A fee alone does not establish fraud."
        )
        if not any("registration fee detected" in w.lower() for w in scam_warnings):
            scam_warnings.insert(0, neutral_caution)

    fraudulent_detected = bool(evaluation.fraudulent_detected)
    if not any(cv.verdict == ClaimVerdictLabel.CONTRADICTED for cv in cleaned_claim_verdicts):
        fraudulent_detected = False

    has_search = evidence.search_status == "completed" and len(evidence.queries_used) > 0
    verification_method = "Gemini AI analysis + web search" if has_search else "Gemini AI analysis only (external web search unavailable)"

    return VerdictStagePayload(
        claim_verdicts=cleaned_claim_verdicts,
        overall_verdict=evaluation.overall_verdict,
        summary=evaluation.summary,
        verification_method=verification_method,
        scam_warnings=scam_warnings,
        has_scam_warning=has_scam_warning,
        fraudulent_detected=fraudulent_detected,
    )


# --- STAGE 5: CARD ---
def run_card_stage(
    run_id: str,
    stages_records: list[dict] | None = None,
    user_id: str = "",
    user_reel_id: int | None = None,
) -> OpportunityCardPayload:
    """Stage 5: Create Opportunity Card only after the first four stages are successfully persisted."""
    persisted = verification_repo.list_stages(run_id)
    records_to_check = persisted if persisted else (stages_records or [])
    persisted_stage_names = {s["stage_name"] for s in records_to_check if s.get("status") == "completed"}
    required_prereqs = {StageName.EXTRACTED.value, StageName.CLAIMS.value, StageName.EVIDENCE.value, StageName.VERDICT.value}

    missing_prereqs = required_prereqs - persisted_stage_names
    if missing_prereqs:
        raise ValueError(
            f"Cannot create Card stage: prerequisite stages {sorted(missing_prereqs)} are not yet persisted for run {run_id}."
        )

    stage_map = {s["stage_name"]: s.get("payload", {}) for s in records_to_check}
    extracted_data = stage_map[StageName.EXTRACTED.value]
    evidence_data = stage_map.get(StageName.EVIDENCE.value, {})
    verdict_data = stage_map[StageName.VERDICT.value]

    deadline_raw = extracted_data.get("deadline", {})
    deadline_info = DeadlineInfo(**deadline_raw) if isinstance(deadline_raw, dict) else DeadlineInfo()

    overall_verdict = ClaimVerdictLabel(verdict_data.get("overall_verdict", ClaimVerdictLabel.INSUFFICIENT_EVIDENCE.value))
    scam_warnings = verdict_data.get("scam_warnings", [])

    evidence_items = evidence_data.get("evidence_items", [])
    official_urls = {
        e.get("url") for e in evidence_items
        if e.get("source_type") in {"official_organizer", "trusted_institution"}
        and e.get("domain_trust") in {"official_match", "high"}
        and not is_generic_root_url(e.get("url", ""))
    }
    claims_summary = [ClaimVerdictItem(**cv) for cv in verdict_data.get("claim_verdicts", [])]

    # Evaluate candidate official registration link
    title_str = extracted_data.get("title") or ""
    org_str = extracted_data.get("organizer") or ""
    cat_str = extracted_data.get("category") or ""
    candidate_links = list(extracted_data.get("links", []))
    for ev in evidence_items:
        u = ev.get("url") if isinstance(ev, dict) else getattr(ev, "url", None)
        if u and u not in candidate_links:
            candidate_links.append(u)

    official_reg_url = None
    official_reg_status = "not_found"
    for cand in candidate_links:
        is_reg, status, _ = verify_official_registration_link(
            cand, organizer=org_str, title=title_str, category=cat_str, evidence_items=evidence_items
        )
        if is_reg:
            official_reg_url = cand
            official_reg_status = "verified"
            break

    if not official_reg_url:
        if candidate_links:
            official_reg_status = "unable_to_verify"
        else:
            official_reg_status = "not_found"

    # Separate supporting evidence links
    supporting_links = []
    seen_links = set()
    if official_reg_url:
        seen_links.add(official_reg_url.lower())

    for ev in evidence_items:
        u = ev.get("url") if isinstance(ev, dict) else getattr(ev, "url", None)
        if u and u.lower() not in seen_links and not is_generic_root_url(u) and "google.com" not in u.lower():
            seen_links.add(u.lower())
            supporting_links.append(u)

    for lk in extracted_data.get("links", []):
        if lk and lk.lower() not in seen_links and not is_generic_root_url(lk) and "google.com" not in lk.lower():
            seen_links.add(lk.lower())
            supporting_links.append(lk)

    # Core claims must be supported AND supported by an official primary source
    core_claims_officially_supported = any(
        cv.verdict == ClaimVerdictLabel.SUPPORTED
        and any(u in official_urls for u in cv.cited_sources)
        for cv in claims_summary
    )

    any_claim_supported = any(cv.verdict in {ClaimVerdictLabel.SUPPORTED, ClaimVerdictLabel.PARTIALLY_SUPPORTED} for cv in claims_summary)
    fraudulent_detected = bool(verdict_data.get("fraudulent_detected", False))

    # Strictly assign badge based on actual evidence
    if overall_verdict == ClaimVerdictLabel.CONTRADICTED or fraudulent_detected:
        badge = "CONTRADICTED"
    elif overall_verdict == ClaimVerdictLabel.SUPPORTED and bool(official_urls) and core_claims_officially_supported:
        badge = "OFFICIAL CORROBORATED"
    elif any_claim_supported and overall_verdict in {ClaimVerdictLabel.SUPPORTED, ClaimVerdictLabel.PARTIALLY_SUPPORTED}:
        badge = "PARTIALLY SUPPORTED"
    else:
        badge = "UNVERIFIED / INSUFFICIENT EVIDENCE"

    can_save_reminder = deadline_info.reminder_eligible and bool(deadline_info.date)
    reminder_action = None
    if can_save_reminder:
        reminder_action = {
            "reel_id": user_reel_id,
            "label": f"Deadline: {extracted_data.get('title', 'Opportunity')}",
            "event_date": deadline_info.date,
        }

    return OpportunityCardPayload(
        card_id=f"card_{run_id}",
        run_id=run_id,
        user_reel_id=user_reel_id,
        title=extracted_data.get("title") or "Opportunity Card",
        organizer=extracted_data.get("organizer") or "Unverified organizer",
        author=extracted_data.get("author"),
        category=extracted_data.get("category") or "other",
        overall_verdict=overall_verdict,
        badge=badge,
        verification_method=verdict_data.get("verification_method", "Gemini AI analysis only"),
        scam_warnings=scam_warnings,
        claims_summary=claims_summary,
        official_links=[official_reg_url] if official_reg_url else [],
        official_registration_url=official_reg_url,
        official_registration_status=official_reg_status,
        supporting_links=supporting_links,
        deadline=deadline_info,
        can_save_reminder=can_save_reminder,
        vault_reminder_action=reminder_action,
        stages_verified=[
            StageName.EXTRACTED.value,
            StageName.CLAIMS.value,
            StageName.EVIDENCE.value,
            StageName.VERDICT.value,
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# --- ORCHESTRATOR ---
def execute_run(
    run_id: str,
    user_id: str,
    tavily_client: Any = None,
    llm_client: Any = None,
) -> dict:
    """Execute or resume the 5-stage verification workflow.
    
    1. Extracted (Gemini Call 1)
    2. Claims (Decomposed claims from Call 1)
    3. Evidence (Tavily search via generated queries)
    4. Verdict (Gemini Call 2)
    5. Card (Opportunity Card from 4 persisted stages)
    
    Resumes from the last completed stage without duplicating completed records or repeating paid LLM calls.
    Short-circuits immediately if run is already completed.
    """
    run = verification_repo.get_run(run_id, user_id)
    if not run:
        raise ValueError(f"Verification run {run_id} not found.")

    # Short-circuit: if run is already completed, return immediately without duplicate work
    if run.get("status") == "completed":
        final_stages = verification_repo.list_stages(run_id)
        card_stage = next((s for s in final_stages if s["stage_name"] == StageName.CARD.value and s.get("status") == "completed"), None)
        return {
            "id": run["id"],
            "user_id": run["user_id"],
            "user_reel_id": run.get("user_reel_id"),
            "input_type": run.get("input_type", "rvpack"),
            "status": "completed",
            "current_stage": "completed",
            "completed_stages": [s["stage_name"] for s in final_stages if s.get("status") == "completed"],
            "stages": final_stages,
            "card": card_stage["payload"] if card_stage else None,
            "created_at": run["created_at"],
            "updated_at": run["updated_at"],
        }

    rvpack_data = parse_rvpack(run["raw_input"])
    existing_stages = verification_repo.list_stages(run_id)
    stage_by_name = {s["stage_name"]: s for s in existing_stages if s.get("status") == "completed"}

    try:
        # --- STAGE 1: Extracted ---
        if StageName.EXTRACTED.value not in stage_by_name:
            verification_repo.update_run(run_id, current_stage=StageName.EXTRACTED.value)
            extracted_payload = run_extracted_stage(rvpack_data, llm_client=llm_client)
            saved = verification_repo.save_stage(
                run_id=run_id,
                stage_name=StageName.EXTRACTED.value,
                stage_order=STAGE_ORDER_MAP[StageName.EXTRACTED.value],
                payload=extracted_payload.model_dump(mode="json"),
                status="completed",
            )
            stage_by_name[StageName.EXTRACTED.value] = saved

        extracted_obj = ExtractedStagePayload(**stage_by_name[StageName.EXTRACTED.value]["payload"])

        # --- STAGE 2: Claims ---
        if StageName.CLAIMS.value not in stage_by_name:
            verification_repo.update_run(run_id, current_stage=StageName.CLAIMS.value)
            claims_payload = run_claims_stage(extracted_obj, rvpack_data)
            saved = verification_repo.save_stage(
                run_id=run_id,
                stage_name=StageName.CLAIMS.value,
                stage_order=STAGE_ORDER_MAP[StageName.CLAIMS.value],
                payload=claims_payload.model_dump(mode="json"),
                status="completed",
            )
            stage_by_name[StageName.CLAIMS.value] = saved

        claims_obj = ClaimsStagePayload(**stage_by_name[StageName.CLAIMS.value]["payload"])

        # --- STAGE 3: Evidence ---
        if StageName.EVIDENCE.value not in stage_by_name:
            verification_repo.update_run(run_id, current_stage=StageName.EVIDENCE.value)
            evidence_payload = run_evidence_stage(claims_obj, extracted_obj, tavily_client=tavily_client)
            saved = verification_repo.save_stage(
                run_id=run_id,
                stage_name=StageName.EVIDENCE.value,
                stage_order=STAGE_ORDER_MAP[StageName.EVIDENCE.value],
                payload=evidence_payload.model_dump(mode="json"),
                status="completed",
            )
            stage_by_name[StageName.EVIDENCE.value] = saved

        evidence_obj = EvidenceStagePayload(**stage_by_name[StageName.EVIDENCE.value]["payload"])

        # --- STAGE 4: Verdict ---
        if StageName.VERDICT.value not in stage_by_name:
            verification_repo.update_run(run_id, current_stage=StageName.VERDICT.value)
            verdict_payload = run_verdict_stage(claims_obj, evidence_obj, extracted_obj, llm_client=llm_client)
            saved = verification_repo.save_stage(
                run_id=run_id,
                stage_name=StageName.VERDICT.value,
                stage_order=STAGE_ORDER_MAP[StageName.VERDICT.value],
                payload=verdict_payload.model_dump(mode="json"),
                status="completed",
            )
            stage_by_name[StageName.VERDICT.value] = saved

        # --- STAGE 5: Card ---
        all_persisted_stages = verification_repo.list_stages(run_id)
        persisted_names = {s["stage_name"] for s in all_persisted_stages if s.get("status") == "completed"}
        required_prereqs = [StageName.EXTRACTED.value, StageName.CLAIMS.value, StageName.EVIDENCE.value, StageName.VERDICT.value]
        missing = [req for req in required_prereqs if req not in persisted_names]
        if missing:
            raise RuntimeError(
                f"Cannot progress to Card stage: prerequisite stages {missing} are not persisted for run {run_id}."
            )

        if StageName.CARD.value not in stage_by_name:
            verification_repo.update_run(run_id, current_stage=StageName.CARD.value)
            card_payload = run_card_stage(
                run_id=run_id,
                stages_records=all_persisted_stages,
                user_id=user_id,
                user_reel_id=run.get("user_reel_id"),
            )
            saved = verification_repo.save_stage(
                run_id=run_id,
                stage_name=StageName.CARD.value,
                stage_order=STAGE_ORDER_MAP[StageName.CARD.value],
                payload=card_payload.model_dump(mode="json"),
                status="completed",
            )
            stage_by_name[StageName.CARD.value] = saved

        # Mark run complete
        verification_repo.update_run(run_id, status="completed", current_stage="completed")
    except Exception as exc:
        verification_repo.update_run(run_id, status="failed", error_message=str(exc))
        raise
    updated_run = verification_repo.get_run(run_id, user_id)
    final_stages = verification_repo.list_stages(run_id)

    card_record = stage_by_name.get(StageName.CARD.value)
    card_dict = card_record["payload"] if card_record else None

    return {
        "id": updated_run["id"],
        "user_id": updated_run["user_id"],
        "user_reel_id": updated_run.get("user_reel_id"),
        "input_type": updated_run.get("input_type", "rvpack"),
        "status": updated_run["status"],
        "current_stage": updated_run["current_stage"],
        "completed_stages": [s["stage_name"] for s in final_stages if s.get("status") == "completed"],
        "stages": final_stages,
        "card": card_dict,
        "created_at": updated_run["created_at"],
        "updated_at": updated_run["updated_at"],
    }


def connect_deadline_to_vault(
    run_id: str,
    user_id: str,
    reel_id: int | None = None,
    label: str | None = None,
    explicit_date: str | None = None,
) -> dict:
    """Connect verified application deadline to Vault reminder (user_saved_dates)."""
    card_stage = verification_repo.get_stage(run_id, StageName.CARD.value)
    if not card_stage:
        raise ValueError(f"Card stage not found for run {run_id}. Run must complete before setting reminder.")

    card_data = card_stage["payload"]
    deadline = DeadlineInfo(**(card_data.get("deadline") or {}))

    target_date = explicit_date or deadline.date
    if not target_date:
        if deadline.year_ambiguous:
            raise ValueError(
                "Cannot connect reminder: Application deadline year is ambiguous in the source. "
                "Explicit date (YYYY-MM-DD) must be confirmed by user."
            )
        raise ValueError("No valid date extracted to set reminder.")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", target_date):
        raise ValueError(f"Invalid date format '{target_date}'. Expected YYYY-MM-DD.")
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid calendar date '{target_date}'.")

    run = verification_repo.get_run(run_id, user_id)
    if not run:
        raise ValueError(f"Verification run {run_id} not found for user {user_id}.")

    if reel_id is not None:
        user_reel = None
        try:
            user_reel = main_repo.get_user_reel(user_id, reel_id)
        except Exception as exc:
            log.warning("Could not verify reel ownership (%s)", exc)
        if not user_reel:
            raise PermissionError(f"Reel {reel_id} not found or does not belong to user {user_id}.")
        target_reel_id = reel_id
    else:
        target_reel_id = run.get("user_reel_id")
        if target_reel_id:
            try:
                user_reel = main_repo.get_user_reel(user_id, target_reel_id)
                if not user_reel:
                    target_reel_id = None
            except Exception:
                pass

    if not target_reel_id:
        try:
            from app.schemas.domain import FetchedPost, PostRef
            short_id = str(run_id).replace("-", "")[:8]
            card_title = card_data.get("title") or "Opportunity"
            ref = PostRef(
                platform="instagram",
                shortcode=f"rv_{short_id}",
                canonical_url=f"https://reelvault.app/run/{run_id}",
            )
            f = FetchedPost(
                platform="instagram",
                shortcode=f"rv_{short_id}",
                author=card_data.get("organizer"),
                transcript=card_title,
                caption=label or f"Deadline: {card_title}",
                raw={
                    "custom_title": card_title,
                    "reel_analysis": {
                        "title": card_title,
                        "summary": card_title,
                        "tags": [card_data.get("category") or "opportunity"],
                    },
                },
            )
            post = main_repo.insert_source_post(f, ref)
            linked = main_repo.link_user_reel(user_id, post["id"])
            target_reel_id = linked["id"]
            verification_repo.update_run(run_id, user_reel_id=target_reel_id)
        except Exception as exc:
            log.warning("Could not auto-link reel for reminder (%s)", exc)

    reminder_label = label or f"Deadline: {card_data.get('title', 'Opportunity')}"
    saved_record = None

    if target_reel_id:
        existing_dates = main_repo.list_saved_dates(user_id)
        for d in existing_dates:
            if (
                str(d.get("event_date")) == target_date
                and d.get("user_reel_id") == target_reel_id
            ):
                saved_record = d
                break
        if not saved_record:
            try:
                saved_record = main_repo.save_date(user_id, target_reel_id, reminder_label.strip(), target_date)
            except Exception as exc:
                log.error("Could not persist to user_saved_dates (%s)", exc)
                raise AppError(f"Database persistence failed: {exc}", status=500, code="db_persistence_failed")
    else:
        raise AppError("Could not establish target reel identity to persist calendar reminder.", status=500, code="reel_link_failed")

    if not saved_record or not saved_record.get("id"):
        raise AppError("Database persistence failed: saved date record was not created.", status=500, code="persistence_failed")

    card_data["deadline"]["vault_reminder_status"] = "connected"
    card_data["deadline"]["date"] = target_date
    card_data["deadline"]["year_ambiguous"] = False
    card_data["can_save_reminder"] = True
    verification_repo.save_stage(
        run_id,
        StageName.CARD.value,
        STAGE_ORDER_MAP[StageName.CARD.value],
        card_data,
        status="completed",
    )

    return {
        "success": True,
        "saved_date_id": saved_record.get("id"),
        "reel_id": target_reel_id,
        "label": reminder_label,
        "event_date": target_date,
        "status": "connected",
        "message": f"Deadline reminder successfully connected to Vault for {target_date}.",
    }


def save_opportunity_card_to_vault(run_id: str, user_id: str) -> dict:
    """Persist the complete Stage 5 opportunity card to the Vault shelf.
    
    Requirements:
    - Run must belong to authenticated user.
    - All first four stages must be complete, and card stage must exist and be completed.
    - Persists complete Opportunity Card: title, category, organizer, deadline, overall verdict,
      claim verdicts, evidence/sources, warnings.
    - Succeeds even if no deadline exists.
    - Idempotent: repeated requests for the same run return the same saved opportunity without duplicates.
    - Does NOT create a calendar event in user_saved_dates.
    """
    run = verification_repo.get_run(run_id)
    if not run:
        raise AppError("Verification run not found.", status=404, code="not_found")
    if str(run.get("user_id")) != str(user_id):
        raise PermissionError(f"Verification run {run_id} does not belong to user {user_id}.")

    stages = verification_repo.list_stages(run_id)
    completed_stages = {s["stage_name"] for s in stages if s.get("status") == "completed"}
    required_stages = {"extracted", "claims", "evidence", "verdict", "card"}
    missing = required_stages - completed_stages
    if missing:
        raise ValueError(
            f"Cannot save to Vault: verification run is incomplete. Missing completed stages: {', '.join(sorted(missing))}."
        )

    card_stage = verification_repo.get_stage(run_id, StageName.CARD.value)
    if not card_stage or not card_stage.get("payload"):
        raise ValueError("Cannot save to Vault: Card stage payload is missing.")
    card_data = card_stage["payload"]

    verdict_stage = verification_repo.get_stage(run_id, StageName.VERDICT.value)
    verdict_data = (verdict_stage.get("payload") if verdict_stage else {}) or {}

    evidence_stage = verification_repo.get_stage(run_id, StageName.EVIDENCE.value)
    evidence_data = (evidence_stage.get("payload") if evidence_stage else {}) or {}

    card_title = (card_data.get("title") or "Opportunity").strip()
    organizer = (card_data.get("organizer") or "Organizer").strip()
    category = (card_data.get("category") or "opportunity").strip()
    deadline_dict = card_data.get("deadline") or {}
    deadline_date = deadline_dict.get("date")
    deadline_raw = deadline_dict.get("raw")

    overall_verdict = card_data.get("overall_verdict") or verdict_data.get("overall_verdict") or "supported"
    claim_verdicts = verdict_data.get("claim_verdicts") or []
    evidence_items = evidence_data.get("evidence") or []
    scam_warnings = card_data.get("scam_warnings") or []

    # Gather links and sources
    links = []
    if card_data.get("links"):
        for l in card_data["links"]:
            if isinstance(l, dict) and l.get("url"):
                links.append({"name": l.get("name") or "Portal", "url": l["url"]})
            elif isinstance(l, str) and l.startswith("http"):
                links.append({"name": "Portal", "url": l})
    for ev in evidence_items:
        if isinstance(ev, dict) and ev.get("url"):
            title_lbl = ev.get("title") or ev.get("domain") or "Verified Evidence"
            if not any(item["url"] == ev["url"] for item in links):
                links.append({"name": title_lbl, "url": ev["url"]})

    extracted_dates = []
    if deadline_date or deadline_raw:
        extracted_dates.append({
            "label": f"Deadline: {card_title}",
            "date": deadline_raw or deadline_date,
            "iso_date": deadline_date,
            "url": links[0]["url"] if links else None,
        })

    reel_analysis = {
        "title": card_title,
        "summary": verdict_data.get("summary") or f"{card_title} organized by {organizer}.",
        "tags": [category.lower(), "opportunity", "verified"],
        "is_opportunity": True,
        "details": {
            "dates": [deadline_date] if deadline_date else ([deadline_raw] if deadline_raw else []),
            "competitions": [card_title] if category.lower() in ("hackathon", "competition") else [],
        },
        "extracted_dates": extracted_dates,
        "explore": {
            "organizer": organizer,
            "category": category.capitalize(),
            "benefits": "Verified opportunity",
            "location": "Online / Global",
        },
        "sources": links,
        "resources": [{"label": l.get("name") or "Portal", "url": l["url"]} for l in links if l.get("url")],
        "overall_verdict": overall_verdict,
        "claim_verdicts": claim_verdicts,
        "evidence": evidence_items,
        "scam_warnings": scam_warnings,
        "card": card_data,
    }

    target_reel_id = run.get("user_reel_id")
    if target_reel_id:
        existing_reel = None
        try:
            existing_reel = main_repo.get_user_reel(user_id, target_reel_id)
        except Exception as exc:
            log.warning("Could not check existing user reel (%s)", exc)
        if existing_reel:
            try:
                post_id = existing_reel.get("source_post_id")
                if post_id:
                    main_repo.update_source_post_analysis(post_id, analysis=reel_analysis)
            except Exception:
                pass
            return {
                "success": True,
                "reel_id": existing_reel["id"],
                "title": card_title,
                "already_saved": True,
                "message": f"Opportunity '{card_title}' is already saved in your Vault.",
            }

    from app.schemas.domain import FetchedPost, PostRef

    short_id = str(run_id).replace("-", "")[:8]
    ref = PostRef(
        platform="instagram",
        shortcode=f"rv_{short_id}",
        canonical_url=f"https://reelvault.app/run/{run_id}",
    )
    f = FetchedPost(
        platform="instagram",
        shortcode=f"rv_{short_id}",
        author=organizer,
        transcript=run.get("raw_input") or card_title,
        caption=card_title,
        raw={
            "custom_title": card_title,
            "reel_analysis": reel_analysis,
            "verification_run_id": str(run_id),
        },
    )
    post = main_repo.insert_source_post(f, ref)
    linked = main_repo.link_user_reel(user_id, post["id"])
    target_reel_id = linked["id"]
    verification_repo.update_run(run_id, user_reel_id=target_reel_id)

    return {
        "success": True,
        "reel_id": target_reel_id,
        "title": card_title,
        "already_saved": False,
        "message": f"'{card_title}' saved to Vault successfully.",
    }

