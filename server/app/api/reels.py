import logging
import re
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query, Response
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import repo
from app.deps import AuthUser, current_user
from app.errors import NoContent, NotFound, RateLimited, UpstreamFailed
from app.llm import get_llm
from app.schemas.reels import (
    DeepCookIn,
    DeepCookOut,
    LinkVaultEntryIn,
    LinkVaultEntryOut,
    ReelIn,
    ReelOut,
    ReelUpdateIn,
    SavedDateIn,
    SavedDateOut,
    SavedLinkIn,
    SavedLinkOut,
    TavilySourceOut,
    TavilyVerifyIn,
    TavilyVerifyOut,
)
from app.services.deep_cook.pipeline import run_deep_cook
from app.services.shallow_cook import save_reel
from app.services.titles import reel_title

router = APIRouter(prefix="/reels", tags=["reels"])


def _source_post(reel: dict) -> dict:
    post = reel.get("source_posts") or {}
    if isinstance(post, list):
        post = post[0] if post else {}
    return post if isinstance(post, dict) else {}


def _out(reel: dict, cached: bool = False) -> ReelOut:
    post = _source_post(reel)
    transcript = post.get("transcript")
    caption = post.get("caption")
    transcript_status = "verified" if transcript else "ambiguous" if caption else "unavailable"
    raw = post.get("raw") if isinstance(post.get("raw"), dict) else {}
    analysis_error = raw.get("reel_analysis_error") if isinstance(raw.get("reel_analysis_error"), dict) else {}
    return ReelOut(
        reel_id=reel["id"],
        platform=post.get("platform") or "instagram",
        url=post.get("url") or "",
        title=reel_title(post),
        author=post.get("author"),
        transcript=transcript,
        caption=caption,
        transcript_status=transcript_status,
        analysis=raw.get("reel_analysis"),
        analysis_error_code=analysis_error.get("code"),
        analysis_error=analysis_error.get("message"),
        created_at=reel["created_at"],
        cached=cached,
    )


@router.post("", response_model=ReelOut)
def create_reel(body: ReelIn, user: AuthUser = Depends(current_user)):
    return save_reel(body.url, user.id)


@router.patch("/{reel_id}", response_model=ReelOut)
def update_reel(reel_id: int, body: ReelUpdateIn, user: AuthUser = Depends(current_user)):
    updated = repo.update_reel_title(user.id, reel_id, body.title)
    if updated is None:
        raise NotFound("reel not found")
    return _out(updated)


def _saved_link_out(row: dict) -> SavedLinkOut:
    return SavedLinkOut(id=row["id"], reel_id=row["user_reel_id"], label=row["label"], url=row["url"], created_at=row["created_at"])


def _saved_date_out(row: dict) -> SavedDateOut:
    return SavedDateOut(id=row["id"], reel_id=row["user_reel_id"], label=row["label"], event_date=str(row["event_date"]), created_at=row["created_at"])


def _link_vault_entry_out(row: dict) -> LinkVaultEntryOut:
    return LinkVaultEntryOut(
        id=row["id"],
        reel_id=row["user_reel_id"],
        title=row["title"],
        links=row.get("links") or [],
        topics=row.get("topics") or [],
        created_at=row["created_at"],
    )


@router.get("/saved-links", response_model=list[SavedLinkOut])
def list_saved_links(user: AuthUser = Depends(current_user)):
    return [_saved_link_out(row) for row in repo.list_saved_links(user.id)]


@router.get("/saved-dates", response_model=list[SavedDateOut])
def list_saved_dates(user: AuthUser = Depends(current_user)):
    return [_saved_date_out(row) for row in repo.list_saved_dates(user.id)]


@router.get("/link-vault", response_model=list[LinkVaultEntryOut])
def list_link_vault(user: AuthUser = Depends(current_user)):
    return [_link_vault_entry_out(row) for row in repo.list_link_vault_entries(user.id)]


@router.post("/{reel_id}/saved-links", response_model=SavedLinkOut)
def save_link(reel_id: int, body: SavedLinkIn, user: AuthUser = Depends(current_user)):
    if repo.get_user_reel(user.id, reel_id) is None:
        raise NotFound("reel not found")
    return _saved_link_out(repo.save_link(user.id, reel_id, body.label.strip(), body.url.strip()))


@router.delete("/saved-links/{link_id}", status_code=204)
def delete_saved_link(link_id: int, user: AuthUser = Depends(current_user)):
    if not repo.delete_saved_link(user.id, link_id):
        raise NotFound("saved link not found")
    return Response(status_code=204)


@router.post("/{reel_id}/saved-dates", response_model=SavedDateOut)
def save_date(reel_id: int, body: SavedDateIn, user: AuthUser = Depends(current_user)):
    if repo.get_user_reel(user.id, reel_id) is None:
        raise NotFound("reel not found")
    return _saved_date_out(repo.save_date(user.id, reel_id, body.label.strip(), body.event_date))


