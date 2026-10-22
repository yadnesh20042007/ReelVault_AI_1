import unittest
import uuid
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from app.errors import AppError
from app.schemas.reels import SavedDateIn
from app.schemas.verification import (
    OpportunityCardPayload,
    StageName,
    ClaimVerdictLabel,
)
from app.services.tools.domain_rules import (
    is_generic_root_url,
    verify_official_registration_link,
)
from app.services.verification_workflow import (
    _parse_deadline,
    run_card_stage,
    connect_deadline_to_vault,
)


class TestDateCorrectnessAndExtraction(unittest.TestCase):
    """
    Tests date correctness across all opportunity types:
    - Never treat 'Date unavailable', empty, or relative phrases as absolute dates without anchor.
    - Accurately normalize relative dates only with a reliable anchor date.
    - Reject impossible calendar dates (e.g. 2026-02-31).
    - Strictly validate Pydantic input schemas.
    """

    def test_placeholder_dates_rejected_for_all_categories(self):
        placeholders = [
            "Date unavailable",
            "not specified",
            "unknown",
            "soon",
            "coming soon",
            "tbd",
            "tba",
            "closed",
            "expired",
            "",
            "   ",
            "N/A",
            "none",
            "null",
        ]
        for ph in placeholders:
            res = _parse_deadline(ph, meta={})
            self.assertIsNone(
                res.date,
                f"Placeholder '{ph}' must not produce a calendar date.",
            )
            self.assertFalse(
                res.reminder_eligible,
                f"Placeholder '{ph}' must not be reminder eligible.",
            )

    def test_relative_date_without_anchor_never_substitutes_today(self):
        relative_phrases = [
            "7 days left",
            "in 3 days",
            "in 2 weeks",
            "2 days remaining",
            "closes tomorrow",
        ]
        for phrase in relative_phrases:
            res = _parse_deadline(phrase, meta={})
            self.assertIsNone(
                res.date,
                f"Relative phrase '{phrase}' without an anchor date must not produce a calendar date.",
            )
            self.assertFalse(res.reminder_eligible)

    def test_relative_date_with_reliable_anchor_normalizes_accurately(self):
        meta = {"posted": "2026-10-10T12:00:00Z"}
        res = _parse_deadline("7 days left", meta=meta)
        self.assertEqual(res.date, "2026-10-17")
        self.assertTrue(res.reminder_eligible)

        res_weeks = _parse_deadline("in 2 weeks", meta={"created_at": "2026-10-01"})
        self.assertEqual(res_weeks.date, "2026-10-15")
        self.assertTrue(res_weeks.reminder_eligible)

    def test_impossible_calendar_dates_rejected(self):
        invalid_dates = [
            "2026-02-31",  # Feb 31 does not exist
            "2026-04-31",  # Apr 31 does not exist
            "2026-13-01",  # Month 13
            "2026-00-10",  # Month 0
            "2026-05-32",  # Day 32
        ]
        for inv in invalid_dates:
            res = _parse_deadline(inv, meta={})
            self.assertIsNone(
                res.date,
                f"Impossible calendar date '{inv}' must be rejected.",
            )

    def test_saved_date_in_schema_validates_calendar_dates(self):
        # Valid date succeeds
        valid_in = SavedDateIn(
            label="Hackathon Registration",
            event_date="2026-11-15",
            title="Global AI Hackathon",
            url="https://hackathon.example.org/register",
        )
        self.assertEqual(valid_in.event_date, "2026-11-15")

        # Impossible calendar date raises ValidationError
        with self.assertRaises(ValidationError):
            SavedDateIn(
                label="Invalid Date",
                event_date="2026-02-31",
            )

        # Non-ISO string raises ValidationError
        with self.assertRaises(ValidationError):
            SavedDateIn(
                label="Invalid String",
                event_date="next Friday",
            )


