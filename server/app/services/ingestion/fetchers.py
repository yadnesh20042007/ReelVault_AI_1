from typing import Protocol

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.errors import (
    TranscriptCreditsExhausted,
    TranscriptPostUnavailable,
    TranscriptProviderAuthError,
    TranscriptRateLimited,
    TranscriptTemporaryError,
    UpstreamFailed,
)
from app.schemas.domain import FetchedPost, PostRef


class ReelFetcher(Protocol):
    def fetch(self, ref: PostRef) -> FetchedPost: ...


class SocialKitFetcher:
    """Third-party vendor for reel and video transcripts.

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
        api_key = (s.socialkit_api_key or "").strip()
        if not api_key:
            raise TranscriptProviderAuthError(
                "SocialKit API key is not configured. Please set SOCIALKIT_API_KEY in server/.env and try again."
            )

        try:
            r = httpx.get(
                f"{s.socialkit_base_url}{path}",
                # SocialKit supports query-string auth, but the header keeps API keys
                # out of access logs and is the provider's preferred form.
                headers={"x-access-key": api_key},
                params={"url": url},
                timeout=60,
            )
        except httpx.TimeoutException:
            raise TranscriptTemporaryError(
                "The transcript provider timed out while processing this reel. Please try again in a few moments."
            )
        except httpx.TransportError as exc:
            raise TranscriptTemporaryError(
                f"Could not connect to transcript provider ({exc.__class__.__name__}). Please check your connection."
            )

        if r.status_code >= 400:
            self._handle_error_response(r)

        try:
            return r.json()
        except Exception:
            raise TranscriptTemporaryError("The transcript provider returned an unreadable response format.")

    @staticmethod
    def _handle_error_response(r: httpx.Response) -> None:
        status_code = r.status_code
        try:
            body = r.json()
            message = str(body.get("message") or body.get("error") or "")
        except Exception:
            message = r.text[:300] if r.text else ""

        msg_lower = message.lower()
        credits_rem = r.headers.get("x-credits-remaining")
        ratelimit_rem = r.headers.get("x-ratelimit-remaining")

        # 1. Credits exhausted
        if status_code == 402 or credits_rem == "0" or any(
            w in msg_lower for w in ("insufficient credits", "credits exhausted", "no credits", "payment required", "out of credits", "quota exceeded")
        ):
            raise TranscriptCreditsExhausted(
                "Transcript provider credits are exhausted. Check your available SocialKit credits at socialkit.dev."
            )

        # 2. Rate limit exceeded
        if status_code == 429 or ratelimit_rem == "0" or any(w in msg_lower for w in ("rate limit", "too many requests")):
            raise TranscriptRateLimited(
                "Transcript provider rate limit reached. Please wait a moment before trying again."
            )

        # 3. Authentication / Key / Permissions
        if status_code in (401, 403):
            raise TranscriptProviderAuthError(
                "Transcript provider access was denied: invalid or unauthorized SocialKit API key. Please verify SOCIALKIT_API_KEY."
            )

        # 4. Content unavailable / private / deleted
        if status_code == 404 or any(
            w in msg_lower for w in ("private", "unavailable", "not found", "deleted", "does not exist")
        ):
            raise TranscriptPostUnavailable(
                "This post is unavailable to the transcript provider. Make sure it is public, active, and accessible."
            )

        # 5. Temporary provider / upstream failure
        raise TranscriptTemporaryError(
            f"Transcript provider encountered an unexpected error ({status_code}). Please try again shortly."
        )

    def fetch(self, ref: PostRef) -> FetchedPost:
        data = self._call(f"/{ref.platform}/transcript", ref.canonical_url)
        if not data.get("success"):
            msg = str(data.get("message") or "transcript provider returned an unsuccessful response")
            msg_lower = msg.lower()
            if any(w in msg_lower for w in ("private", "unavailable", "not found", "deleted")):
                raise TranscriptPostUnavailable(msg)
            if any(w in msg_lower for w in ("credit", "quota")):
                raise TranscriptCreditsExhausted(msg)
            if any(w in msg_lower for w in ("rate limit", "too many requests")):
                raise TranscriptRateLimited(msg)
            if any(w in msg_lower for w in ("unauthorized", "access denied", "forbidden")):
                raise TranscriptProviderAuthError(msg)
            raise TranscriptTemporaryError(msg)
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
    if status_code in (401, 403):
        return "Transcript provider access was denied: invalid or unauthorized SocialKit API key. Please verify SOCIALKIT_API_KEY."
    if status_code == 402:
        return "Transcript provider credits are exhausted. Check your available SocialKit credits at socialkit.dev."
    if status_code == 404:
        return "This post is unavailable to the transcript provider. Make sure it is public and still online."
    if status_code == 429:
        return "Transcript provider rate limit reached. Please wait a moment and try again."
    return f"Transcript provider could not complete this request ({status_code}). Please try again."


def get_fetcher(platform: str) -> ReelFetcher:
    return SocialKitFetcher()