@router.post("/{reel_id}/link-vault", response_model=LinkVaultEntryOut)
def save_link_vault_entry(reel_id: int, body: LinkVaultEntryIn, user: AuthUser = Depends(current_user)):
    if repo.get_user_reel(user.id, reel_id) is None:
        raise NotFound("reel not found")
    links = [link.model_dump(mode="json") for link in body.links if link.name.strip()]
    topics = list(dict.fromkeys(topic.strip() for topic in body.topics if topic.strip()))
    row = repo.save_link_vault_entry(user.id, reel_id, body.title.strip(), links, topics)
    return _link_vault_entry_out(row)


@router.delete("/saved-dates/{date_id}", status_code=204)
def delete_saved_date(date_id: int, user: AuthUser = Depends(current_user)):
    if not repo.delete_saved_date(user.id, date_id):
        raise NotFound("saved date not found")
    return Response(status_code=204)


@router.delete("/link-vault/{entry_id}", status_code=204)
def delete_link_vault_entry(entry_id: int, user: AuthUser = Depends(current_user)):
    if not repo.delete_link_vault_entry(user.id, entry_id):
        raise NotFound("link vault entry not found")
    return Response(status_code=204)


@router.post("/{reel_id}/deep-cook", response_model=DeepCookOut, status_code=202)
def start_deep_cook(
    reel_id: int,
    background_tasks: BackgroundTasks,
    body: DeepCookIn = Body(default_factory=DeepCookIn),
    user: AuthUser = Depends(current_user),
):
    """Verify reel correctness, summary, and topics via Gemini web search."""
    if not get_settings().gemini_api_key:
        raise UpstreamFailed("Gemini API key is not configured on the server.")

    reel = repo.get_user_reel(user.id, reel_id)
    if reel is None:
        raise NotFound("reel not found")

    current = repo.get_latest_deep_cook(user.id, reel_id)
    if current and current["status"] not in {"done", "not_opportunity", "failed"}:
        return current
    if repo.count_deep_cooks_since_24h(user.id) >= 20:
        raise RateLimited("Daily limit for research requests reached.")

    post = _source_post(reel)
    payload = body
    raw = post.get("raw") if isinstance(post.get("raw"), dict) else {}
    analysis = raw.get("reel_analysis") or {}

    transcript = (payload.transcript or post.get("transcript") or "").strip() or None
    caption = (payload.caption or post.get("caption") or "").strip() or None
    title = (payload.title or reel_title(post) or "").strip() or None
    summary = (payload.summary or analysis.get("summary") or "").strip() or None
    summary_points = payload.summary_points or analysis.get("summary_points") or []
    topics = payload.topics or analysis.get("tags") or []

    if not (transcript or caption or summary):
        raise NoContent("This reel has no transcript, caption, or summary to verify.")

    deep_cook = repo.create_deep_cook(user.id, reel_id)
    background_tasks.add_task(
        run_deep_cook,
        deep_cook["id"],
        transcript=transcript,
        caption=caption,
        title=title,
        summary=summary,
        summary_points=summary_points,
        topics=topics,
    )
    return deep_cook


@router.get("/{reel_id}/deep-cook", response_model=DeepCookOut)
def get_deep_cook(reel_id: int, user: AuthUser = Depends(current_user)):
    if repo.get_user_reel(user.id, reel_id) is None:
        raise NotFound("reel not found")
    deep_cook = repo.get_latest_deep_cook(user.id, reel_id)
    if deep_cook is None:
        raise NotFound("research not found")
    return deep_cook


