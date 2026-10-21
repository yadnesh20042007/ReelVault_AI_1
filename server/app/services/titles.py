import re

_LATIN_LETTER = re.compile(r"[A-Za-z]")
_NON_LATIN_LETTER = re.compile(r"[^\W\d_A-Za-z]", re.UNICODE)


def _is_english_text(value: str) -> bool:
    letters = _LATIN_LETTER.findall(value)
    return bool(letters) and not _NON_LATIN_LETTER.search(value)


def _english_llm_title(post: dict) -> str | None:
    raw = post.get("raw") if isinstance(post.get("raw"), dict) else {}
    analysis = raw.get("reel_analysis") if isinstance(raw.get("reel_analysis"), dict) else {}
    title = (analysis.get("title") or "").strip()
    if title and _is_english_text(title):
        return title[:160]
    return None


def reel_title(post: dict) -> str:
    """Prefer custom user title, then Gemini's English title; otherwise use an English payload or author fallback."""
    raw = post.get("raw") or {}
    if isinstance(raw, dict) and raw.get("custom_title"):
        return str(raw["custom_title"]).strip()[:200]

    llm_title = _english_llm_title(post)
    if llm_title:
        return llm_title

    raw = post.get("raw") or {}
    data = raw.get("data") if isinstance(raw, dict) else {}
    if isinstance(data, dict):
        for key in ("title", "videoTitle", "video_title", "name"):
            value = data.get(key)
            if isinstance(value, str) and value.strip() and _is_english_text(value):
                return value.strip()[:160]

    caption = (post.get("caption") or "").strip()
    if caption:
        first = caption.splitlines()[0].strip()
        if first and _is_english_text(first):
            return first[:160]

    author = (post.get("author") or "").strip()
    if author:
        handle = author if author.startswith("@") else f"@{author}"
        return f"{handle} reel"

    transcript = (post.get("transcript") or "").strip()
    if transcript:
        first = transcript.split(".")[0].strip()
        if first and _is_english_text(first):
            return first[:160]

    return "Untitled reel"