class TestOfficialRegistrationAndSourceLinks(unittest.TestCase):
    """
    Tests official-link verification across hackathons, scholarships, internships, jobs, and competitions:
    - Generic root homepages (NVIDIA, Microsoft, Amazon, Harvard, IIT Bombay) are rejected as registration links.
    - Dedicated event domains and relevant event registration paths are verified.
    - Mismatched links are rejected.
    - Official registration links and supporting links are cleanly separated.
    """

    def test_generic_root_homepages_rejected_for_all_organizations(self):
        root_urls = [
            "https://www.nvidia.com",
            "https://nvidia.com/",
            "https://www.microsoft.com/en-us",
            "https://amazon.com",
            "https://www.harvard.edu/",
            "https://www.iitb.ac.in",
            "https://adobe.com",
            "https://google.com",
        ]
        for url in root_urls:
            self.assertTrue(
                is_generic_root_url(url),
                f"URL '{url}' should be identified as a generic root homepage.",
            )
            is_valid, status, reason = verify_official_registration_link(
                url,
                organizer="NVIDIA",
                title="Global Hackathon 2026",
            )
            self.assertFalse(
                is_valid,
                f"Generic root homepage '{url}' must not be accepted as an official registration link.",
            )
            self.assertEqual(status, "unable_to_verify")

    def test_dedicated_opportunity_domains_verified(self):
        dedicated_opportunities = [
            ("Google Summer of Code 2026", "Google", "https://summerofcode.withgoogle.com"),
            ("AI Founders Grant 2026", "AI Founders", "https://aifoundersgrant.org"),
        ]
        for title, organizer, url in dedicated_opportunities:
            is_valid, status, _ = verify_official_registration_link(url, organizer=organizer, title=title)
            self.assertTrue(
                is_valid,
                f"Dedicated opportunity domain '{url}' should be verified.",
            )
            self.assertEqual(status, "verified")

    def test_path_based_registration_links_verified_across_categories(self):
        opportunities = [
            # Hackathon
            ("NVIDIA AI World Hackathon 2026", "NVIDIA", "https://developer.nvidia.com/hackathons/ai-world-2026/register"),
            # Scholarship
            ("Tata Trust Merit Scholarship 2026", "Tata Trusts", "https://tatatrusts.org/scholarships/merit-2026/apply"),
            # Internship
            ("Microsoft Security Research Internship", "Microsoft", "https://careers.microsoft.com/students/us/en/internship-apply"),
            # Job
            ("DRDO Scientist Junior Fellow Recruitment", "DRDO", "https://drdo.gov.in/careers/fellowship-2026/application-form"),
        ]
        for title, organizer, url in opportunities:
            is_valid, status, _ = verify_official_registration_link(url, organizer=organizer, title=title)
            self.assertTrue(
                is_valid,
                f"Legitimate registration link '{url}' for '{title}' must be verified.",
            )
            self.assertEqual(status, "verified")

    def test_mismatched_unrelated_links_rejected(self):
        is_valid, status, _ = verify_official_registration_link(
            "https://amazon.com/gp/bestsellers/books",
            organizer="Amazon",
            title="Amazon Machine Learning Summer School 2026",
        )
        self.assertFalse(is_valid)
        self.assertEqual(status, "unable_to_verify")

    def test_run_card_stage_separates_official_and_supporting_links(self):
        run_id = str(uuid.uuid4())
        stages_records = [
            {
                "stage_name": StageName.EXTRACTED.value,
                "status": "completed",
                "payload": {
                    "title": "NVIDIA AI World Hackathon 2026",
                    "organizer": "NVIDIA",
                    "category": "hackathon",
                    "deadline": {"date": "2026-11-20", "raw": "2026-11-20", "reminder_eligible": True},
                    "links": ["https://developer.nvidia.com/hackathons/ai-world-2026/register"],
                },
            },
            {
                "stage_name": StageName.CLAIMS.value,
                "status": "completed",
                "payload": {"claims": []},
            },
            {
                "stage_name": StageName.EVIDENCE.value,
                "status": "completed",
                "payload": {
                    "evidence_items": [
                        {
                            "url": "https://developer.nvidia.com/hackathons/ai-world-2026/register",
                            "source_type": "official_organizer",
                            "domain_trust": "official_match",
                            "snippet": "Official registration page for NVIDIA AI World Hackathon 2026.",
                        },
                        {
                            "url": "https://techcrunch.com/2026/10/nvidia-hackathon-announcement",
                            "source_type": "news_outlet",
                            "domain_trust": "high",
                            "snippet": "TechCrunch news article reporting on the hackathon.",
                        },
                        {
                            "url": "https://www.nvidia.com",
                            "source_type": "official_organizer",
                            "domain_trust": "high",
                            "snippet": "Corporate homepage.",
                        },
                    ],
                },
            },
            {
                "stage_name": StageName.VERDICT.value,
                "status": "completed",
                "payload": {
                    "overall_verdict": ClaimVerdictLabel.SUPPORTED.value,
                    "claim_verdicts": [
                        {
                            "claim_id": "c1",
                            "claim_text": "Hackathon registration is open.",
                            "verdict": ClaimVerdictLabel.SUPPORTED.value,
                            "explanation": "Corroborated by official portal timeline.",
                            "cited_sources": ["https://developer.nvidia.com/hackathons/ai-world-2026/register"],
                        }
                    ],
                },
            },
        ]

        card = run_card_stage(run_id=run_id, stages_records=stages_records)

        # Official registration link is correctly isolated
        self.assertEqual(
            card.official_registration_url,
            "https://developer.nvidia.com/hackathons/ai-world-2026/register",
        )
        self.assertEqual(card.official_registration_status, "verified")

        # Supporting links do NOT contain the official registration link and exclude generic root homepages
        self.assertIn("https://techcrunch.com/2026/10/nvidia-hackathon-announcement", card.supporting_links)
        self.assertNotIn(card.official_registration_url, card.supporting_links)

    def test_run_card_stage_sets_unable_to_verify_when_only_root_homepages_exist(self):
        run_id = str(uuid.uuid4())
        stages_records = [
            {
                "stage_name": StageName.EXTRACTED.value,
                "status": "completed",
                "payload": {
                    "title": "NVIDIA AI Hackathon 2026",
                    "organizer": "NVIDIA",
                    "category": "hackathon",
                    "deadline": {"date": "2026-11-20", "raw": "2026-11-20", "reminder_eligible": True},
                    "links": ["https://www.nvidia.com"],
                },
            },
            {
                "stage_name": StageName.CLAIMS.value,
                "status": "completed",
                "payload": {"claims": []},
            },
            {
                "stage_name": StageName.EVIDENCE.value,
                "status": "completed",
                "payload": {
                    "evidence_items": [
                        {
                            "url": "https://www.nvidia.com",
                            "source_type": "official_organizer",
                            "domain_trust": "high",
                            "snippet": "Generic homepage.",
                        }
                    ],
                },
            },
            {
                "stage_name": StageName.VERDICT.value,
                "status": "completed",
                "payload": {
                    "overall_verdict": ClaimVerdictLabel.SUPPORTED.value,
                    "claim_verdicts": [],
                },
            },
        ]

        card = run_card_stage(run_id=run_id, stages_records=stages_records)

        # Root homepage is NOT set as official registration link
        self.assertIsNone(card.official_registration_url)
        self.assertEqual(card.official_registration_status, "unable_to_verify")


