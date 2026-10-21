import os
import unittest
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

from app.config import get_settings
from app.db import verification_repo
from app.deps import AuthUser, current_user
from app.errors import AppError
from app.main import app
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
from app.services.verification_workflow import (
    classify_source,
    connect_deadline_to_vault,
    execute_run,
    is_substantively_relevant,
    match_evidence_to_claims,
    run_card_stage,
    run_claims_stage,
    run_evidence_stage,
    run_extracted_stage,
    run_verdict_stage,
)


class MockLLM:
    """Mock LLM supporting .with_structured_output(...) and recording invocations."""

    def __init__(self, responses: list[Any] = None, response: Any = None):
        self.responses = list(responses) if responses else ([response] if response is not None else [])
        self.calls = []

    def with_structured_output(self, schema: Any):
        return self

    def invoke(self, messages: Any) -> Any:
        self.calls.append(messages)
        if self.responses:
            item = self.responses.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        raise RuntimeError("MockLLM: no configured response for invoke()")


class TestGeminiPoweredVerificationWorkflow(unittest.TestCase):
    def setUp(self):
        self.user_id = "test-user-12345"

    def test_1_gemini_invoked_for_new_claim_analysis(self):
        """1. Gemini is actually invoked for new claim analysis (Call 1)."""
        mock_analysis = GeminiClaimAnalysis(
            title="National AI Hackathon 2026",
            organizer="IIT Bombay",
            author="tech_creator_account",
            category="hackathon",
            deadline_raw="15th December 2026",
            deadline_date="2026-12-15",
            year_ambiguous=False,
            has_fee=True,
            is_fee_warning=True,
            fee_raw="₹500",
            fee_warning_message="Registration fee detected (₹500). Verify organizer before paying.",
            eligibility="Engineering students",
            reward_or_benefit="₹5,00,000 cash prize pool",
            mode="offline",
            links=["https://iitb.ac.in/hackathon"],
            claims=[
                ClaimItem(claim_id="c1", claim_text="The opportunity is organized by IIT Bombay.", claim_type="organizer"),
                ClaimItem(claim_id="c2", claim_text="Application deadline is 15th December 2026.", claim_type="deadline"),
                ClaimItem(claim_id="c3", claim_text="Registration fee of ₹500 is required.", claim_type="fee", is_fee_warning_claim=True),
            ],
            search_queries=["IIT Bombay National AI Hackathon 2026 official"],
        )
        mock_llm = MockLLM(response=mock_analysis)

        rvpack = RVPackData(
            transcript="Join the National AI Hackathon 2026 organized by IIT Bombay. Registration fee is ₹500. Deadline is 15th December 2026.",
            on_screen="IIT Bombay AI Hackathon\nApply at https://iitb.ac.in/hackathon",
            meta={"author": "tech_creator_account", "title": "AI Hackathon"},
            raw_text="Join the National AI Hackathon 2026 organized by IIT Bombay.",
            sections_found=["TRANSCRIPT", "ON_SCREEN", "META"],
        )

        extracted = run_extracted_stage(rvpack, llm_client=mock_llm)

        # Verify Gemini Call 1 was invoked
        self.assertEqual(len(mock_llm.calls), 1)
        system_msg = mock_llm.calls[0][0]["content"]
        self.assertIn("ReelVault's expert factual extraction", system_msg)
        user_msg = mock_llm.calls[0][1]["content"]
        self.assertIn("National AI Hackathon 2026", user_msg)

        # Verify outputs derived from Gemini structured response
        self.assertEqual(extracted.title, "National AI Hackathon 2026")
        self.assertEqual(extracted.organizer, "IIT Bombay")
        self.assertEqual(extracted.author, "tech_creator_account")
        self.assertEqual(len(extracted.claims), 3)
        self.assertEqual(extracted.search_queries, ["IIT Bombay National AI Hackathon 2026 official"])

    def test_2_gemini_invoked_for_evidence_evaluation(self):
        """2. Gemini is actually invoked for evidence evaluation (Call 2)."""
        claims = ClaimsStagePayload(
            claims=[
                ClaimItem(claim_id="c1", claim_text="The opportunity is organized by IIT Bombay.", claim_type="organizer"),
                ClaimItem(claim_id="c2", claim_text="Registration fee of ₹500 is required.", claim_type="fee", is_fee_warning_claim=True),
            ],
            total_claims=2,
            contains_fee_claim=True,
        )
        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=["c1", "c2"],
                    url="https://iitb.ac.in/events/ai-hackathon",
                    title="Official IIT Bombay AI Hackathon 2026",
                    snippet="IIT Bombay announces National AI Hackathon 2026. Nominal team registration fee is ₹500.",
                    domain="iitb.ac.in",
                    domain_trust="high",
                    source_type="official_organizer",
                    source_label="Official organizer source",
                )
            ],
            queries_used=["IIT Bombay AI Hackathon 2026 official"],
            official_domains=["iitb.ac.in"],
            search_status="completed",
        )
        extracted = ExtractedStagePayload(
            title="National AI Hackathon 2026",
            organizer="IIT Bombay",
            author="tech_creator",
            has_fee=True,
            fee_raw="₹500",
        )

        mock_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(
                    claim_id="c1",
                    claim_text="The opportunity is organized by IIT Bombay.",
                    verdict=ClaimVerdictLabel.SUPPORTED,
                    explanation="Official organizer portal confirms the hackathon.",
                    cited_sources=["https://iitb.ac.in/events/ai-hackathon"],
                ),
                ClaimVerdictItem(
                    claim_id="c2",
                    claim_text="Registration fee of ₹500 is required.",
                    verdict=ClaimVerdictLabel.SUPPORTED,
                    explanation="Official event terms confirm ₹500 participation fee.",
                    cited_sources=["https://iitb.ac.in/events/ai-hackathon"],
                    is_fee_warning_claim=True,
                ),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="All core claims are corroborated by the official IIT Bombay domain.",
            scam_warnings=[],
            has_scam_warning=False,
            fraudulent_detected=False,
        )
        mock_llm = MockLLM(response=mock_eval)

        verdict = run_verdict_stage(claims, evidence, extracted, llm_client=mock_llm)

        # Verify Gemini Call 2 was invoked
        self.assertEqual(len(mock_llm.calls), 1)
        system_msg = mock_llm.calls[0][0]["content"]
        self.assertIn("ReelVault's evidence evaluation and verdict engine", system_msg)
        user_msg = mock_llm.calls[0][1]["content"]
        self.assertIn("https://iitb.ac.in/events/ai-hackathon", user_msg)

        # Verify verdicts derived from model
        self.assertEqual(verdict.overall_verdict, ClaimVerdictLabel.SUPPORTED)
        self.assertEqual(len(verdict.claim_verdicts), 2)
        self.assertEqual(verdict.claim_verdicts[0].verdict, ClaimVerdictLabel.SUPPORTED)
        self.assertEqual(verdict.claim_verdicts[0].cited_sources, ["https://iitb.ac.in/events/ai-hackathon"])

    def test_3_verdicts_derived_from_model_not_old_hardcoded_rules(self):
        """3. Verdicts are derived from model responses and relevant supplied evidence rather than old hardcoded rules."""
        # Scenario: Even though domain is high-trust (iitb.ac.in), the model determines the opportunity was canceled / contradicted.
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c1", claim_text="Event is active.", claim_type="event")]
        )
        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=["c1"],
                    url="https://iitb.ac.in/cancellation-notice",
                    title="Notice: Event Cancelled",
                    snippet="The planned hackathon has been canceled indefinitely.",
                    domain="iitb.ac.in",
                    domain_trust="high",
                    source_type="official_organizer",
                )
            ],
            queries_used=["IIT Bombay Hackathon official"],
            search_status="completed",
        )
        extracted = ExtractedStagePayload(title="Hackathon 2026", organizer="IIT Bombay")

        mock_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(
                    claim_id="c1",
                    claim_text="Event is active.",
                    verdict=ClaimVerdictLabel.CONTRADICTED,
                    explanation="Official notice states the event was canceled indefinitely.",
                    cited_sources=["https://iitb.ac.in/cancellation-notice"],
                )
            ],
            overall_verdict=ClaimVerdictLabel.CONTRADICTED,
            summary="Event notice confirms cancellation.",
            scam_warnings=[],
            has_scam_warning=False,
            fraudulent_detected=True,
        )
        mock_llm = MockLLM(response=mock_eval)

        verdict = run_verdict_stage(claims, evidence, extracted, llm_client=mock_llm)

        # Under old rules, matching an official organizer domain would hardcode SUPPORTED.
        # Under genuine Gemini evaluation, the model's CONTRADICTED verdict is preserved.
        self.assertEqual(verdict.overall_verdict, ClaimVerdictLabel.CONTRADICTED)
        self.assertEqual(verdict.claim_verdicts[0].verdict, ClaimVerdictLabel.CONTRADICTED)
        self.assertIn("canceled indefinitely", verdict.claim_verdicts[0].explanation)

    def test_4_no_api_key_produces_clear_configuration_error(self):
        """4. No API key produces a clear configuration error, not a fake verdict."""
        # Temporarily mock get_all_gemini_keys to return []
        with patch("app.config.Settings.get_all_gemini_keys", return_value=[]):
            with self.assertRaises(AppError) as ctx:
                run_extracted_stage(
                    RVPackData(transcript="Hello", on_screen="Test", meta={}, raw_text="Hello Test"),
                    llm_client=None,
                )
            self.assertEqual(ctx.exception.status, 503)
            self.assertEqual(ctx.exception.code, "llm_unconfigured")
            self.assertIn("Gemini API key is not configured", ctx.exception.message)

    def test_5_search_failure_does_not_fabricate_evidence(self):
        """5. Search failure does not result in fabricated evidence or falsely verified claims."""
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c1", claim_text="Event organized by ABC Corp", claim_type="organizer")]
        )
        extracted = ExtractedStagePayload(
            title="ABC Challenge",
            organizer="ABC Corp",
            search_queries=["ABC Corp Challenge official"],
        )

        mock_tavily = MagicMock()
        mock_tavily.search.side_effect = RuntimeError("Tavily search rate limit exceeded")

        evidence = run_evidence_stage(claims, extracted, tavily_client=mock_tavily)

        self.assertEqual(evidence.search_status, "failed")
        self.assertIn("failed", evidence.search_notes.lower())
        self.assertEqual(len(evidence.evidence_items), 0)
        self.assertEqual(len(evidence.official_domains), 0)

    def test_6_unrelated_third_party_results_do_not_support_target_event(self):
        """6. Unrelated third-party results do not support the target event."""
        extracted = ExtractedStagePayload(
            title="IIT Bombay AI Hackathon 2026",
            organizer="IIT Bombay",
            links=[],
        )
        claims = [
            ClaimItem(claim_id="c1", claim_text="IIT Bombay AI Hackathon 2026 event", claim_type="event"),
            ClaimItem(claim_id="c2", claim_text="Organized by IIT Bombay", claim_type="organizer"),
        ]

        # Evidence for completely unrelated event at a different college
        unrelated_matches = match_evidence_to_claims(
            ev_title="MIT Robotics Competition 2024",
            ev_snippet="Annual robotics challenge hosted by MIT in Boston.",
            ev_url="https://mit.edu/robotics-2024",
            source_type="trusted_institution",
            claims=claims,
            extracted=extracted,
        )
        self.assertEqual(unrelated_matches, [])

    def test_7_parseable_deadline_does_not_auto_verify(self):
        """7. A parseable deadline does not automatically count as verified."""
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c_dl", claim_text="Deadline is 25th December 2026.", claim_type="deadline")]
        )
        # Search returns no corroborating evidence for the deadline
        evidence = EvidenceStagePayload(evidence_items=[], search_status="completed")
        extracted = ExtractedStagePayload(
            title="Some Opportunity",
            deadline=DeadlineInfo(raw="25th December 2026", date="2026-12-25", reminder_eligible=True),
        )

        mock_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(
                    claim_id="c_dl",
                    claim_text="Deadline is 25th December 2026.",
                    verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
                    explanation="Date syntax parses correctly, but no external source corroborates this deadline.",
                    cited_sources=[],
                )
            ],
            overall_verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
            summary="Deadline lacks external corroboration.",
            scam_warnings=[],
            has_scam_warning=False,
            fraudulent_detected=False,
        )
        mock_llm = MockLLM(response=mock_eval)

        verdict = run_verdict_stage(claims, evidence, extracted, llm_client=mock_llm)
        self.assertEqual(verdict.claim_verdicts[0].verdict, ClaimVerdictLabel.INSUFFICIENT_EVIDENCE)
        self.assertIn("no external source corroborates", verdict.claim_verdicts[0].explanation)

    def test_8_fee_500_alone_does_not_imply_fraud(self):
        """8. A ₹500 fee alone does not imply fraud; displays neutral caution."""
        extracted = ExtractedStagePayload(
            title="National CodeFest",
            organizer="Unverified organizer",
            has_fee=True,
            fee_raw="₹500",
        )
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c_fee", claim_text="Registration fee of ₹500 is required.", claim_type="fee", is_fee_warning_claim=True)],
            contains_fee_claim=True,
        )
        evidence = EvidenceStagePayload(evidence_items=[], search_status="completed")

        mock_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(
                    claim_id="c_fee",
                    claim_text="Registration fee of ₹500 is required.",
                    verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
                    explanation="Fee stated in announcement, unverified externally. A fee alone does not establish fraud.",
                    cited_sources=[],
                    is_fee_warning_claim=True,
                )
            ],
            overall_verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
            summary="Registration fee is present; verify payment recipient before transferring funds.",
            scam_warnings=[],
            has_scam_warning=True,
            fraudulent_detected=False,
        )
        mock_llm = MockLLM(response=mock_eval)

        verdict = run_verdict_stage(claims, evidence, extracted, llm_client=mock_llm)

        # Must not declare fraud
        self.assertFalse(verdict.fraudulent_detected)
        self.assertNotEqual(verdict.overall_verdict, ClaimVerdictLabel.CONTRADICTED)

        # Must include the neutral fee caution
        self.assertTrue(verdict.has_scam_warning)
        self.assertTrue(any("Registration fee detected (₹500)" in w for w in verdict.scam_warnings))
        self.assertTrue(any("A fee alone does not establish fraud" in w for w in verdict.scam_warnings))

    def test_9_content_author_not_automatically_organizer(self):
        """9. The content author is not automatically the event organizer."""
        mock_analysis = GeminiClaimAnalysis(
            title="Startup Pitch Day 2026",
            organizer="Unverified organizer",
            author="reel_influencer_daily",
            category="competition",
            claims=[
                ClaimItem(claim_id="c1", claim_text="Organizer is unverified.", claim_type="organizer"),
            ],
        )
        mock_llm = MockLLM(response=mock_analysis)

        rvpack = RVPackData(
            transcript="Hey guys, checkout this startup pitch competition happening next month!",
            on_screen="Pitch Day 2026",
            meta={"author": "reel_influencer_daily"},
            raw_text="Hey guys, checkout this startup pitch competition happening next month!",
            sections_found=["TRANSCRIPT", "ON_SCREEN", "META"],
        )

        extracted = run_extracted_stage(rvpack, llm_client=mock_llm)

        self.assertEqual(extracted.author, "reel_influencer_daily")
        self.assertEqual(extracted.organizer, "Unverified organizer")
        self.assertNotEqual(extracted.organizer, extracted.author)

    def test_10_citations_map_to_real_evidence_records(self):
        """10. Citations map to real evidence records and URLs (hallucinated URLs stripped)."""
        real_url = "https://verified-site.org/event"
        fake_url = "https://completely-invented-by-model.com/fake"

        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c1", claim_text="Event announcement", claim_type="event")]
        )
        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(id="ev_1", url=real_url, domain="verified-site.org")
            ]
        )
        extracted = ExtractedStagePayload(title="Verified Event")

        mock_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(
                    claim_id="c1",
                    claim_text="Event announcement",
                    verdict=ClaimVerdictLabel.SUPPORTED,
                    explanation="Supported by real and fake url.",
                    cited_sources=[real_url, fake_url],
                )
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Grounded evaluation.",
        )
        mock_llm = MockLLM(response=mock_eval)

        verdict = run_verdict_stage(claims, evidence, extracted, llm_client=mock_llm)

        # fake_url must have been stripped
        self.assertEqual(verdict.claim_verdicts[0].cited_sources, [real_url])
        self.assertNotIn(fake_url, verdict.claim_verdicts[0].cited_sources)

    def test_11_malformed_gemini_output_handled_safely(self):
        """11. Malformed Gemini output is handled safely without corrupting workflow."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("Model rate limit 429 or schema parse failure")
        mock_llm.with_structured_output.return_value = mock_llm

        rvpack = RVPackData(
            transcript="Valid announcement",
            on_screen="Test",
            meta={},
            raw_text="Valid announcement",
            sections_found=["TRANSCRIPT"],
        )

        with self.assertRaises(RuntimeError) as ctx:
            run_extracted_stage(rvpack, llm_client=mock_llm)
        self.assertIn("Gemini claim analysis failed", str(ctx.exception))

    def test_12_resuming_run_does_not_repeat_paid_calls(self):
        """12. Resuming a run does not repeat already persisted paid calls."""
        run = verification_repo.create_run(self.user_id, "---TRANSCRIPT---\nTest\n---ON_SCREEN---\nTest", "rvpack")
        run_id = run["id"]

        # Pre-save completed Stage 1 (Extracted)
        extracted_data = ExtractedStagePayload(
            title="Pre-extracted Title",
            organizer="Pre-extracted Organizer",
            claims=[ClaimItem(claim_id="c1", claim_text="Claim 1")],
            search_queries=["query 1"],
        ).model_dump(mode="json")
        verification_repo.save_stage(run_id, StageName.EXTRACTED.value, 1, extracted_data, "completed")

        # LLM mock for Stage 4 (Verdict) only
        verdict_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="Claim 1", verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE, explanation="None")
            ],
            overall_verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
            summary="None",
        )
        mock_llm = MockLLM(response=verdict_eval)
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = {"results": []}

        res = execute_run(run_id, self.user_id, tavily_client=mock_tavily, llm_client=mock_llm)

        # Stage 1 was already completed, so Call 1 was NOT invoked. Only Call 2 (Verdict) was invoked.
        self.assertEqual(len(mock_llm.calls), 1)
        self.assertEqual(res["status"], "completed")

        # If we execute_run again to resume the completed run, 0 calls should happen!
        mock_llm_2 = MockLLM()
        res2 = execute_run(run_id, self.user_id, tavily_client=mock_tavily, llm_client=mock_llm_2)
        self.assertEqual(len(mock_llm_2.calls), 0)
        self.assertEqual(res2["status"], "completed")

    def test_13_existing_auth_ownership_and_stage_order_protections(self):
        """13. Existing authentication, ownership, persistence, and stage-ordering protections remain intact."""
        from starlette.testclient import TestClient

        client = TestClient(app)

        # Unauthenticated request returns 401
        unauth_res = client.post("/v1/verification/rvpack", json={"content": "---TRANSCRIPT---\nTest"})
        self.assertEqual(unauth_res.status_code, 401)

        # Prerequisite stage ordering check: Card cannot be created without Stages 1-4 persisted
        dummy_run = verification_repo.create_run(self.user_id, "---TRANSCRIPT---\nIncomplete", "rvpack")
        with self.assertRaises(ValueError) as ctx:
            run_card_stage(dummy_run["id"], stages_records=[], user_id=self.user_id)
        self.assertIn("prerequisite stages", str(ctx.exception))


class TestVerificationAPIEndpoints(unittest.TestCase):
    def setUp(self):
        from starlette.testclient import TestClient
        self.mock_user = AuthUser(id="api-test-user-999", email="test@example.com", token="mock-token")
        app.dependency_overrides[current_user] = lambda: self.mock_user
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_api_unconfigured_gemini_key_returns_503(self):
        """API returns 503 llm_unconfigured when Gemini keys are missing."""
        with patch("app.config.Settings.get_all_gemini_keys", return_value=[]):
            res = self.client.post(
                "/v1/verification/rvpack",
                json={"content": "---TRANSCRIPT---\nTest Hackathon\n---ON_SCREEN---\nTest"},
            )
            self.assertEqual(res.status_code, 503)
            err_dict = res.json().get("error", {})
            self.assertEqual(err_dict.get("code"), "llm_unconfigured")
            self.assertIn("Gemini API key is not configured", err_dict.get("message", ""))

    def test_api_full_run_with_mocked_llm(self):
        """API executes full 5-stage run successfully with mocked LLM."""
        mock_analysis = GeminiClaimAnalysis(
            title="National CodeFest 2026",
            organizer="IIT Bombay",
            author="iitb_official",
            category="hackathon",
            deadline_raw="15th December 2026",
            deadline_date="2026-12-15",
            has_fee=True,
            fee_raw="₹500",
            fee_warning_message="Registration fee detected (₹500). Verify organizer before paying.",
            claims=[
                ClaimItem(claim_id="c1", claim_text="National CodeFest 2026 event", claim_type="event"),
                ClaimItem(claim_id="c2", claim_text="Registration fee of ₹500", claim_type="fee", is_fee_warning_claim=True),
            ],
            search_queries=["IIT Bombay CodeFest official"],
        )
        mock_verdict = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="National CodeFest 2026 event", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Verified", cited_sources=["https://iitb.ac.in"]),
                ClaimVerdictItem(claim_id="c2", claim_text="Registration fee of ₹500", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Fee confirmed", cited_sources=["https://iitb.ac.in"], is_fee_warning_claim=True),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="All details corroborated.",
            scam_warnings=[],
            has_scam_warning=False,
            fraudulent_detected=False,
        )
        mock_llm = MockLLM(responses=[mock_analysis, mock_verdict])

        # Patch _invoke_structured_llm in verification_workflow to use mock_llm
        with patch("app.services.verification_workflow._invoke_structured_llm") as mock_invoke:
            def side_effect(client, schema, messages, fallback_kind="fast", **kwargs):
                if schema == GeminiClaimAnalysis:
                    return mock_analysis
                return mock_verdict

            mock_invoke.side_effect = side_effect

            res = self.client.post(
                "/v1/verification/rvpack",
                json={
                    "content": (
                        "---TRANSCRIPT---\n"
                        "National CodeFest 2026 organized by IIT Bombay. Fee is ₹500.\n"
                        "---ON_SCREEN---\n"
                        "IIT Bombay CodeFest\n"
                        "---META---\n"
                        "author: iitb_official\n"
                    )
                },
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "completed")
            self.assertEqual(data["completed_stages"], ["extracted", "claims", "evidence", "verdict", "card"])
            self.assertIsNotNone(data["card"])
            self.assertEqual(data["card"]["title"], "National CodeFest 2026")
            self.assertEqual(data["card"]["organizer"], "IIT Bombay")
            self.assertEqual(data["card"]["author"], "iitb_official")


class TestNineRequiredVerificationScenarios(unittest.TestCase):
    """Explicitly verifies the 9 mandatory verification workflow scenarios."""

    def setUp(self):
        self.user_id = "test-nine-scenarios-user"

    def test_scenario_1_exact_matching_official_page_corroborates_officially(self):
        """Scenario 1: Exact matching official event page -> officially corroborated."""
        extracted = ExtractedStagePayload(
            title="IIT Bombay National AI Hackathon 2026",
            organizer="IIT Bombay",
            deadline=DeadlineInfo(raw="15th December 2026", date="2026-12-15"),
            has_fee=False,
        )
        claims = ClaimsStagePayload(
            claims=[
                ClaimItem(claim_id="c1", claim_text="IIT Bombay National AI Hackathon 2026", claim_type="event"),
                ClaimItem(claim_id="c2", claim_text="Organized by IIT Bombay", claim_type="organizer"),
            ]
        )
        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=["c1", "c2"],
                    url="https://iitb.ac.in/events/ai-hackathon-2026",
                    title="IIT Bombay National AI Hackathon 2026 Official Portal",
                    snippet="IIT Bombay officially hosts the National AI Hackathon 2026 on campus.",
                    domain="iitb.ac.in",
                    domain_trust="high",
                    source_type="official_organizer",
                )
            ],
            official_domains=["iitb.ac.in"],
            search_status="completed",
        )
        verdict = VerdictStagePayload(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="IIT Bombay National AI Hackathon 2026", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Verified by official organizer portal.", cited_sources=["https://iitb.ac.in/events/ai-hackathon-2026"]),
                ClaimVerdictItem(claim_id="c2", claim_text="Organized by IIT Bombay", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Organizer confirmed by official domain.", cited_sources=["https://iitb.ac.in/events/ai-hackathon-2026"]),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Officially corroborated by iitb.ac.in.",
        )

        dummy_run = verification_repo.create_run(self.user_id, "---TRANSCRIPT---\nTest", "rvpack")
        stages = [
            {"stage_name": "extracted", "status": "completed", "payload": extracted.model_dump(mode="json")},
            {"stage_name": "claims", "status": "completed", "payload": claims.model_dump(mode="json")},
            {"stage_name": "evidence", "status": "completed", "payload": evidence.model_dump(mode="json")},
            {"stage_name": "verdict", "status": "completed", "payload": verdict.model_dump(mode="json")},
        ]
        card = run_card_stage(dummy_run["id"], stages, self.user_id)
        self.assertEqual(card.badge, "OFFICIAL CORROBORATED")

    def test_scenario_2_unrelated_institution_rejected_as_evidence(self):
        """Scenario 2: Reputable but unrelated institution (.edu domain) is rejected."""
        extracted = ExtractedStagePayload(
            title="IIT Bombay AI Hackathon 2026",
            organizer="IIT Bombay",
        )
        cls_info = classify_source("https://mit.edu/robotics-competition", extracted.organizer, extracted.title)
        self.assertEqual(cls_info["source_type"], "unrelated_institution")

        is_rel, reason = is_substantively_relevant(
            ev_title="MIT Robotics 2026",
            ev_snippet="MIT hosts robotics challenge in Cambridge MA.",
            ev_url="https://mit.edu/robotics-competition",
            source_type=cls_info["source_type"],
            extracted=extracted,
        )
        self.assertFalse(is_rel)
        self.assertIn("Unrelated institution", reason)

    def test_scenario_3_generic_hackathon_directory_rejected_as_primary_evidence(self):
        """Scenario 3: Generic hackathon directory (Unstop, Devpost) rejected as primary evidence."""
        extracted = ExtractedStagePayload(
            title="IIT Bombay AI Hackathon 2026",
            organizer="IIT Bombay",
        )
        cls_info = classify_source("https://unstop.com/hackathons/unrelated-contest", extracted.organizer, extracted.title)
        self.assertEqual(cls_info["source_type"], "generic_directory")

        # 1. Unrelated generic directory search result is rejected
        is_rel, reason = is_substantively_relevant(
            ev_title="Top 10 Coding Hackathons on Unstop",
            ev_snippet="Browse popular hackathons across India.",
            ev_url="https://unstop.com/hackathons",
            source_type=cls_info["source_type"],
            extracted=extracted,
        )
        self.assertFalse(is_rel)
        self.assertIn("Generic directory", reason)

        # 2. Even when a generic directory has relevant listing, it CANNOT officially corroborate the event
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c1", claim_text="IIT Bombay AI Hackathon 2026", claim_type="event")]
        )
        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=["c1"],
                    url="https://unstop.com/hackathons/iitb-ai-hackathon",
                    title="IIT Bombay AI Hackathon on Unstop",
                    snippet="Student hackathon listing on Unstop directory.",
                    domain="unstop.com",
                    domain_trust="third_party",
                    source_type="generic_directory",
                )
            ],
            search_status="completed",
        )
        verdict = VerdictStagePayload(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="IIT Bombay AI Hackathon 2026", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Listed on Unstop directory.", cited_sources=["https://unstop.com/hackathons/iitb-ai-hackathon"]),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Listed on generic platform.",
        )
        dummy_run = verification_repo.create_run(self.user_id, "---TRANSCRIPT---\nTest", "rvpack")
        stages = [
            {"stage_name": "extracted", "status": "completed", "payload": extracted.model_dump(mode="json")},
            {"stage_name": "claims", "status": "completed", "payload": claims.model_dump(mode="json")},
            {"stage_name": "evidence", "status": "completed", "payload": evidence.model_dump(mode="json")},
            {"stage_name": "verdict", "status": "completed", "payload": verdict.model_dump(mode="json")},
        ]
        card = run_card_stage(dummy_run["id"], stages, self.user_id)
        # MUST NOT be officially corroborated; at best partially supported
        self.assertNotEqual(card.badge, "OFFICIAL CORROBORATED")
        self.assertEqual(card.badge, "PARTIALLY SUPPORTED")

    def test_scenario_4_different_years_disambiguated(self):
        """Scenario 4: Two events with similar names/years (2024 vs 2026) are disambiguated."""
        extracted = ExtractedStagePayload(
            title="IIT Bombay AI Hackathon 2026",
            organizer="IIT Bombay",
        )
        is_rel, reason = is_substantively_relevant(
            ev_title="IIT Bombay AI Hackathon 2024 Winners",
            ev_snippet="Congratulations to the winners of IIT Bombay AI Hackathon 2024.",
            ev_url="https://iitb.ac.in/events/ai-hackathon-2024",
            source_type="official_organizer",
            extracted=extracted,
        )
        self.assertFalse(is_rel)
        self.assertIn("edition/year", reason.lower())

    def test_scenario_5_source_supporting_organizer_only_leaves_fee_deadline_unverified(self):
        """Scenario 5: Source supporting organizer only leaves fee and deadline unverified."""
        extracted = ExtractedStagePayload(
            title="National CodeFest 2026",
            organizer="IIT Bombay",
        )
        claims = [
            ClaimItem(claim_id="c_org", claim_text="Organized by IIT Bombay", claim_type="organizer"),
            ClaimItem(claim_id="c_fee", claim_text="Registration fee of ₹500 is required.", claim_type="fee", is_fee_warning_claim=True),
            ClaimItem(claim_id="c_dl", claim_text="Application deadline is 15th December 2026.", claim_type="deadline"),
        ]
        matched = match_evidence_to_claims(
            ev_title="Indian Institute of Technology Bombay",
            ev_snippet="IIT Bombay is an autonomous public engineering and research institution located in Powai, Mumbai.",
            ev_url="https://iitb.ac.in/about",
            source_type="official_organizer",
            claims=claims,
            extracted=extracted,
        )
        self.assertIn("c_org", matched)
        self.assertNotIn("c_fee", matched)
        self.assertNotIn("c_dl", matched)

    def test_scenario_6_missing_and_fabricated_citations_sanitized(self):
        """Scenario 6: Missing citations and fabricated citation URLs sanitized and rejected."""
        real_url = "https://iitb.ac.in/event"
        fake_url = "https://fabricated-source-url.com/fake"

        claims = ClaimsStagePayload(claims=[ClaimItem(claim_id="c1", claim_text="IIT Bombay event", claim_type="event")])
        evidence = EvidenceStagePayload(evidence_items=[EvidenceItem(id="ev_1", url=real_url, domain="iitb.ac.in")])
        extracted = ExtractedStagePayload(title="IIT Bombay event")

        mock_eval = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(
                    claim_id="c1",
                    claim_text="IIT Bombay event",
                    verdict=ClaimVerdictLabel.SUPPORTED,
                    explanation="Claim evaluation",
                    cited_sources=[real_url, fake_url],
                )
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Evaluation",
        )
        mock_llm = MockLLM(response=mock_eval)
        verdict = run_verdict_stage(claims, evidence, extracted, llm_client=mock_llm)
        self.assertEqual(verdict.claim_verdicts[0].cited_sources, [real_url])
        self.assertNotIn(fake_url, verdict.claim_verdicts[0].cited_sources)

    def test_scenario_7_tavily_search_failure_preserves_partial_evidence(self):
        """Scenario 7: Search error preserves partial evidence and records bounded failure."""
        claims = ClaimsStagePayload(claims=[ClaimItem(claim_id="c1", claim_text="National AI Hackathon")])
        extracted = ExtractedStagePayload(
            title="National AI Hackathon 2026",
            organizer="IIT Bombay",
            links=["https://iitb.ac.in/ai-hackathon-2026"],
            search_queries=["IIT Bombay National AI Hackathon 2026 official"],
        )
        mock_tavily = MagicMock()
        mock_tavily.search.side_effect = RuntimeError("Connection timed out after 8.0s")

        evidence = run_evidence_stage(claims, extracted, tavily_client=mock_tavily)
        self.assertEqual(evidence.search_status, "failed")
        self.assertIn("failed", evidence.search_notes.lower())
        self.assertTrue(len(evidence.evidence_items) >= 1)
        self.assertEqual(evidence.evidence_items[0].url, "https://iitb.ac.in/ai-hackathon-2026")

    def test_scenario_8_re_running_completed_workflow_short_circuits(self):
        """Scenario 8: Re-running completed workflow short-circuits without duplicate API calls."""
        run = verification_repo.create_run(self.user_id, "---TRANSCRIPT---\nTest\n---ON_SCREEN---\nTest", "rvpack")
        run_id = run["id"]
        verification_repo.update_run(run_id, status="completed", completed_stages=["extracted", "claims", "evidence", "verdict", "card"])
        mock_llm = MockLLM()
        mock_tavily = MagicMock()

        result = execute_run(run_id, self.user_id, tavily_client=mock_tavily, llm_client=mock_llm)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(mock_llm.calls), 0)
        self.assertEqual(mock_tavily.search.call_count, 0)

    def test_scenario_9_badge_never_defaults_to_verified_without_official_source(self):
        """Scenario 9: Badge is never OFFICIAL CORROBORATED without verified official source."""
        extracted = ExtractedStagePayload(
            title="Dubious Hackathon 2026",
            organizer="Unverified organizer",
        )
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c1", claim_text="Dubious Hackathon 2026", claim_type="event")]
        )
        evidence = EvidenceStagePayload(
            evidence_items=[],
            search_status="completed",
        )
        verdict = VerdictStagePayload(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="Dubious Hackathon 2026", verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE, explanation="No corroboration found.", cited_sources=[]),
            ],
            overall_verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
            summary="No corroboration found.",
        )
        dummy_run = verification_repo.create_run(self.user_id, "---TRANSCRIPT---\nTest", "rvpack")
        stages = [
            {"stage_name": "extracted", "status": "completed", "payload": extracted.model_dump(mode="json")},
            {"stage_name": "claims", "status": "completed", "payload": claims.model_dump(mode="json")},
            {"stage_name": "evidence", "status": "completed", "payload": evidence.model_dump(mode="json")},
            {"stage_name": "verdict", "status": "completed", "payload": verdict.model_dump(mode="json")},
        ]
        card = run_card_stage(dummy_run["id"], stages, self.user_id)
        self.assertEqual(card.badge, "UNVERIFIED / INSUFFICIENT EVIDENCE")
        self.assertNotEqual(card.badge, "OFFICIAL CORROBORATED")
        self.assertNotEqual(card.badge, "VERIFIED")


class TestLiveGeminiIntegration(unittest.TestCase):
    """Optional live integration test making an actual call to Gemini API if key is present."""

    def test_live_gemini_call_if_configured(self):
        settings = get_settings()
        keys = settings.get_all_gemini_keys()
        if os.getenv("RUN_LIVE_TESTS") != "true" or not keys:
            self.skipTest("Live Gemini integration test skipped unless RUN_LIVE_TESTS=true.")

        rvpack = RVPackData(
            transcript="Microsoft Imagine Cup 2026 is now open. Registration deadline is 31st December 2026.",
            on_screen="Microsoft Imagine Cup\nRegister at https://imaginecup.microsoft.com",
            meta={"author": "microsoft_student_ambassadors"},
            raw_text="Microsoft Imagine Cup 2026 is now open. Registration deadline is 31st December 2026.",
            sections_found=["TRANSCRIPT", "ON_SCREEN", "META"],
        )

        extracted = run_extracted_stage(rvpack)
        self.assertIsNotNone(extracted.title)
        self.assertTrue(len(extracted.claims) > 0)
        self.assertEqual(extracted.author, "microsoft_student_ambassadors")
        self.assertNotEqual(extracted.organizer, "microsoft_student_ambassadors")


class TestGemini504AndTimeoutHandling(unittest.TestCase):
    """Verifies Requirement 1-7: Transient Gemini 504 handling, single retry, exhaustion, persistence, and 504 API error responses."""

    def setUp(self):
        from starlette.testclient import TestClient
        self.user_id = "test-timeout-user-504"
        self.mock_user = AuthUser(id=self.user_id, email="timeout-test@example.com", token="mock-token")
        app.dependency_overrides[current_user] = lambda: self.mock_user
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_gemini_504_retry_success(self):
        """Gemini raises 504 DEADLINE_EXCEEDED on attempt 1, succeeds on attempt 2 (retry success)."""
        mock_analysis = GeminiClaimAnalysis(
            title="National AI Hackathon 2026",
            organizer="IIT Bombay",
            author="tech_creator",
            category="hackathon",
            deadline_raw="15th December 2026",
            deadline_date="2026-12-15",
            has_fee=False,
            claims=[
                ClaimItem(claim_id="c1", claim_text="National AI Hackathon 2026", claim_type="event"),
                ClaimItem(claim_id="c2", claim_text="Organized by IIT Bombay", claim_type="organizer"),
            ],
            search_queries=["IIT Bombay National AI Hackathon 2026 official"],
        )
        # Attempt 1: 504 DEADLINE_EXCEEDED; Attempt 2: valid analysis
        mock_llm = MockLLM(responses=[
            RuntimeError("504 DEADLINE_EXCEEDED: Request timed out contacting upstream"),
            mock_analysis,
        ])

        rvpack = RVPackData(
            transcript="Join National AI Hackathon 2026 organized by IIT Bombay.",
            on_screen="IIT Bombay AI Hackathon\nhttps://iitb.ac.in",
            meta={"author": "tech_creator"},
            raw_text="Join National AI Hackathon 2026 organized by IIT Bombay.",
            sections_found=["TRANSCRIPT", "ON_SCREEN", "META"],
        )

        extracted = run_extracted_stage(rvpack, llm_client=mock_llm)

        # Verified: exactly 2 attempts made (initial + 1 retry)
        self.assertEqual(len(mock_llm.calls), 2)
        self.assertEqual(extracted.title, "National AI Hackathon 2026")
        self.assertEqual(extracted.organizer, "IIT Bombay")

    def test_gemini_504_retry_exhaustion_raises_504_app_error(self):
        """Gemini raises 504 on both attempt 1 and attempt 2, exhausting single retry and raising 504 AppError."""
        mock_llm = MockLLM(responses=[
            RuntimeError("504 DEADLINE_EXCEEDED: Request timed out"),
            RuntimeError("504 DEADLINE_EXCEEDED: Request timed out again on retry"),
            # An optional 3rd response should NEVER be consumed because retry is capped at 1
            RuntimeError("Unexpected 3rd attempt"),
        ])

        rvpack = RVPackData(
            transcript="Join National AI Hackathon 2026.",
            on_screen="IIT Bombay AI Hackathon",
            meta={"author": "creator"},
            raw_text="Join National AI Hackathon 2026.",
            sections_found=["TRANSCRIPT"],
        )

        with self.assertRaises(AppError) as ctx:
            run_extracted_stage(rvpack, llm_client=mock_llm)

        self.assertEqual(ctx.exception.status, 504)
        self.assertEqual(ctx.exception.code, "gemini_timeout")
        self.assertIn("504 DEADLINE_EXCEEDED", ctx.exception.message)
        # Bounded retry: exactly 2 attempts, no runaway retries
        self.assertEqual(len(mock_llm.calls), 2)

    def test_gemini_504_preserves_uploaded_rvpack_and_allows_resume(self):
        """Failed stage due to 504 preserves raw RVPack and allows resumption without repeating completed stages."""
        run = verification_repo.create_run(
            user_id=self.user_id,
            raw_input="---TRANSCRIPT---\nTest Event 2026 organized by Tech Corp\n---ON_SCREEN---\nTech Corp\n---META---\nauthor: tech_creator",
            input_type="rvpack",
        )
        run_id = run["id"]

        # Run fails at Stage 1 due to 504
        mock_llm_failing = MockLLM(responses=[
            RuntimeError("504 DEADLINE_EXCEEDED: Gateway Timeout"),
            RuntimeError("504 DEADLINE_EXCEEDED: Gateway Timeout"),
        ])

        with self.assertRaises(AppError) as ctx:
            execute_run(run_id, self.user_id, llm_client=mock_llm_failing)

        self.assertEqual(ctx.exception.status, 504)

        # Verify run state: RVPack preserved, status failed, no completed stages, no false card
        updated_run = verification_repo.get_run(run_id, self.user_id)
        self.assertIn("Test Event 2026", updated_run["raw_input"])
        self.assertEqual(updated_run["status"], "failed")
        self.assertIn("504 DEADLINE_EXCEEDED", updated_run.get("error_message", ""))
        self.assertEqual(len(verification_repo.list_stages(run_id)), 0)

        # Now resume: Stage 1 succeeds, stages 2-5 execute
        mock_analysis = GeminiClaimAnalysis(
            title="Test Event 2026",
            organizer="Tech Corp",
            claims=[ClaimItem(claim_id="c1", claim_text="Test Event 2026", claim_type="event")],
        )
        mock_verdict = GeminiVerdictEvaluation(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="Test Event 2026", verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE, explanation="Unverified externally", cited_sources=[]),
            ],
            overall_verdict=ClaimVerdictLabel.INSUFFICIENT_EVIDENCE,
            summary="Unverified externally",
        )
        mock_llm_success = MockLLM(responses=[mock_analysis, mock_verdict])
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = {"results": []}

        res = execute_run(run_id, self.user_id, llm_client=mock_llm_success, tavily_client=mock_tavily)
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["completed_stages"], ["extracted", "claims", "evidence", "verdict", "card"])
        self.assertIsNotNone(res["card"])

    def test_api_submit_rvpack_returns_504_not_500_on_timeout(self):
        """POST /v1/verification/rvpack returns HTTP 504 (not 500) when Gemini encounters 504 DEADLINE_EXCEEDED."""
        with patch("app.services.verification_workflow._invoke_structured_llm") as mock_invoke:
            mock_invoke.side_effect = AppError(
                "Gemini model request timed out (504 DEADLINE_EXCEEDED). You can retry or resume this verification run.",
                status=504,
                code="gemini_timeout",
            )

            res = self.client.post(
                "/v1/verification/rvpack",
                json={
                    "content": (
                        "---TRANSCRIPT---\n"
                        "National CodeFest 2026 organized by IIT Bombay.\n"
                        "---ON_SCREEN---\n"
                        "IIT Bombay CodeFest\n"
                    )
                },
            )
            self.assertEqual(res.status_code, 504)
            data = res.json()
            self.assertEqual(data["error"]["code"], "gemini_timeout")
            self.assertIn("504 DEADLINE_EXCEEDED", data["error"]["message"])

    def test_failed_extraction_does_not_create_card_or_mark_completed(self):
        """A failed extraction never marks run completed or generates an official opportunity card."""
        with patch("app.services.verification_workflow._invoke_structured_llm") as mock_invoke:
            mock_invoke.side_effect = AppError(
                "Gemini model request timed out (504 DEADLINE_EXCEEDED). You can retry or resume this verification run.",
                status=504,
                code="gemini_timeout",
            )

            res = self.client.post(
                "/v1/verification/rvpack",
                json={"content": "---TRANSCRIPT---\nIncomplete Event\n---ON_SCREEN---\nTest"},
            )
            self.assertEqual(res.status_code, 504)

            matching_runs = [r for r in verification_repo._fallback_store._runs.values() if r.get("user_id") == self.user_id]
            self.assertTrue(len(matching_runs) > 0)
            latest = matching_runs[-1]
            self.assertEqual(latest["status"], "failed")
            self.assertNotEqual(latest["status"], "completed")
            stages = verification_repo.list_stages(latest["id"])
            self.assertEqual(len(stages), 0)


class TestGeminiModelConfigAndWatchdogTimeouts(unittest.TestCase):
    """Verifies gemini-3-flash-preview configuration, configurable timeouts, prompt cleanup, and watchdog safety."""

    def test_configured_models_and_timeouts(self):
        """Settings configure gemini-3-flash-preview and consistent 30s HTTP / 35s watchdog timeouts."""
        s = get_settings()
        self.assertEqual(s.llm_model_fast, "gemini-3-flash-preview")
        self.assertEqual(s.llm_model_main, "gemini-3-flash-preview")
        self.assertEqual(s.gemini_http_timeout_s, 30.0)
        self.assertEqual(s.workflow_watchdog_timeout_s, 35.0)

    def test_extraction_prompt_removes_redundant_full_raw_text(self):
        """When transcript, on_screen, or meta are present, redundant FULL RAW TEXT is omitted from prompt."""
        mock_analysis = GeminiClaimAnalysis(
            title="Clean Prompt Event",
            organizer="Clean Org",
            claims=[ClaimItem(claim_id="c1", claim_text="Event claim", claim_type="event")],
        )
        mock_llm = MockLLM(response=mock_analysis)

        rvpack = RVPackData(
            transcript="Spoken words about the opportunity.",
            on_screen="Text on video frame.",
            meta={"author": "creator_name"},
            raw_text="---TRANSCRIPT---\nSpoken words about the opportunity.\n---ON_SCREEN---\nText on video frame.\n---META---\nauthor: creator_name",
            sections_found=["TRANSCRIPT", "ON_SCREEN", "META"],
        )

        run_extracted_stage(rvpack, llm_client=mock_llm)
        self.assertEqual(len(mock_llm.calls), 1)

        user_content = mock_llm.calls[0][1]["content"]
        self.assertIn("---TRANSCRIPT---", user_content)
        self.assertIn("---ON_SCREEN---", user_content)
        self.assertIn("---META---", user_content)
        self.assertNotIn("---FULL RAW TEXT---", user_content)
        self.assertNotIn("---RAW TEXT---", user_content)

    def test_extraction_prompt_includes_raw_text_when_sections_empty(self):
        """When structured sections are empty, raw text is included as fallback."""
        mock_analysis = GeminiClaimAnalysis(
            title="Fallback Event",
            organizer="Fallback Org",
            claims=[ClaimItem(claim_id="c1", claim_text="Fallback claim", claim_type="event")],
        )
        mock_llm = MockLLM(response=mock_analysis)

        rvpack = RVPackData(
            transcript="",
            on_screen="",
            meta={},
            raw_text="Unparsed opportunity announcement text.",
            sections_found=[],
        )

        run_extracted_stage(rvpack, llm_client=mock_llm)
        self.assertEqual(len(mock_llm.calls), 1)

        user_content = mock_llm.calls[0][1]["content"]
        self.assertIn("---RAW TEXT---", user_content)
        self.assertIn("Unparsed opportunity announcement text.", user_content)

    def test_watchdog_timeout_raises_504_app_error(self):
        """Watchdog timeout raises AppError with 504 status and gemini_timeout code."""
        import concurrent.futures

        mock_future = MagicMock()
        mock_future.result.side_effect = concurrent.futures.TimeoutError("Future watchdog timed out")

        with patch("app.services.verification_workflow._LLM_EXECUTOR.submit", return_value=mock_future):
            from app.services.verification_workflow import _invoke_structured_llm
            with self.assertRaises(AppError) as ctx:
                _invoke_structured_llm(
                    client=MagicMock(),
                    schema=GeminiClaimAnalysis,
                    messages=[{"role": "user", "content": "test"}],
                    max_retries=1,
                    backoff_s=0.01,
                )

            self.assertEqual(ctx.exception.status, 504)
            self.assertEqual(ctx.exception.code, "gemini_timeout")
            self.assertIn("504 DEADLINE_EXCEEDED", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