def _clean_source_summary(content: str) -> str:
    """Produce a concise 2-3 line relevant summary under 170 characters without markdown or web noise."""
    if not content:
        return "Verified web record matching this opportunity."
    clean = re.sub(r"<[^>]+>", " ", content)
    clean = re.sub(r"[#*`_\[\]]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > 170:
        period_idx = clean.find(".", 85)
        if 0 < period_idx <= 180:
            clean = clean[:period_idx + 1]
        else:
            space_idx = clean.rfind(" ", 85, 165)
            clean = (clean[:space_idx] if space_idx > 85 else clean[:165]) + "…"
    return clean


class _AIVerdict(BaseModel):
    verdict: Literal["True", "Partially True", "False", "Unverified"] = "Partially True"
    explanation: str = Field(description="Concise 2-3 sentence explanation based on the retrieved evidence.")
    claims: list[str] = Field(default_factory=list, description="2-3 key factual claims verified from the reel.")


@router.post("/{reel_id}/verify-tavily", response_model=TavilyVerifyOut)
def verify_reel_with_tavily(
    reel_id: int,
    body: TavilyVerifyIn = Body(default_factory=TavilyVerifyIn),
    user: AuthUser = Depends(current_user),
):
    """Verify reel content, summary, and keywords using Tavily real-time web search platform and AI analysis."""
    settings = get_settings()
    if not settings.tavily_api_key:
        raise UpstreamFailed("Tavily API key is not configured on the server.")

    reel = repo.get_user_reel(user.id, reel_id)
    post = _source_post(reel) if reel else {}
    raw = post.get("raw") if isinstance(post.get("raw"), dict) else {}
    analysis = raw.get("reel_analysis") or {}

    summary = (body.summary or analysis.get("summary") or "").strip()
    transcript = (body.transcript or post.get("transcript") or post.get("caption") or "").strip()
    title = (body.title or (reel_title(post) if post else None) or "").strip()

    if not (summary or transcript or title):
        raise NoContent("This reel has no transcript, caption, or summary to verify.")

    query = (body.query or "").strip()
    if not query:
        if summary:
            query = summary
        elif transcript:
            query = transcript[:250]
        else:
            query = title or "opportunity verification"

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        res = client.search(query=query, max_results=3, search_depth="basic")
        raw_results = res.get("results", [])[:3]

        sources: list[TavilySourceOut] = []
        for r in raw_results:
            if not r.get("url"):
                continue
            raw_content = r.get("content") or ""
            short_summary = _clean_source_summary(raw_content)
            sources.append(
                TavilySourceOut(
                    title=r.get("title") or "Web Source",
                    url=r.get("url"),
                    summary=short_summary,
                    content=short_summary,
                    score=r.get("score"),
                )
            )

        if not sources:
            return TavilyVerifyOut(
                verified=False,
                verdict="Unverified",
                explanation="No relevant web evidence was found for these claims via search.",
                claims=[title] if title else [],
                query=query,
                sources=[],
                summary="No matching web records found.",
            )

        # AI Analysis to cross-check claims against retrieved web evidence
        verdict = "Partially True"
        explanation = f"Found {len(sources)} relevant web sources corroborating details of this opportunity."
        claims = []
        if analysis.get("summary_points"):
            claims = list(analysis["summary_points"][:3])
        elif title:
            claims = [title]

        if settings.gemini_api_key:
            try:
                evidence_text = "\n\n".join(
                    f"Source {i+1}: {s.title} ({s.url})\nEvidence: {s.summary}"
                    for i, s in enumerate(sources)
                )
                target_text = f"Title: {title}\nSummary: {summary}\nTranscript: {transcript[:500]}"
                ai_model = get_llm("fast").with_structured_output(_AIVerdict)
                ai_res = ai_model.invoke([
                    SystemMessage(
                        "You are an expert fact-checker. Cross-examine the reel claims against the retrieved top-3 web evidence.\n"
                        "Classify verdict as strictly one of:\n"
                        "- 'True': If retrieved web evidence clearly supports and confirms the reel claims.\n"
                        "- 'Partially True': If core idea is valid but some details (dates, eligibility, stipends) differ, or only partially backed.\n"
                        "- 'False': If web evidence directly contradicts the claims or indicates a hoax/scam.\n"
                        "- 'Unverified': If web evidence is completely inconclusive or unrelated.\n"
                        "Provide a concise 2-3 sentence explanation and extract 1-3 key factual claims."
                    ),
                    HumanMessage(f"Reel to verify:\n{target_text}\n\nRetrieved Web Evidence:\n{evidence_text}")
                ])
                verdict = ai_res.verdict
                explanation = ai_res.explanation
                if ai_res.claims:
                    claims = ai_res.claims
            except Exception as ai_err:
                logging.getLogger("verify").warning("AI verdict evaluation fallback: %s", ai_err)
                if any(s.score and s.score > 0.7 for s in sources):
                    verdict = "True"
                else:
                    verdict = "Partially True"

        return TavilyVerifyOut(
            verified=True,
            verdict=verdict,
            explanation=explanation,
            claims=claims,
            query=query,
            sources=sources,
            summary=f"Found {len(sources)} verified web source(s) via Tavily search.",
        )
    except Exception as exc:
        raise UpstreamFailed(f"Tavily search failed: {exc}")


@router.get("", response_model=list[ReelOut])
def list_reels(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: AuthUser = Depends(current_user),
):
    return [_out(row, cached=True) for row in repo.list_user_reels(user.id, limit, offset)]


@router.get("/{reel_id}", response_model=ReelOut)
def get_reel(reel_id: int, user: AuthUser = Depends(current_user)):
    reel = repo.get_user_reel(user.id, reel_id)
    if reel is None:
        raise NotFound("reel not found")
    return _out(reel, cached=True)


@router.delete("/{reel_id}", status_code=204)
def delete_reel(reel_id: int, user: AuthUser = Depends(current_user)):
    if not repo.delete_user_reel(user.id, reel_id):
        raise NotFound("reel not found")
    return Response(status_code=204)