class TestCalendarPersistenceAndIsolation(unittest.TestCase):
    """
    Tests calendar reminder persistence and cross-opportunity isolation:
    - Rejects invalid or missing dates before persistence.
    - Does not report success if persistence fails.
    - Prevents cross-opportunity contamination (same label on another reel cannot hijack).
    - Preserves distinct identity across hackathons, scholarships, internships, jobs, competitions.
    """

    def setUp(self):
        self.user_id = "test-calendar-user-999"
        self.saved_dates_db = []
        self.runs_db = {}
        self.user_reels_db = {}
        self.id_counter = 500

    def _mock_save_date(self, user_id, reel_id, label, event_date):
        for d in self.saved_dates_db:
            if d.get("user_id") == user_id and d.get("user_reel_id") == reel_id and str(d.get("event_date")) == str(event_date):
                return d
        self.id_counter += 1
        entry = {
            "id": self.id_counter,
            "user_id": user_id,
            "user_reel_id": reel_id,
            "label": label,
            "event_date": str(event_date),
            "created_at": "2026-10-22T00:00:00Z",
        }
        self.saved_dates_db.append(entry)
        return entry

    def _mock_list_saved_dates(self, user_id):
        return [d for d in self.saved_dates_db if d.get("user_id") == user_id]

    def _mock_get_run(self, run_id, user_id=None):
        return self.runs_db.get(run_id)

    def _mock_get_stage(self, run_id, stage_name):
        run = self.runs_db.get(run_id)
        if run and "stages" in run and stage_name in run["stages"]:
            return run["stages"][stage_name]
        return None

    def _mock_save_stage(self, run_id, stage_name, stage_order, payload, status="completed"):
        if run_id in self.runs_db:
            self.runs_db[run_id]["stages"][stage_name] = {"payload": payload, "status": status}

    def _mock_get_user_reel(self, user_id, reel_id):
        return self.user_reels_db.get(reel_id)

    def test_connect_deadline_requires_valid_calendar_date(self):
        run_id = str(uuid.uuid4())
        card_data = {"title": "Test", "deadline": {"raw": "Date unavailable", "date": None, "vault_reminder_status": "not_connected"}}
        self.runs_db[run_id] = {
            "id": run_id,
            "user_id": self.user_id,
            "user_reel_id": 1,
            "card_payload": card_data,
            "stages": {"card": {"payload": card_data, "status": "completed"}},
        }
        self.user_reels_db[1] = {"id": 1, "user_id": self.user_id}

        with patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
             patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage):

            with self.assertRaises(ValueError) as ctx:
                connect_deadline_to_vault(
                    run_id=run_id,
                    user_id=self.user_id,
                    explicit_date="Date unavailable",
                )
            self.assertIn("Invalid date format", str(ctx.exception))

            with self.assertRaises(ValueError) as ctx:
                connect_deadline_to_vault(
                    run_id=run_id,
                    user_id=self.user_id,
                    explicit_date="2026-02-31",
                )
            self.assertIn("Invalid calendar date", str(ctx.exception))

    def test_persistence_failure_raises_error_and_does_not_mark_connected(self):
        run_id = str(uuid.uuid4())
        card_data = {
            "title": "Hackathon 2026",
            "deadline": {"date": "2026-11-15", "vault_reminder_status": "not_connected"},
        }
        self.runs_db[run_id] = {
            "id": run_id,
            "user_id": self.user_id,
            "user_reel_id": 42,
            "card_payload": card_data,
            "stages": {"card": {"payload": card_data, "status": "completed"}},
        }
        self.user_reels_db[42] = {"id": 42, "user_id": self.user_id}

        with patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
             patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
             patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
             patch("app.services.verification_workflow.main_repo.list_saved_dates", return_value=[]), \
             patch("app.services.verification_workflow.main_repo.save_date", side_effect=Exception("DB Connection Timeout")):

            with self.assertRaises(AppError) as ctx:
                connect_deadline_to_vault(
                    run_id=run_id,
                    user_id=self.user_id,
                    explicit_date="2026-11-15",
                )
            self.assertEqual(ctx.exception.code, "db_persistence_failed")
            # Card status is NOT marked connected
            self.assertEqual(card_data["deadline"]["vault_reminder_status"], "not_connected")

    def test_cross_opportunity_isolation_same_label_different_reels(self):
        # Opportunity 1: PayPal Hackathon (Reel 101)
        run_101 = str(uuid.uuid4())
        card_101 = {
            "title": "PayPal Global Hackathon",
            "deadline": {"date": "2026-11-20", "vault_reminder_status": "not_connected"},
        }
        self.runs_db[run_101] = {
            "id": run_101,
            "user_id": self.user_id,
            "user_reel_id": 101,
            "card_payload": card_101,
            "stages": {"card": {"payload": card_101, "status": "completed"}},
        }
        self.user_reels_db[101] = {"id": 101, "user_id": self.user_id}

        # Opportunity 2: AI Grant (Reel 102) with SAME default reminder label
        run_102 = str(uuid.uuid4())
        card_102 = {
            "title": "AI Founders Grant",
            "deadline": {"date": "2026-10-26", "vault_reminder_status": "not_connected"},
        }
        self.runs_db[run_102] = {
            "id": run_102,
            "user_id": self.user_id,
            "user_reel_id": 102,
            "card_payload": card_102,
            "stages": {"card": {"payload": card_102, "status": "completed"}},
        }
        self.user_reels_db[102] = {"id": 102, "user_id": self.user_id}

        with patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
             patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
             patch("app.services.verification_workflow.verification_repo.save_stage", side_effect=self._mock_save_stage), \
             patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
             patch("app.services.verification_workflow.main_repo.list_saved_dates", side_effect=self._mock_list_saved_dates), \
             patch("app.services.verification_workflow.main_repo.save_date", side_effect=self._mock_save_date):

            res_1 = connect_deadline_to_vault(
                run_id=run_101,
                user_id=self.user_id,
                explicit_date="2026-11-20",
            )
            self.assertTrue(res_1["success"])
            self.assertEqual(res_1["event_date"], "2026-11-20")
            self.assertEqual(res_1["reel_id"], 101)

            res_2 = connect_deadline_to_vault(
                run_id=run_102,
                user_id=self.user_id,
                explicit_date="2026-10-26",
            )
            self.assertTrue(res_2["success"])
            self.assertEqual(res_2["event_date"], "2026-10-26")
            self.assertEqual(res_2["reel_id"], 102)

        # Ensure both dates exist independently in the DB with distinct IDs and distinct reels
        self.assertEqual(len(self.saved_dates_db), 2)
        saved_101 = next(d for d in self.saved_dates_db if d["user_reel_id"] == 101)
        saved_102 = next(d for d in self.saved_dates_db if d["user_reel_id"] == 102)
        self.assertNotEqual(saved_101["id"], saved_102["id"])
        self.assertEqual(saved_101["event_date"], "2026-11-20")
        self.assertEqual(saved_102["event_date"], "2026-10-26")

    def test_multi_category_opportunities_preserve_calendar_identity(self):
        categories = [
            ("hackathon", 201, "Global AI Hackathon 2026", "2026-11-15"),
            ("scholarship", 202, "Women in Tech Scholarship", "2026-12-01"),
            ("internship", 203, "Open Source Fellowship Internship", "2026-10-30"),
            ("job", 204, "Junior AI Engineer Program", "2026-11-28"),
            ("competition", 205, "Autonomous Drone Challenge", "2026-12-10"),
        ]

        for cat, reel_id, title, date in categories:
            run_id = f"run-{reel_id}"
            card_data = {
                "title": title,
                "category": cat,
                "deadline": {"date": date, "vault_reminder_status": "not_connected"},
            }
            self.runs_db[run_id] = {
                "id": run_id,
                "user_id": self.user_id,
                "user_reel_id": reel_id,
                "card_payload": card_data,
                "stages": {"card": {"payload": card_data, "status": "completed"}},
            }
            self.user_reels_db[reel_id] = {"id": reel_id, "user_id": self.user_id}

        saved_results = []
        with patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
             patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
             patch("app.services.verification_workflow.verification_repo.save_stage", side_effect=self._mock_save_stage), \
             patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
             patch("app.services.verification_workflow.main_repo.list_saved_dates", side_effect=self._mock_list_saved_dates), \
             patch("app.services.verification_workflow.main_repo.save_date", side_effect=self._mock_save_date):

            for cat, reel_id, title, date in categories:
                res = connect_deadline_to_vault(
                    run_id=f"run-{reel_id}",
                    user_id=self.user_id,
                    explicit_date=date,
                )
                saved_results.append(res)

        self.assertEqual(len(saved_results), 5)
        # Verify each event preserved its own title, date, and reel identity
        for i, (cat, reel_id, title, date) in enumerate(categories):
            res = saved_results[i]
            self.assertEqual(res["reel_id"], reel_id)
            self.assertEqual(res["event_date"], date)


