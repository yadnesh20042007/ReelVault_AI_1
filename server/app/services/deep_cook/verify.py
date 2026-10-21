from langchain_core.messages import HumanMessage

from app.config import get_settings
from app.errors import PipelineError
from app.llm import get_llm
from app.schemas.domain import ClaimCheck, Extracted, Verdict, VerdictDraft, VerificationResult
from app.services.deep_cook import prompts as P
from app.services.deep_cook.ground import contains
from app.services.deep_cook.tool_loop import LoopStats, gather_evidence
from app.services.tools.toolkit import ToolRun, build_tools


def verify(
    ex: Extracted,
    run: ToolRun,
    *,
    summary: str | None = None,
    summary_points: list[str] | None = None,
    topics: list[str] | None = None,
    tools_factory=build_tools,
) -> tuple[VerificationResult, LoopStats]:
    s = get_settings()
    llm = get_llm("main")

    parts: list[str] = [
        "Verify this claimed opportunity, reel summary, and topics using web search:",
        P.wrap("claim", ex.model_dump_json(exclude_none=True, indent=2)),
    ]
    if summary and summary.strip():
        parts.append(f"Reel Summary to verify:\n{summary.strip()}")
    if summary_points:
        clean_pts = [p.strip() for p in summary_points if isinstance(p, str) and p.strip()]
        if clean_pts:
            parts.append("Key Summary Points:\n" + "\n".join(f"- {p}" for p in clean_pts))
    if topics:
        clean_topics = [t.strip() for t in topics if isinstance(t, str) and t.strip()]
        if clean_topics:
            parts.append("Topics to verify:\n" + ", ".join(clean_topics))

    prompt_text = "\n\n".join(parts)

    messages, stats = gather_evidence(
        llm,
        tools_factory(run),
        P.GATHER_SYSTEM,
        prompt_text,
        max_calls=s.verify_max_tool_calls,
        timeout_s=s.verify_timeout_s,
    )
    if stats.calls > 0 and stats.ok == 0:
        raise PipelineError("search_unavailable")
    draft = llm.with_structured_output(VerdictDraft).invoke(messages + [HumanMessage(P.JUDGE_PROMPT)])
    return apply_guard(draft, run, ex, summary=summary, summary_points=summary_points, topics=topics), stats


def apply_guard(
    draft: VerdictDraft,
    run: ToolRun,
    ex: Extracted,
    summary: str | None = None,
    summary_points: list[str] | None = None,
    topics: list[str] | None = None,
) -> VerificationResult:
    """Deterministic. The LLM proposes; code disposes. When unsure, DOWNGRADE."""
    notes: list[str] = []
    verdict = draft.verdict
    official = [u for u in dict.fromkeys(draft.official_urls) if u in run.pages]
    support = [u for u in dict.fromkeys(draft.supporting_urls) if u in run.seen_urls]
    if len(official) < len(set(draft.official_urls)):
        notes.append("dropped official_urls that were not read in this run")

    def page_has_identity(u: str) -> bool:
        return any(contains(run.pages[u], v) for v in (ex.title.value, ex.organizer.value) if v)

    if verdict == Verdict.OFFICIAL_CONFIRMED:
        ok = [u for u in official if run.domain_checks.get(u, {}).get("plausibly_official") and page_has_identity(u)]
        if not ok:
            verdict = Verdict.FOUND_UNOFFICIAL if (official or support) else Verdict.NOT_FOUND
            notes.append("downgraded: no plausibly-official page (read) containing title/organizer")
        official = ok

    official_deadline = None
    if (
        official
        and draft.official_deadline
        and draft.official_deadline_quote
        and any(contains(run.pages[u], draft.official_deadline_quote) for u in official)
    ):
        official_deadline = draft.official_deadline
        if verdict == Verdict.OFFICIAL_CONFIRMED and ex.deadline.value and ex.deadline.value != official_deadline:
            verdict = Verdict.CONFLICTING
            notes.append("deadline differs from the official source; official date preferred")

    field_status: dict[str, str] = {}
    for fc in draft.field_checks:
        grounded = bool(fc.official_value) and any(contains(run.pages[u], fc.official_value) for u in official)
        field_status[fc.field] = fc.status if (fc.status != "matched" or grounded) else "unverified"

    if verdict == Verdict.SUSPICIOUS and not draft.scam_signals:
        verdict = Verdict.NOT_FOUND
        notes.append("suspicious without concrete signals -> not_found")

    sources_verified = bool(
        (draft.sources_verified or verdict == Verdict.OFFICIAL_CONFIRMED) and len(official) > 0
    )

    claim_checks: list[ClaimCheck] = []
    for cc in draft.claim_checks:
        status = cc.status if (cc.status != "verified" or sources_verified) else "unverified"
        source_url = cc.source_url if (cc.source_url in run.seen_urls) else (official[0] if official else None)
        claim_checks.append(
            ClaimCheck(
                claim=cc.claim,
                status=status,
                evidence=cc.evidence,
                source_url=source_url,
            )
        )

    if not claim_checks:
        if summary_points:
            for pt in summary_points:
                claim_checks.append(
                    ClaimCheck(
                        claim=pt,
                        status="verified" if sources_verified else "unverified",
                        evidence=draft.summary,
                        source_url=official[0] if official else (support[0] if support else None),
                    )
                )
        elif topics:
            for top in topics:
                claim_checks.append(
                    ClaimCheck(
                        claim=f"Topic: {top}",
                        status="verified" if sources_verified else "unverified",
                        evidence=draft.summary,
                        source_url=official[0] if official else (support[0] if support else None),
                    )
                )
        else:
            if ex.title.value:
                claim_checks.append(
                    ClaimCheck(
                        claim=f"Opportunity Title: {ex.title.value}",
                        status="verified" if sources_verified else "unverified",
                        evidence=draft.summary,
                        source_url=official[0] if official else (support[0] if support else None),
                    )
                )
            if ex.organizer.value:
                claim_checks.append(
                    ClaimCheck(
                        claim=f"Organizer: {ex.organizer.value}",
                        status="verified" if sources_verified else "unverified",
                        evidence=draft.summary,
                        source_url=official[0] if official else (support[0] if support else None),
                    )
                )

    notes.append("Verified via Gemini API web search pipeline")

    return VerificationResult(
        verdict=verdict,
        summary=draft.summary,
        official_urls=official,
        supporting_urls=support,
        field_status=field_status,
        official_deadline=official_deadline,
        scam_signals=draft.scam_signals,
        guard_notes=notes,
        sources_verified=sources_verified,
        claim_checks=claim_checks,
    )
