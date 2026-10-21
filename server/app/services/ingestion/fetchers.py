from typing import Protocol

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.errors import UpstreamFailed
from app.schemas.domain import FetchedPost, PostRef


class ReelFetcher(Protocol):
    def fetch(self, ref: PostRef) -> FetchedPost: ...


class SocialKitFetcher:
    """Third-party vendor. Treat as unreliable: timeouts, retries, clear errors.

    Confirmed against SocialKit docs:
    GET {base}/{instagram|youtube|tiktok}/transcript?access_key=&url=
    Envelope: {success, data: {transcript, transcriptSegments, wordCount, ...}}.
    Caption / author / posted_at are not in the transcript contract; mapped if present.
    Do NOT use the summarize endpoint (lossy LLM summary).
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=8),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=True,
    )
    def _call(self, path: str, url: str) -> dict:
        s = get_settings()
        r = httpx.get(
            f"{s.socialkit_base_url}{path}",
            # SocialKit supports query-string auth, but the header keeps API keys
            # out of access logs and is the provider's preferred form.
            headers={"x-access-key": s.socialkit_api_key},
            params={"url": url},
            timeout=60,
        )
        if r.status_code >= 400:
            raise UpstreamFailed(_provider_error(r.status_code))
        return r.json()

    def fetch(self, ref: PostRef) -> FetchedPost:
        data = self._call(f"/{ref.platform}/transcript", ref.canonical_url)
        if not data.get("success"):
            raise UpstreamFailed("transcript provider returned an unsuccessful response")
        return self._parse(data, ref)

    @staticmethod
    def _parse(data: dict, ref: PostRef) -> FetchedPost:
        d = dict(data.get("data", {}) or {})
        transcript = d.get("transcript")
        if not transcript:
            segs = d.get("transcriptSegments") or []
            joined = " ".join((s.get("text") or "").strip() for s in segs).strip()
            transcript = joined or None
        author = d.get("author") or d.get("username") or d.get("channel")
        if isinstance(author, dict):
            author = author.get("username") or author.get("name") or author.get("handle")
        title = d.get("title") or d.get("videoTitle") or d.get("video_title") or d.get("name")
        if isinstance(title, str) and title.strip():
            d["title"] = title.strip()
        return FetchedPost(
            platform=ref.platform,
            shortcode=ref.shortcode,
            url=ref.canonical_url,
            transcript=transcript,
            caption=d.get("caption") or d.get("description"),
            author=author,
            language_hint=d.get("language") or d.get("language_hint"),
            raw={**data, "data": d},
        )


def _provider_error(status_code: int) -> str:
    if status_code == 401:
        return "Transcript provider authentication failed. Update SOCIALKIT_API_KEY and try again."
    if status_code == 403:
        return "Transcript provider access was denied. Check the SocialKit API key and available credits, then try again."
    if status_code == 404:
        return "This post is unavailable to the transcript provider. Make sure it is public and still online."
    if status_code == 429:
        return "Transcript provider rate limit reached. Please wait a moment and try again."
    return f"Transcript provider could not complete this request ({status_code}). Please try again."


def get_fetcher(platform: str) -> ReelFetcher:
    return SocialKitFetcher()