class TestRealAnalyzeOutputAndRootCauses(unittest.TestCase):
    """
    Regression tests covering root cause fixes for real analyze output:
    1. 'October 30' with reliable 2026 event context becomes 2026-10-30 with preserved provenance.
    2. An ambiguous date without sufficient year context is not assigned an invented year.
    3. A valid normalized date enables the calendar action.
    4. A placeholder or invalid date does not enable the action.
    5. Amazon's homepage is never accepted as the event's official registration URL without specific supporting evidence.
    6. A genuine, evidence-supported event registration URL can be verified.
    7. An unavailable registration URL does not prevent a valid deadline from being added to the calendar.
    8. Supporting links cannot accidentally become official registration links.
    """

    def test_october_30_with_reliable_2026_event_context_becomes_2026_10_30(self):
        # Case A: Year established in event announcement text
        reel_text = (
            "Hacktoberfest 2026 with Cestra Prizes and Merchandise. "
            "The event runs until October 30th. "
            "Comment on the post or check the bio for the registration link."
        )
        res = _parse_deadline("The event runs until October 30th", meta={"context_text": reel_text})
        self.assertEqual(res.date, "2026-10-30")
        self.assertFalse(res.year_ambiguous)
        self.assertTrue(res.reminder_eligible)
        self.assertIn("spoken in reel transcript", res.provenance or "")
        self.assertIn("2026", res.provenance or "")
        self.assertEqual(res.year_resolved_from, "contextual evidence (2026)")

        # Case B: Year established in meta title
        res_title = _parse_deadline(
            "October 30",
            meta={"title": "Hacktoberfest 2026 Announcement"},
        )
        self.assertEqual(res_title.date, "2026-10-30")
        self.assertFalse(res_title.year_ambiguous)
        self.assertTrue(res_title.reminder_eligible)

        # Case C: Year established in full raw text directly
        res_direct = _parse_deadline(reel_text, meta={})
        self.assertEqual(res_direct.date, "2026-10-30")
        self.assertFalse(res_direct.year_ambiguous)
        self.assertTrue(res_direct.reminder_eligible)

    def test_ambiguous_date_without_sufficient_year_context_is_not_assigned_invented_year(self):
        ambiguous_text = "The event runs until October 30th. Comment on the post or check the bio for the registration link."
        res = _parse_deadline(ambiguous_text, meta={})
        self.assertIsNone(
            res.date,
            "An ambiguous date without year context must not be assigned an invented year.",
        )
        self.assertTrue(res.year_ambiguous)
        self.assertFalse(res.reminder_eligible)
        self.assertEqual(res.vault_reminder_status, "not_connected")
        self.assertIn("spoken in reel transcript; year ambiguous", res.provenance or "")

    def test_valid_normalized_date_enables_calendar_action(self):
        run_id = str(uuid.uuid4())
        stages_records = [
            {
                "stage_name": StageName.EXTRACTED.value,
                "status": "completed",
                "payload": {
                    "title": "Hacktoberfest 2026",
                    "organizer": "Hacktoberfest",
                    "category": "hackathon",
                    "deadline": {
                        "date": "2026-10-30",
                        "raw": "October 30th",
                        "reminder_eligible": True,
                        "year_ambiguous": False,
                    },
                    "links": [],
                },
            },
            {
                "stage_name": StageName.CLAIMS.value,
                "status": "completed",
                "payload": {"claims": []},
            },
            {
                "stage_name": StageName.EVIDENCE.value,
                "status": "completed",
                "payload": {"evidence_items": []},
            },
            {
                "stage_name": StageName.VERDICT.value,
                "status": "completed",
                "payload": {
                    "overall_verdict": ClaimVerdictLabel.INSUFFICIENT_EVIDENCE.value,
                    "claim_verdicts": [],
                },
            },
        ]

        card = run_card_stage(run_id=run_id, stages_records=stages_records, user_reel_id=123)
        self.assertTrue(card.deadline.reminder_eligible)
        self.assertEqual(card.deadline.date, "2026-10-30")
        # Action is enabled: can_save_reminder is True and vault_reminder_action exists with 2026-10-30
        self.assertTrue(card.can_save_reminder)
        self.assertIsNotNone(card.vault_reminder_action)
        self.assertEqual(card.vault_reminder_action["event_date"], "2026-10-30")

    def test_placeholder_or_invalid_date_does_not_enable_action(self):
        run_id = str(uuid.uuid4())
        for invalid_raw in ["Date unavailable", "soon", "tbd", "2026-02-31"]:
            parsed = _parse_deadline(invalid_raw, meta={})
            stages_records = [
                {
                    "stage_name": StageName.EXTRACTED.value,
                    "status": "completed",
                    "payload": {
                        "title": "Hackathon",
                        "organizer": "Org",
                        "category": "hackathon",
                        "deadline": parsed.model_dump(mode="json"),
                        "links": [],
                    },
                },
                {
                    "stage_name": StageName.CLAIMS.value,
                    "status": "completed",
                    "payload": {"claims": []},
                },
                {
                    "stage_name": StageName.EVIDENCE.value,
                    "status": "completed",
                    "payload": {"evidence_items": []},
                },
                {
                    "stage_name": StageName.VERDICT.value,
                    "status": "completed",
                    "payload": {
                        "overall_verdict": ClaimVerdictLabel.INSUFFICIENT_EVIDENCE.value,
                        "claim_verdicts": [],
                    },
                },
            ]
            card = run_card_stage(run_id=run_id, stages_records=stages_records, user_reel_id=123)
            self.assertFalse(card.deadline.reminder_eligible)
            self.assertIsNone(card.deadline.date)
            # Calendar action is disabled
            self.assertFalse(card.can_save_reminder)
            self.assertIsNone(card.vault_reminder_action)

    def test_amazon_homepage_never_accepted_as_official_registration_url(self):
        # Direct verification check
        is_valid, status, reason = verify_official_registration_link(
            "https://www.amazon.com/",
            organizer="Hacktoberfest",
            title="Hacktoberfest 2026",
        )
        self.assertFalse(is_valid)
        self.assertEqual(status, "unable_to_verify")
        self.assertIn("Generic organization root homepage", reason)

        # Fallback analysis check: amazon.com is NOT placed in resources
        from app.services.reel_analysis import fallback_analysis
        fallback = fallback_analysis("Hacktoberfest with Amazon prize sponsorship", "")
        self.assertIsNotNone(fallback)
        res_urls = [r["url"] for r in fallback["resources"]]
        self.assertNotIn("https://www.amazon.com", res_urls)

    def test_genuine_evidence_supported_event_registration_url_can_be_verified(self):
        evidence = [
            {
                "url": "https://hacktoberfest.com/register",
                "source_type": "official_organizer",
                "domain_trust": "official_match",
                "snippet": "Register for Hacktoberfest 2026 official event.",
            }
        ]
        is_valid, status, reason = verify_official_registration_link(
            "https://hacktoberfest.com/register",
            organizer="Hacktoberfest",
            title="Hacktoberfest 2026",
            category="hackathon",
            evidence_items=evidence,
        )
        self.assertTrue(is_valid)
        self.assertEqual(status, "verified")

    def test_unavailable_registration_url_does_not_prevent_calendar_action(self):
        run_id = str(uuid.uuid4())
        stages_records = [
            {
                "stage_name": StageName.EXTRACTED.value,
                "status": "completed",
                "payload": {
                    "title": "Hacktoberfest 2026",
                    "organizer": "Hacktoberfest",
                    "category": "hackathon",
                    "deadline": {
                        "date": "2026-10-30",
                        "raw": "October 30th",
                        "reminder_eligible": True,
                        "year_ambiguous": False,
                    },
                    "links": ["https://www.amazon.com/"],  # Only generic corporate homepage discovered
                },
            },
            {
                "stage_name": StageName.CLAIMS.value,
                "status": "completed",
                "payload": {"claims": []},
            },
            {
                "stage_name": StageName.EVIDENCE.value,
                "status": "completed",
                "payload": {
                    "evidence_items": [
                        {
                            "url": "https://www.amazon.com/",
                            "source_type": "official_organizer",
                            "domain_trust": "high",
                            "snippet": "Amazon homepage",
                        }
                    ]
                },
            },
            {
                "stage_name": StageName.VERDICT.value,
                "status": "completed",
                "payload": {
                    "overall_verdict": ClaimVerdictLabel.INSUFFICIENT_EVIDENCE.value,
                    "claim_verdicts": [],
                },
            },
        ]

        card = run_card_stage(run_id=run_id, stages_records=stages_records, user_reel_id=456)
        # Registration URL is unable to verify
        self.assertIsNone(card.official_registration_url)
        self.assertEqual(card.official_registration_status, "unable_to_verify")

        # BUT calendar action is still enabled for the valid deadline!
        self.assertTrue(card.deadline.reminder_eligible)
        self.assertEqual(card.deadline.date, "2026-10-30")
        self.assertTrue(card.can_save_reminder)
        self.assertIsNotNone(card.vault_reminder_action)
        self.assertEqual(card.vault_reminder_action["event_date"], "2026-10-30")

    def test_supporting_links_cannot_accidentally_become_official_registration_links(self):
        run_id = str(uuid.uuid4())
        stages_records = [
            {
                "stage_name": StageName.EXTRACTED.value,
                "status": "completed",
                "payload": {
                    "title": "Hacktoberfest 2026",
                    "organizer": "Hacktoberfest",
                    "category": "hackathon",
                    "deadline": {"date": "2026-10-30", "raw": "2026-10-30", "reminder_eligible": True},
                    "links": [
                        "https://techcrunch.com/2026/hacktoberfest-announcement",
                        "https://github.com/hacktoberfest/starter-kit",
                    ],
                },
            },
            {
                "stage_name": StageName.CLAIMS.value,
                "status": "completed",
                "payload": {"claims": []},
            },
            {
                "stage_name": StageName.EVIDENCE.value,
                "status": "completed",
                "payload": {
                    "evidence_items": [
                        {
                            "url": "https://news.ycombinator.com/item?id=123",
                            "source_type": "news_outlet",
                            "domain_trust": "medium",
                            "snippet": "Discussion",
                        }
                    ]
                },
            },
            {
                "stage_name": StageName.VERDICT.value,
                "status": "completed",
                "payload": {
                    "overall_verdict": ClaimVerdictLabel.PARTIALLY_SUPPORTED.value,
                    "claim_verdicts": [],
                },
            },
        ]

        card = run_card_stage(run_id=run_id, stages_records=stages_records)
        # Supporting news links cannot become official registration URL
        self.assertIsNone(card.official_registration_url)
        self.assertEqual(card.official_registration_status, "unable_to_verify")
        # Supporting links contain the news/starter-kit links
        self.assertIn("https://news.ycombinator.com/item?id=123", card.supporting_links)


if __name__ == "__main__":
    unittest.main()

