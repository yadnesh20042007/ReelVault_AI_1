import re
from urllib.parse import parse_qs, urlparse

from app.errors import InvalidURL
from app.schemas.domain import PostRef

_CODE = re.compile(r"^[A-Za-z0-9_-]{5,}$")
_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_MSG = "Only Instagram, YouTube and TikTok video links are supported."


def normalize_url(raw: str) -> PostRef:
    raw = (raw or "").strip()
    if not raw or len(raw) > 2048:
        raise InvalidURL(_MSG)
    p = urlparse(raw)
    if p.scheme not in ("http", "https") or p.username or p.password:
        raise InvalidURL(_MSG)
    host = (p.hostname or "").lower()
    for prefix in ("www.", "m."):
        host = host.removeprefix(prefix)
    parts = [x for x in p.path.split("/") if x]

    if host == "instagram.com":
        for i, seg in enumerate(parts[:-1]):
            if seg in ("reel", "reels", "p", "tv") and _CODE.match(parts[i + 1]):
                kind = "p" if seg == "p" else "reel"
                code = parts[i + 1]
                return PostRef(
                    platform="instagram",
                    shortcode=code,
                    canonical_url=f"https://www.instagram.com/{kind}/{code}/",
                )
    elif host == "youtube.com":
        if len(parts) >= 2 and parts[0] == "shorts" and _YT_ID.match(parts[1]):
            return PostRef(
                platform="youtube",
                shortcode=parts[1],
                canonical_url=f"https://www.youtube.com/shorts/{parts[1]}",
            )
        if parts[:1] == ["watch"]:
            vid = (parse_qs(p.query).get("v") or [""])[0]
            if _YT_ID.match(vid):
                return PostRef(
                    platform="youtube",
                    shortcode=vid,
                    canonical_url=f"https://www.youtube.com/watch?v={vid}",
                )
    elif host == "youtu.be":
        if parts and _YT_ID.match(parts[0]):
            return PostRef(
                platform="youtube",
                shortcode=parts[0],
                canonical_url=f"https://www.youtube.com/watch?v={parts[0]}",
            )
    elif host == "tiktok.com":
        if len(parts) >= 3 and parts[0].startswith("@") and parts[1] == "video" and parts[2].isdigit():
            return PostRef(
                platform="tiktok",
                shortcode=parts[2],
                canonical_url=f"https://www.tiktok.com/{parts[0]}/video/{parts[2]}",
            )
    elif host in ("vm.tiktok.com", "vt.tiktok.com"):
        if parts and re.match(r"^[A-Za-z0-9]{5,}$", parts[0]):
            return PostRef(
                platform="tiktok",
                shortcode=f"s_{parts[0]}",
                canonical_url=f"https://{host}/{parts[0]}/",
            )
    raise InvalidURL(_MSG)
