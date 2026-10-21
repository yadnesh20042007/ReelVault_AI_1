import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.config import Settings
from app.errors import (
    TranscriptCreditsExhausted,
    TranscriptPostUnavailable,
    TranscriptProviderAuthError,
    TranscriptRateLimited,
    TranscriptTemporaryError,
)
from app.schemas.domain import PostRef
from app.services.ingestion.fetchers import SocialKitFetcher, _provider_error


class TestSocialKitApiKeyValidation(unittest.TestCase):
    """Verifies that missing or unconfigured SocialKit API keys are caught immediately."""

    def test_missing_api_key_fails_fast_without_network_call(self):
        fetcher = SocialKitFetcher()
        ref = PostRef(platform="instagram", shortcode="DNGOPWTNvsp", canonical_url="https://www.instagram.com/reel/DNGOPWTNvsp/")

        empty_settings = Settings(socialkit_api_key="")
        with patch("app.services.ingestion.fetchers.get_settings", return_value=empty_settings):
            with patch("httpx.get") as mock_http:
                with self.assertRaises(TranscriptProviderAuthError) as ctx:
                    fetcher.fetch(ref)
                self.assertIn("SOCIALKIT_API_KEY", str(ctx.exception))
                mock_http.assert_not_called()


class TestSocialKitErrorClassification(unittest.TestCase):
    """Verifies granular error classification for SocialKit provider responses."""

    def setUp(self):
        self.fetcher = SocialKitFetcher()
        self.ref = PostRef(platform="instagram", shortcode="DNGOPWTNvsp", canonical_url="https://www.instagram.com/reel/DNGOPWTNvsp/")
        self.valid_settings = Settings(socialkit_api_key="valid_dummy_key_123")

    def test_http_401_unauthorized_raises_provider_auth_error(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 401
        mock_resp.headers = {}
        mock_resp.json.return_value = {"success": False, "message": "You are not authorized to access this resource."}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptProviderAuthError) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_auth_failed")
                self.assertIn("SOCIALKIT_API_KEY", ctx.exception.message)

    def test_http_403_invalid_key_raises_provider_auth_error(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 403
        mock_resp.headers = {}
        mock_resp.json.return_value = {"success": False, "message": "You are not authorized to access this resource."}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptProviderAuthError) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_auth_failed")

    def test_http_402_exhausted_credits_raises_credits_exhausted(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 402
        mock_resp.headers = {"x-credits-remaining": "0"}
        mock_resp.json.return_value = {"success": False, "message": "Insufficient credits to complete transcript."}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptCreditsExhausted) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_credits_exhausted")
                self.assertIn("credits are exhausted", ctx.exception.message.lower())

    def test_zero_credits_header_on_403_raises_credits_exhausted(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 403
        mock_resp.headers = {"x-credits-remaining": "0"}
        mock_resp.json.return_value = {"success": False, "message": "Quota exceeded"}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptCreditsExhausted) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_credits_exhausted")

    def test_http_429_rate_limit_raises_provider_rate_limited(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 429
        mock_resp.headers = {"x-ratelimit-remaining": "0"}
        mock_resp.json.return_value = {"success": False, "message": "Too many requests. Rate limit reached."}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptRateLimited) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_rate_limited")

    def test_http_404_private_or_deleted_post_raises_post_unavailable(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 404
        mock_resp.headers = {}
        mock_resp.json.return_value = {"success": False, "message": "Video is private or unavailable"}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptPostUnavailable) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_post_unavailable")
                self.assertIn("unavailable", ctx.exception.message.lower())

    def test_http_503_upstream_error_raises_temporary_error(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 503
        mock_resp.headers = {}
        mock_resp.json.return_value = {"error": "Instagram service degraded"}

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptTemporaryError) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_unavailable")

    def test_http_timeout_raises_temporary_error(self):
        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", side_effect=httpx.TimeoutException("Connection timed out")):
                with self.assertRaises(TranscriptTemporaryError) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_unavailable")
                self.assertIn("timed out", ctx.exception.message.lower())


class TestSocialKitParsingCorrectness(unittest.TestCase):
    """Verifies response parsing and ensures failed calls never claim a transcript was found."""

    def setUp(self):
        self.fetcher = SocialKitFetcher()
        self.ref = PostRef(platform="instagram", shortcode="DNGOPWTNvsp", canonical_url="https://www.instagram.com/reel/DNGOPWTNvsp/")
        self.valid_settings = Settings(socialkit_api_key="valid_dummy_key_123")

    def test_successful_transcript_parsed_correctly(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {"x-credits-remaining": "18"}
        mock_resp.json.return_value = {
            "success": True,
            "data": {
                "transcript": "National hackathon registration is open until April 15th.",
                "caption": "Check the link in bio for full guidelines.",
                "author": "tech_events_india",
                "videoTitle": "Hackathon 2026 Announcement",
            },
        }

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                post = self.fetcher.fetch(self.ref)
                self.assertEqual(post.platform, "instagram")
                self.assertEqual(post.shortcode, "DNGOPWTNvsp")
                self.assertEqual(post.transcript, "National hackathon registration is open until April 15th.")
                self.assertEqual(post.caption, "Check the link in bio for full guidelines.")
                self.assertEqual(post.author, "tech_events_india")

    def test_successful_call_with_no_speech_returns_none_transcript(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {"x-credits-remaining": "16"}
        mock_resp.json.return_value = {
            "success": True,
            "data": {
                "transcript": "",
                "transcriptSegments": [],
                "caption": "Background music only.",
                "author": "creator_123",
            },
        }

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                post = self.fetcher.fetch(self.ref)
                self.assertIsNone(post.transcript)
                self.assertEqual(post.caption, "Background music only.")

    def test_200_payload_with_success_false_raises_appropriate_exception(self):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.json.return_value = {
            "success": False,
            "message": "Video is private or unavailable",
        }

        with patch("app.services.ingestion.fetchers.get_settings", return_value=self.valid_settings):
            with patch("httpx.get", return_value=mock_resp):
                with self.assertRaises(TranscriptPostUnavailable) as ctx:
                    self.fetcher.fetch(self.ref)
                self.assertEqual(ctx.exception.code, "provider_post_unavailable")


class TestProviderErrorHelper(unittest.TestCase):
    """Verifies backward-compatible _provider_error helper messages."""

    def test_provider_error_strings(self):
        self.assertIn("SOCIALKIT_API_KEY", _provider_error(401))
        self.assertIn("SOCIALKIT_API_KEY", _provider_error(403))
        self.assertIn("credits", _provider_error(402).lower())
        self.assertIn("unavailable", _provider_error(404).lower())
        self.assertIn("rate limit", _provider_error(429).lower())
        self.assertIn("500", _provider_error(500))


if __name__ == "__main__":
    unittest.main()
