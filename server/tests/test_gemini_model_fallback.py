"""Tests for Gemini model fallback, quota exhaustion cooldown, and error classification.

All tests are strictly offline with mocked responses and do not make live Gemini API calls.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from google.api_core.exceptions import (
    InvalidArgument,
    NotFound,
    PermissionDenied,
    ResourceExhausted,
    TooManyRequests,
    Unauthenticated,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import BaseModel

from app.config import Settings
from app.llm import (
    AllModelsExhaustedError,
    ModelPool,
    ModelQuotaError,
    _build_model,
    _model_pool,
    get_llm,
    is_auth_error,
    is_invalid_argument_error,
    is_not_found_error,
    is_quota_or_rate_limit_error,
    parse_retry_after,
)
from app.schemas.reels import ReelAnalysis
from app.services.reel_analysis import analyze_reel
from app.services.verification_workflow import _classify_gemini_error


class SampleStructuredOutput(BaseModel):
    title: str
    summary: str


class TestGeminiModelFallback(unittest.TestCase):
    def setUp(self):
        _model_pool.reset()

    def tearDown(self):
        _model_pool.reset()

    @patch("app.llm.get_settings")
    def test_primary_model_success_no_fallback_triggered(self, mock_settings):
        """When primary model succeeds, fallback models should not be called."""
        mock_settings.return_value = Settings(
            gemini_api_key="test_key_1",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite", "gemini-3.8-flash"],
        )

        llm = get_llm("fast")
        structured = llm.with_structured_output(SampleStructuredOutput)

        # Mock primary generate
        with patch("app.llm.MonitoredChatGoogleGenerativeAI._generate") as mock_gen:
            mock_gen.return_value = ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content='{"title": "Primary Success", "summary": "Direct hit"}'
                        )
                    )
                ]
            )

            result = structured.invoke([HumanMessage(content="test prompt")])
            self.assertEqual(result.title, "Primary Success")
            self.assertEqual(result.summary, "Direct hit")
            self.assertEqual(mock_gen.call_count, 1)

    @patch("app.llm.get_settings")
    def test_fallback_to_flash_lite_after_primary_quota_exhausted(self, mock_settings):
        """When primary model (Gemini 3 Flash) hits quota, fallback to gemini-3.5-flash-lite."""
        mock_settings.return_value = Settings(
            gemini_api_key="test_key_1",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite", "gemini-3.8-flash"],
        )

        llm = get_llm("fast")
        structured = llm.with_structured_output(SampleStructuredOutput)

        call_log = []

        def fake_generate(self_model, messages, **kwargs):
            call_log.append(self_model.model_name_str)
            if self_model.model_name_str == "gemini-3-flash-preview":
                raise ResourceExhausted("429 Resource has been exhausted (quota exceeded for metric per day)")
            if self_model.model_name_str == "gemini-3.5-flash-lite":
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content='{"title": "Fallback Success", "summary": "From 3.5 Flash Lite"}'
                            )
                        )
                    ]
                )
            raise RuntimeError("Unexpected model called")

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate):
            res = structured.invoke([HumanMessage(content="test")])

            self.assertEqual(res.title, "Fallback Success")
            self.assertEqual(res.summary, "From 3.5 Flash Lite")
            self.assertEqual(call_log, ["gemini-3-flash-preview", "gemini-3.5-flash-lite"])
            # Primary model should now be marked exhausted in _model_pool
            self.assertTrue(_model_pool.is_exhausted("gemini-3-flash-preview"))

    @patch("app.llm.get_settings")
    def test_subsequent_request_skips_exhausted_model_cooldown(self, mock_settings):
        """When primary model is in cooldown, subsequent request routes directly to healthy fallback model."""
        mock_settings.return_value = Settings(
            gemini_api_key="test_key_1",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite", "gemini-3.8-flash"],
        )

        # Pre-mark primary model as exhausted (e.g. daily quota reached)
        _model_pool.mark_exhausted("gemini-3-flash-preview", duration=1800.0)

        llm = get_llm("fast")
        structured = llm.with_structured_output(SampleStructuredOutput)

        call_log = []

        def fake_generate(self_model, messages, **kwargs):
            call_log.append(self_model.model_name_str)
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content='{"title": "Fast Route", "summary": "Skipped exhausted model"}'
                        )
                    )
                ]
            )

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate):
            res = structured.invoke([HumanMessage(content="test")])
            self.assertEqual(res.title, "Fast Route")
            # gemini-3-flash-preview was NOT called because it is in cooldown!
            self.assertEqual(call_log, ["gemini-3.5-flash-lite"])

    @patch("app.llm.get_settings")
    def test_all_models_exhausted_behavior(self, mock_settings):
        """When all models (primary + all fallbacks) return quota errors, fail with quota error."""
        mock_settings.return_value = Settings(
            gemini_api_key="test_key_1",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite", "gemini-3.8-flash"],
        )

        llm = get_llm("fast")
        structured = llm.with_structured_output(SampleStructuredOutput)

        def fake_generate_all_quota(self_model, messages, **kwargs):
            raise ResourceExhausted(f"429 Quota reached for {self_model.model_name_str}")

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate_all_quota):
            with self.assertRaises((ModelQuotaError, ResourceExhausted)):
                structured.invoke([HumanMessage(content="test")])

            # All candidate models should now be marked exhausted
            self.assertTrue(_model_pool.is_exhausted("gemini-3-flash-preview"))
            self.assertTrue(_model_pool.is_exhausted("gemini-3.5-flash-lite"))
            self.assertTrue(_model_pool.is_exhausted("gemini-3.8-flash"))

    @patch("app.llm.get_settings")
    def test_non_quota_error_does_not_trigger_fallback(self, mock_settings):
        """Non-quota errors (401 unauthenticated, 400 invalid argument) fail immediately without fallback."""
        mock_settings.return_value = Settings(
            gemini_api_key="test_key_1",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite", "gemini-3.8-flash"],
        )

        llm = get_llm("fast")
        structured = llm.with_structured_output(SampleStructuredOutput)

        called_models = []

        def fake_generate_unauth(self_model, messages, **kwargs):
            called_models.append(self_model.model_name_str)
            raise Unauthenticated("401 API_KEY_INVALID: The provided API key is expired or invalid")

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate_unauth):
            with self.assertRaises(Unauthenticated):
                structured.invoke([HumanMessage(content="test")])

            # Only primary was called; fallbacks were NOT triggered for auth error
            self.assertEqual(called_models, ["gemini-3-flash-preview"])
            # Model was NOT marked exhausted because auth error is not a quota problem
            self.assertFalse(_model_pool.is_exhausted("gemini-3-flash-preview"))

    @patch("app.llm.get_settings")
    def test_invalid_argument_does_not_trigger_fallback(self, mock_settings):
        """Malformed requests (400) fail immediately and do not mark models exhausted."""
        mock_settings.return_value = Settings(
            gemini_api_key="test_key_1",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite"],
        )

        llm = get_llm("fast")
        structured = llm.with_structured_output(SampleStructuredOutput)

        called_models = []

        def fake_generate_invalid(self_model, messages, **kwargs):
            called_models.append(self_model.model_name_str)
            raise InvalidArgument("400 Invalid argument: parameter out of range")

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate_invalid):
            with self.assertRaises(InvalidArgument):
                structured.invoke([HumanMessage(content="test")])

            self.assertEqual(called_models, ["gemini-3-flash-preview"])
            self.assertFalse(_model_pool.is_exhausted("gemini-3-flash-preview"))


class TestErrorClassificationAndAnalyzeReel(unittest.TestCase):
    def setUp(self):
        _model_pool.reset()

    def tearDown(self):
        _model_pool.reset()

    def test_parse_retry_after_extraction(self):
        """Verify retry-after parsing from seconds text, daily quota, and headers."""
        # 1. Text with seconds
        exc_sec = ResourceExhausted("Resource exhausted: please retry in 45s.")
        self.assertEqual(parse_retry_after(exc_sec), 45.0)

        # 2. Text with daily limit
        exc_day = ResourceExhausted("Resource exhausted: quota exceeded for metric per day.")
        self.assertEqual(parse_retry_after(exc_day), 1800.0)

        # 3. Text with RPM limit
        exc_min = ResourceExhausted("Rate limit exceeded for requests per minute (RPM).")
        self.assertEqual(parse_retry_after(exc_min), 60.0)

    def test_error_classifiers_distinguish_types(self):
        """Verify error classifiers distinguish quota from auth and not-found errors."""
        quota_exc = ResourceExhausted("429 Resource has been exhausted (quota).")
        auth_exc = Unauthenticated("401 API_KEY_INVALID: unauthenticated.")
        not_found_exc = NotFound("404 models/gemini-invalid is not found for api version.")
        bad_arg_exc = InvalidArgument("400 Bad request.")

        self.assertTrue(is_quota_or_rate_limit_error(quota_exc))
        self.assertFalse(is_quota_or_rate_limit_error(auth_exc))
        self.assertFalse(is_quota_or_rate_limit_error(not_found_exc))

        self.assertTrue(is_auth_error(auth_exc))
        self.assertFalse(is_auth_error(quota_exc))

        self.assertTrue(is_not_found_error(not_found_exc))
        self.assertFalse(is_not_found_error(quota_exc))

        self.assertTrue(is_invalid_argument_error(bad_arg_exc))
        self.assertFalse(is_invalid_argument_error(quota_exc))

    def test_classify_gemini_error_accurately_reports_status(self):
        """_classify_gemini_error returns distinct codes for auth, not-found, and quota."""
        # Auth error
        is_transient, status, code, msg = _classify_gemini_error(
            Unauthenticated("401 API_KEY_INVALID")
        )
        self.assertFalse(is_transient)
        self.assertEqual(status, 401)
        self.assertEqual(code, "gemini_auth_error")

        # Quota error
        is_transient, status, code, msg = _classify_gemini_error(
            ResourceExhausted("429 Resource has been exhausted")
        )
        self.assertTrue(is_transient)
        self.assertEqual(status, 429)
        self.assertEqual(code, "gemini_rate_limited")

        # Not found
        is_transient, status, code, msg = _classify_gemini_error(
            NotFound("404 models/gemini-unknown is not found for api version")
        )
        self.assertFalse(is_transient)
        self.assertEqual(status, 404)
        self.assertEqual(code, "gemini_model_not_found")

    @patch("app.services.reel_analysis.get_settings")
    def test_analyze_reel_falls_back_when_primary_exhausted(self, mock_settings):
        """analyze_reel completes successfully when primary is quota-exhausted and fallback succeeds."""
        mock_settings.return_value = Settings(
            gemini_api_key="valid_key",
            llm_model_fast="gemini-3-flash-preview",
            llm_fallback_models=["gemini-3.5-flash-lite"],
        )

        def fake_generate(self_model, messages, **kwargs):
            if self_model.model_name_str == "gemini-3-flash-preview":
                raise ResourceExhausted("429 Daily quota reached")
            if self_model.model_name_str == "gemini-3.5-flash-lite":
                content = (
                    '{"title": "NVIDIA AI Challenge", "summary": "Great opportunity", '
                    '"english_transcript": "Transcript text", "resources": [], "links": []}'
                )
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
            raise RuntimeError("Unexpected model")

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate):
            analysis, error = analyze_reel("NVIDIA AI challenge transcript", "caption")
            self.assertIsNone(error)
            self.assertIsNotNone(analysis)
            self.assertEqual(analysis["title"], "NVIDIA AI Challenge")

    @patch("app.services.reel_analysis.get_settings")
    def test_analyze_reel_distinguishes_auth_error_from_quota(self, mock_settings):
        """analyze_reel returns ai_auth_error when API key is invalid."""
        mock_settings.return_value = Settings(
            gemini_api_key="invalid_key",
            llm_model_fast="gemini-3-flash-preview",
        )

        def fake_generate(self_model, messages, **kwargs):
            raise Unauthenticated("401 API_KEY_INVALID: Invalid API key")

        with patch("langchain_google_genai.chat_models.ChatGoogleGenerativeAI._generate", fake_generate):
            analysis, error = analyze_reel("Some transcript", "caption")
            self.assertIsNone(analysis)
            self.assertIsNotNone(error)
            self.assertEqual(error["code"], "ai_auth_error")
            self.assertIn("invalid or unauthenticated", error["message"].lower())


if __name__ == "__main__":
    unittest.main()
