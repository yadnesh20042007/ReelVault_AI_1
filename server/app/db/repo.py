from datetime import datetime, timedelta, timezone

from app.db.client import get_db
from app.errors import UpstreamFailed
from app.schemas.domain import FetchedPost, PostRef


def _one(res) -> dict | None:
    return res.data[0] if res.data else None


def _since(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def get_source_post(platform: str, shortcode: str) -> dict | None:
    return _one(
        get_db()
        .table("source_posts")
        .select("*")
        .eq("platform", platform)
        .eq("shortcode", shortcode)
        .limit(1)
        .execute()
    )


def insert_source_post(f: FetchedPost, ref: PostRef) -> dict:
    row = {
        "platform": ref.platform,
        "shortcode": ref.shortcode,
        "url": ref.canonical_url,
        "author": f.author,
        "transcript": f.transcript,
        "caption": f.caption,
        "posted_at": f.posted_at.isoformat() if f.posted_at else None,
        "language_hint": f.language_hint,
        "raw": f.raw,
    }
    get_db().table("source_posts").upsert(row, on_conflict="platform,shortcode", ignore_duplicates=True).execute()
    post = get_source_post(ref.platform, ref.shortcode)
    if post is None:
        raise UpstreamFailed("could not store reel")
    return post


def update_source_post_analysis(post_id: int, analysis: dict | None = None, error: dict | None = None) -> dict:
    """Persist an AI result or its user-safe failure state with the source post."""
    post = get_db().table("source_posts").select("*").eq("id", post_id).limit(1).execute()
    current = _one(post)
    if current is None:
        raise UpstreamFailed("could not find saved reel")
    raw = dict(current.get("raw") or {})
    if analysis is not None:
        raw["reel_analysis"] = analysis
        raw.pop("reel_analysis_error", None)
    elif error is not None:
        raw["reel_analysis_error"] = error
    get_db().table("source_posts").update({"raw": raw}).eq("id", post_id).execute()
    return {**current, "raw": raw}


def link_user_reel(user_id: str, source_post_id: int) -> dict:
    get_db().table("user_reels").upsert(
        {"user_id": user_id, "source_post_id": source_post_id},
        on_conflict="user_id,source_post_id",
        ignore_duplicates=True,
    ).execute()
    linked = _one(
        get_db()
        .table("user_reels")
        .select("*")
        .eq("user_id", user_id)
        .eq("source_post_id", source_post_id)
        .limit(1)
        .execute()
    )
    if linked is None:
        raise UpstreamFailed("could not link reel to user")
    return linked


def count_user_reels_since_24h(user_id: str) -> int:
    r = (
        get_db()
        .table("user_reels")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", _since(24))
        .execute()
    )
    return r.count or 0


_POST_FIELDS = "platform, url, transcript, caption, author, raw"


def list_user_reels(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    res = (
        get_db()
        .table("user_reels")
        .select(f"id, created_at, source_posts({_POST_FIELDS})")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return res.data


def get_user_reel(user_id: str, reel_id: int) -> dict | None:
    return _one(
        get_db()
        .table("user_reels")
        .select("id, created_at, source_post_id, source_posts(*)")
        .eq("id", reel_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )


def delete_user_reel(user_id: str, reel_id: int) -> bool:
    res = get_db().table("user_reels").delete().eq("id", reel_id).eq("user_id", user_id).execute()
    return bool(res.data)


def update_reel_title(user_id: str, reel_id: int, title: str) -> dict | None:
    reel = get_user_reel(user_id, reel_id)
    if not reel:
        return None
    post_id = reel.get("source_post_id")
    if not post_id:
        return reel
    post = get_db().table("source_posts").select("*").eq("id", post_id).limit(1).execute()
    current = _one(post)
    if not current:
        return reel
    raw = dict(current.get("raw") or {})
    raw["custom_title"] = title.strip()
    analysis = dict(raw.get("reel_analysis") or {})
    analysis["title"] = title.strip()
    raw["reel_analysis"] = analysis
    get_db().table("source_posts").update({"raw": raw}).eq("id", post_id).execute()
    return get_user_reel(user_id, reel_id)


_TERMINAL_DEEP_COOK_STATUSES = {"done", "not_opportunity", "failed"}
_ACTIVE_DEEP_COOK_STATUSES = {"queued", "classifying", "extracting", "verifying", "researching"}


def count_deep_cooks_since_24h(user_id: str) -> int:
    res = (
        get_db()
        .table("deep_cooks")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", _since(24))
        .execute()
    )
    return res.count or 0


def get_latest_deep_cook(user_id: str, reel_id: int) -> dict | None:
    return _one(
        get_db()
        .table("deep_cooks")
        .select("*")
        .eq("user_id", user_id)
        .eq("user_reel_id", reel_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )


def create_deep_cook(user_id: str, reel_id: int) -> dict:
    result = (
        get_db()
        .table("deep_cooks")
        .insert({"user_id": user_id, "user_reel_id": reel_id, "status": "queued"})
        .execute()
    )
    deep_cook = _one(result)
    if deep_cook is None:
        raise UpstreamFailed("could not start Gemini verification")
    return deep_cook


def get_deep_cook(deep_cook_id: int) -> dict | None:
    return _one(get_db().table("deep_cooks").select("*").eq("id", deep_cook_id).limit(1).execute())


def update_deep_cook(deep_cook_id: int, **fields) -> None:
    if fields.get("status") in _TERMINAL_DEEP_COOK_STATUSES:
        fields.setdefault("finished_at", datetime.now(timezone.utc).isoformat())
    get_db().table("deep_cooks").update(fields).eq("id", deep_cook_id).execute()


def fail_interrupted_deep_cooks() -> int:
    """Close jobs abandoned by a previous API process.

    Deep-cook work runs in FastAPI background tasks, so it cannot survive a
    server restart. Leaving those rows active makes every client poll forever.
    """
    result = (
        get_db()
        .table("deep_cooks")
        .update(
            {
                "status": "failed",
                "error_code": "interrupted",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .in_("status", list(_ACTIVE_DEEP_COOK_STATUSES))
        .execute()
    )
    return len(result.data or [])


def save_link(user_id: str, reel_id: int, label: str, url: str) -> dict:
    result = get_db().table("user_saved_links").upsert(
        {"user_id": user_id, "user_reel_id": reel_id, "label": label, "url": url},
        on_conflict="user_id,user_reel_id,url",
        ignore_duplicates=True,
    ).execute()
    if result.data:
        return result.data[0]
    return _one(get_db().table("user_saved_links").select("*").eq("user_id", user_id).eq("user_reel_id", reel_id).eq("url", url).limit(1).execute())


def list_saved_links(user_id: str) -> list[dict]:
    return get_db().table("user_saved_links").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data


def delete_saved_link(user_id: str, link_id: int) -> bool:
    return bool(get_db().table("user_saved_links").delete().eq("id", link_id).eq("user_id", user_id).execute().data)


def save_date(user_id: str, reel_id: int, label: str, event_date: str) -> dict:
    result = get_db().table("user_saved_dates").upsert(
        {"user_id": user_id, "user_reel_id": reel_id, "label": label, "event_date": event_date},
        on_conflict="user_id,user_reel_id,event_date,label",
        ignore_duplicates=True,
    ).execute()
    if result.data:
        return result.data[0]
    return _one(get_db().table("user_saved_dates").select("*").eq("user_id", user_id).eq("user_reel_id", reel_id).eq("event_date", event_date).eq("label", label).limit(1).execute())


def list_saved_dates(user_id: str) -> list[dict]:
    return get_db().table("user_saved_dates").select("*").eq("user_id", user_id).order("event_date").execute().data


def delete_saved_date(user_id: str, date_id: int) -> bool:
    return bool(get_db().table("user_saved_dates").delete().eq("id", date_id).eq("user_id", user_id).execute().data)


def save_link_vault_entry(user_id: str, reel_id: int, title: str, links: list[dict], topics: list[str]) -> dict:
    """Save one reel's useful links and follow-up search terms as a single shelf item."""
    payload = {
        "user_id": user_id,
        "user_reel_id": reel_id,
        "title": title,
        "links": links,
        "topics": topics,
    }
    result = get_db().table("user_link_vault_entries").upsert(
        payload,
        on_conflict="user_id,user_reel_id",
    ).execute()
    if result.data:
        return result.data[0]
    saved = _one(
        get_db().table("user_link_vault_entries")
        .select("*")
        .eq("user_id", user_id)
        .eq("user_reel_id", reel_id)
        .limit(1)
        .execute()
    )
    if saved is None:
        raise UpstreamFailed("could not save link vault entry")
    return saved


def list_link_vault_entries(user_id: str) -> list[dict]:
    return (
        get_db().table("user_link_vault_entries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )


def delete_link_vault_entry(user_id: str, entry_id: int) -> bool:
    return bool(
        get_db().table("user_link_vault_entries")
        .delete()
        .eq("id", entry_id)
        .eq("user_id", user_id)
        .execute()
        .data
    )
