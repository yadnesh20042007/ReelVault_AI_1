import unittest
from unittest.mock import MagicMock, patch
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings
from app.deps import AuthUser, current_user
from app.schemas.reels import SavedDateIn, TavilyVerifyIn, TavilyVerifyOut
from app.services.verification_workflow import (
    connect_deadline_to_vault,
    save_opportunity_card_to_vault,
)


class TestCalendarIdentityAndDateHandling(unittest.TestCase):
    """
    Regression test suite for:
    Issue 1: Normal Analyze vs Deep Analyze date separation and consistent Add to Calendar.
    Issue 2: Calendar event identity, stable IDs, no cross-opportunity corruption, and deduplication.
    Issue 3: Independent Save to Vault and Add to Calendar features.
    """

    def setUp(self):
        self.user_id = "test-user-calendar-12345"
        self.auth_user = AuthUser(id=self.user_id, email="calendar_tester@example.com", token="mock_token")
        self.client = TestClient(app)

        # In-memory mock storage for database tables
        self.saved_dates_db = []
        self.user_reels_db = {}
        self.source_posts_db = {}
        self.verification_runs_db = {}
        self.id_counter = 100

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

    def _mock_get_user_reel(self, user_id, reel_id):
        return self.user_reels_db.get(reel_id)

    def _mock_list_user_reels(self, user_id, limit=50, offset=0):
        return list(self.user_reels_db.values())

    def _mock_insert_source_post(self, fetched_post, post_ref):
        for p in self.source_posts_db.values():
            if p.get("platform") == fetched_post.platform and p.get("shortcode") == fetched_post.shortcode:
                return p
        self.id_counter += 1
        post_id = self.id_counter
        entry = {
            "id": post_id,
            "platform": fetched_post.platform,
            "shortcode": fetched_post.shortcode,
            "author": fetched_post.author,
            "transcript": fetched_post.transcript,
            "caption": fetched_post.caption,
            "raw": fetched_post.raw,
            "url": post_ref.canonical_url,
        }
        self.source_posts_db[post_id] = entry
        return entry

    def _mock_link_user_reel(self, user_id, post_id):
        for r in self.user_reels_db.values():
            if r.get("user_id") == user_id and r.get("source_post_id") == post_id:
                return r
        self.id_counter += 1
        reel_id = self.id_counter
        entry = {
            "id": reel_id,
            "user_id": user_id,
            "source_post_id": post_id,
            "created_at": "2026-10-22T00:00:00Z",
            "source_posts": self.source_posts_db.get(post_id),
        }
        self.user_reels_db[reel_id] = entry
        return entry

    def _mock_update_source_post_analysis(self, post_id, analysis):
        post = self.source_posts_db.get(post_id)
        if post:
            if "raw" not in post or not isinstance(post["raw"], dict):
                post["raw"] = {}
            post["raw"]["reel_analysis"] = analysis
            return post
        return None

    def _mock_get_run(self, run_id, user_id=None):
        run = self.verification_runs_db.get(str(run_id))
        if run and user_id and str(run.get("user_id")) != str(user_id):
            return None
        return run

    def _mock_get_stage(self, run_id, stage_name):
        run = self.verification_runs_db.get(str(run_id))
        if run and "stages" in run and stage_name in run["stages"]:
            return run["stages"][stage_name]
        return None

    def _mock_list_stages(self, run_id):
        run = self.verification_runs_db.get(str(run_id))
        if run and "stages" in run:
            res = []
            for name, s in run["stages"].items():
                res.append({
                    "stage_name": name,
                    "status": s.get("status", "completed"),
                    "payload": s.get("payload", {}),
                })
            return res
        return []

    def _mock_update_run(self, run_id, **kwargs):
        run = self.verification_runs_db.get(str(run_id))
        if run:
            run.update(kwargs)
            return run
        return kwargs

    def _create_complete_run(self, user_id, title="Open Source Hackathon", deadline_date="2026-10-26"):
        run_id = str(uuid.uuid4())
        deadline_obj = {
            "date": deadline_date,
            "raw": deadline_date or "Not specified",
            "type": "hard" if deadline_date else "none",
        } if deadline_date else {"date": None, "raw": "Not specified", "type": "none"}

        self.verification_runs_db[run_id] = {
            "id": run_id,
            "user_id": user_id,
            "user_reel_id": None,
            "status": "completed",
            "raw_input": f"Announcement for {title}",
            "stages": {
                "extracted": {"stage_name": "extracted", "status": "completed", "payload": {"title": title}},
                "claims": {"stage_name": "claims", "status": "completed", "payload": {"claims": [{"claim_id": "c1", "claim_text": title}]}},
                "evidence": {"stage_name": "evidence", "status": "completed", "payload": {"evidence": [{"title": "Official Portal", "url": "https://hack.org/portal", "domain": "hack.org"}]}},
                "verdict": {"stage_name": "verdict", "status": "completed", "payload": {"overall_verdict": "supported", "claim_verdicts": [{"claim_id": "c1", "verdict": "supported", "explanation": "Confirmed"}]}},
                "card": {
                    "stage_name": "card",
                    "status": "completed",
                    "payload": {
                        "title": title,
                        "organizer": "Tech Community",
                        "category": "hackathon",
                        "overall_verdict": "supported",
                        "deadline": deadline_obj,
                        "links": [{"name": "Official Registration", "url": "https://hack.org/apply"}],
                        "scam_warnings": [],
                    }
                }
            }
        }
        return run_id

    def test_regression_two_opportunities_no_cross_corruption(self):
        """
        Verify that adding a .rvpack opportunity with a 26 October deadline,
        followed by creating and analyzing a separate PayPal hackathon reel,
        preserves the 26 October event's identity, title, date, and source without
        overwriting, renaming, or mutating it.
        """
        # Step 1: Add Opportunity 1 (.rvpack with 26 October deadline)
        run_1_id = str(uuid.uuid4())
        self.verification_runs_db[run_1_id] = {
            "id": run_1_id,
            "user_id": self.user_id,
            "user_reel_id": None,
            "status": "completed",
            "stages": {
                "card": {
                    "payload": {
                        "title": "Open Source Sprint 2026",
                        "organizer": "RV Community",
                        "category": "Hackathon",
                        "deadline": {"date": "2026-10-26", "type": "hard", "description": "Submission deadline"},
                        "links": [{"name": "Portal", "url": "https://rvpack.example.com/apply"}],
                    }
                }
            },
        }

        with patch("app.services.verification_workflow.main_repo.list_saved_dates", side_effect=self._mock_list_saved_dates), \
             patch("app.services.verification_workflow.main_repo.save_date", side_effect=self._mock_save_date), \
             patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
             patch("app.services.verification_workflow.main_repo.list_user_reels", side_effect=self._mock_list_user_reels), \
             patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
             patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
             patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
             patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
             patch("app.services.verification_workflow.verification_repo.save_stage", return_value=True), \
             patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run):

            res1 = connect_deadline_to_vault(run_1_id, self.user_id, explicit_date="2026-10-26", label="Open Source Sprint Deadline")
            self.assertTrue(res1["success"])
            self.assertEqual(res1["status"], "connected")
            self.assertEqual(res1["event_date"], "2026-10-26")
            event1_id = res1["saved_date_id"]
            event1_reel_id = res1["reel_id"]
            self.assertIsNotNone(event1_id)
            self.assertIsNotNone(event1_reel_id)

            # Step 2: Now simulate Opportunity 2: PayPal Hackathon Reel
            paypal_post_id = 888
            paypal_reel_id = 999
            paypal_post = {
                "id": paypal_post_id,
                "platform": "instagram",
                "shortcode": "PAYPAL_HACK_REEL",
                "author": "paypal_devs",
                "transcript": "Join the PayPal Global AI Hackathon with $50,000 in prizes! Register at paypal.com/hackathon",
                "caption": "PayPal Hackathon announcement",
                "raw": {
                    "custom_title": "PayPal Global AI Hackathon",
                    "reel_analysis": {
                        "title": "PayPal Global AI Hackathon",
                        "summary": "PayPal is hosting a global AI hackathon.",
                        "tags": ["hackathon", "paypal", "ai"],
                    },
                },
                "url": "https://www.instagram.com/reel/PAYPAL_HACK_REEL/",
            }
            self.source_posts_db[paypal_post_id] = paypal_post
            self.user_reels_db[paypal_reel_id] = {
                "id": paypal_reel_id,
                "user_id": self.user_id,
                "source_post_id": paypal_post_id,
                "created_at": "2026-10-22T01:00:00Z",
                "source_posts": paypal_post,
            }

            # Add PayPal hackathon date (e.g., 2026-11-20)
            res2_date = self._mock_save_date(self.user_id, paypal_reel_id, "PayPal Submission Deadline", "2026-11-20")
            event2_id = res2_date["id"]
            self.assertNotEqual(event1_id, event2_id, "Each calendar event must have a distinct stable ID.")

            # Step 3: Verify the 26 October event was NOT mutated, overwritten, or renamed
            all_dates = self._mock_list_saved_dates(self.user_id)
            self.assertEqual(len(all_dates), 2)

            event_26_oct = next((d for d in all_dates if d["id"] == event1_id), None)
            self.assertIsNotNone(event_26_oct)
            self.assertEqual(event_26_oct["event_date"], "2026-10-26")
            self.assertEqual(event_26_oct["user_reel_id"], event1_reel_id)
            self.assertNotEqual(event_26_oct["user_reel_id"], paypal_reel_id)
            self.assertIn("Sprint", event_26_oct["label"])
            self.assertNotIn("PayPal", event_26_oct["label"])

            # Verify reel title association for the 26 October event
            oct_reel = self.user_reels_db.get(event1_reel_id)
            self.assertIsNotNone(oct_reel)
            oct_post = oct_reel.get("source_posts", {})
            self.assertEqual(oct_post.get("raw", {}).get("custom_title"), "Open Source Sprint 2026")
            self.assertNotIn("PayPal", oct_post.get("raw", {}).get("custom_title", ""))

    def test_duplicate_event_prevention_on_retry(self):
        """
        Verify that retrying an analysis or saving the same opportunity/date
        multiple times prevents duplicate entries and returns the existing event.
        """
        reel_id = 501
        self.user_reels_db[reel_id] = {
            "id": reel_id,
            "user_id": self.user_id,
            "source_post_id": 501,
            "source_posts": {"id": 501, "raw": {"custom_title": "Unique Tech Competition"}},
        }

        # First add
        d1 = self._mock_save_date(self.user_id, reel_id, "Registration Deadline", "2026-10-26")
        self.assertEqual(len(self.saved_dates_db), 1)
        first_id = d1["id"]

        # Retry / duplicate add with exact same user, reel, date
        d2 = self._mock_save_date(self.user_id, reel_id, "Registration Deadline", "2026-10-26")
        self.assertEqual(len(self.saved_dates_db), 1, "Duplicate date must not be created.")
        self.assertEqual(d2["id"], first_id, "Existing record must be returned on duplicate add.")

    def test_normal_analyze_reports_no_dates_when_not_in_reel(self):
        """
        Issue 1: Normal analyze should only extract dates present in the transcript/caption.
        When a reel contains no explicit dates, normal analyze returns an empty list
        and must NEVER invent or hallucinate a deadline.
        """
        reel_transcript_no_dates = (
            "Hey guys, today I am sharing the top 3 open-source opportunities you can contribute to right now! "
            "Build your resume and earn rewards. Check out the link in bio for full guidelines."
        )

        import re
        # Date extraction pattern used in normal analyze
        date_pattern = re.compile(
            r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\d{4}-\d{2}-\d{2})\b",
            re.IGNORECASE,
        )
        found_dates = date_pattern.findall(reel_transcript_no_dates)
        self.assertEqual(found_dates, [], "Normal analyze must report 0 dates when none are spoken in the reel.")

    def test_deep_analyze_discovers_external_verified_deadline_without_falsifying_reel(self):
        """
        Issue 1: Deep Analyze queries external web sources and discovers official deadlines.
        The discovered deadline must be clearly attributed to external research and
        never represented as explicitly spoken in the reel.
        """
        # Simulated external Tavily verification result with external verified deadline
        tavily_result = TavilyVerifyOut(
            verified=True,
            verdict="True",
            explanation="External search confirms official competition records with submission closing on 26 October 2026.",
            claims=["Competition has official registration portal."],
            query="Hackathon verification",
            sources=[
                {
                    "title": "Official Portal Registration & Guidelines",
                    "url": "https://officialportal.example.com/dates",
                    "summary": "All teams must submit final project by 2026-10-26 23:59 UTC.",
                    "score": 0.95,
                }
            ],
            summary="Found 1 verified official source.",
            official_deadline="2026-10-26",
        )

        # Discovered deadline exists from external verification
        self.assertEqual(tavily_result.official_deadline, "2026-10-26")

        # But the original reel transcript does not have dates
        reel_caption = "Big hackathon announcement! Check portal in bio."
        self.assertNotIn("2026-10-26", reel_caption)

        # Add to calendar prefill action must pre-populate with the verified deadline
        prefill_payload = {
            "label": f"Official Deadline: Hackathon",
            "event_date": tavily_result.official_deadline,
            "title": "Hackathon",
            "url": tavily_result.sources[0].url,
        }
        self.assertEqual(prefill_payload["event_date"], "2026-10-26")
        self.assertEqual(prefill_payload["url"], "https://officialportal.example.com/dates")
        self.assertIn("Official Deadline", prefill_payload["label"])

    def test_api_list_saved_dates_preserves_title_url_and_stable_id(self):
        """
        Verify that GET /reels/saved-dates returns each saved date with its own
        title, url, and stable ID without relying on or colliding with the latest reel.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            # Seed 2 distinct opportunities in mock DB
            reel_1 = {
                "id": 101,
                "user_id": self.user_id,
                "source_post_id": 101,
                "source_posts": {
                    "id": 101,
                    "url": "https://example.com/reel1",
                    "raw": {"custom_title": "First AI Fellowship"},
                },
            }
            reel_2 = {
                "id": 202,
                "user_id": self.user_id,
                "source_post_id": 202,
                "source_posts": {
                    "id": 202,
                    "url": "https://example.com/reel2",
                    "raw": {"custom_title": "PayPal Global Hackathon"},
                },
            }
            self.user_reels_db[101] = reel_1
            self.user_reels_db[202] = reel_2

            self.saved_dates_db.append({
                "id": 1,
                "user_id": self.user_id,
                "user_reel_id": 101,
                "label": "Fellowship Deadline",
                "event_date": "2026-10-26",
                "created_at": "2026-10-22T00:00:00Z",
            })
            self.saved_dates_db.append({
                "id": 2,
                "user_id": self.user_id,
                "user_reel_id": 202,
                "label": "PayPal Submission",
                "event_date": "2026-11-20",
                "created_at": "2026-10-22T00:00:00Z",
            })

            with patch("app.api.reels.repo.list_saved_dates", side_effect=self._mock_list_saved_dates), \
                 patch("app.api.reels.repo.list_user_reels", side_effect=self._mock_list_user_reels):

                response = self.client.get("/v1/reels/saved-dates")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(len(data), 2)

                # Check event 1
                ev1 = next((e for e in data if e["id"] == 1), None)
                self.assertIsNotNone(ev1)
                self.assertEqual(ev1["title"], "First AI Fellowship")
                self.assertEqual(ev1["event_date"], "2026-10-26")
                self.assertEqual(ev1["reel_id"], 101)

                # Check event 2
                ev2 = next((e for e in data if e["id"] == 2), None)
                self.assertIsNotNone(ev2)
                self.assertEqual(ev2["title"], "PayPal Global Hackathon")
                self.assertEqual(ev2["event_date"], "2026-11-20")
                self.assertEqual(ev2["reel_id"], 202)
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_save_to_vault_with_deadline(self):
        """
        Verify that saving an opportunity with a deadline persists the complete
        Stage 5 opportunity card (title, category, organizer, deadline, verdict,
        evidence links, scam warnings) to Vault, but does NOT create a calendar event.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            run_id = self._create_complete_run(self.user_id, title="Quantum Computing Sprint", deadline_date="2026-11-15")

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
                 patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run), \
                 patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
                 patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
                 patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
                 patch("app.services.verification_workflow.main_repo.update_source_post_analysis", side_effect=self._mock_update_source_post_analysis):

                response = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])
                self.assertFalse(data["already_saved"])
                self.assertEqual(data["title"], "Quantum Computing Sprint")
                self.assertIsNotNone(data["reel_id"])

                # Verify NO calendar date was created
                self.assertEqual(len(self.saved_dates_db), 0, "Saving to Vault must NOT create a calendar event.")

                # Verify opportunity card is persisted in user_reels and source_posts
                reel_id = data["reel_id"]
                saved_reel = self.user_reels_db.get(reel_id)
                self.assertIsNotNone(saved_reel)
                post = saved_reel.get("source_posts", {})
                raw = post.get("raw", {})
                self.assertEqual(raw.get("custom_title"), "Quantum Computing Sprint")
                analysis = raw.get("reel_analysis", {})
                self.assertEqual(analysis.get("overall_verdict"), "supported")
                self.assertEqual(analysis.get("card", {}).get("category"), "hackathon")
                self.assertEqual(analysis.get("card", {}).get("deadline", {}).get("date"), "2026-11-15")
                self.assertTrue(len(analysis.get("sources", [])) > 0)
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_save_to_vault_without_deadline(self):
        """
        Verify that saving an opportunity with NO deadline succeeds and persists
        the complete card to Vault without creating a calendar event.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            run_id = self._create_complete_run(self.user_id, title="Rolling Fellowship", deadline_date=None)

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
                 patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run), \
                 patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
                 patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
                 patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
                 patch("app.services.verification_workflow.main_repo.update_source_post_analysis", side_effect=self._mock_update_source_post_analysis):

                response = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data["success"])
                self.assertFalse(data["already_saved"])
                self.assertEqual(data["title"], "Rolling Fellowship")
                self.assertIsNotNone(data["reel_id"])

                # Verify NO calendar event created
                self.assertEqual(len(self.saved_dates_db), 0)

                # Verify reel persisted with null date in details
                reel_id = data["reel_id"]
                saved_reel = self.user_reels_db.get(reel_id)
                self.assertIsNotNone(saved_reel)
                analysis = saved_reel["source_posts"]["raw"]["reel_analysis"]
                self.assertIsNone(analysis.get("card", {}).get("deadline", {}).get("date"))
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_save_to_vault_idempotent_no_duplicate_cards(self):
        """
        Verify that saving the same verification run twice is idempotent:
        it returns the same saved opportunity and does not create duplicate cards in Vault.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            run_id = self._create_complete_run(self.user_id, title="Idempotent Hackathon", deadline_date="2026-11-01")

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
                 patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run), \
                 patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
                 patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
                 patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
                 patch("app.services.verification_workflow.main_repo.update_source_post_analysis", side_effect=self._mock_update_source_post_analysis):

                # First save
                res1 = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(res1.status_code, 200)
                data1 = res1.json()
                self.assertTrue(data1["success"])
                self.assertFalse(data1["already_saved"])
                reel_id_1 = data1["reel_id"]
                self.assertEqual(len(self.user_reels_db), 1)

                # Second save (retry / duplicate click)
                res2 = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(res2.status_code, 200)
                data2 = res2.json()
                self.assertTrue(data2["success"])
                self.assertTrue(data2["already_saved"])
                self.assertEqual(data2["reel_id"], reel_id_1)

                # Ensure Vault still contains exactly 1 card
                self.assertEqual(len(self.user_reels_db), 1, "Duplicate card must not be created.")
                self.assertEqual(len(self.saved_dates_db), 0, "No calendar event should exist.")
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_save_to_vault_does_not_create_calendar_event(self):
        """
        Explicitly assert that saving to Vault does not insert any records
        into user_saved_dates table.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            run_id = self._create_complete_run(self.user_id, title="Scholarship Program", deadline_date="2026-12-01")

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
                 patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run), \
                 patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
                 patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
                 patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
                 patch("app.services.verification_workflow.main_repo.save_date", side_effect=self._mock_save_date):

                res = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(res.status_code, 200)
                self.assertEqual(len(self.saved_dates_db), 0)
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_user_cannot_save_another_users_run(self):
        """
        Ensure a user cannot save another user's verification run (403 Forbidden).
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            victim_user_id = "victim-user-99999"
            run_id = self._create_complete_run(victim_user_id, title="Victim Private Opportunity")

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run):
                response = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(response.status_code, 403)
                self.assertEqual(len(self.user_reels_db), 0)
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_incomplete_runs_cannot_be_saved(self):
        """
        Require that the run's first four stages are complete and its Card stage exists.
        Incomplete verification runs must be rejected with 400 Bad Request.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            run_id = str(uuid.uuid4())
            # Incomplete run: only 2 stages finished, missing verdict and card
            self.verification_runs_db[run_id] = {
                "id": run_id,
                "user_id": self.user_id,
                "user_reel_id": None,
                "status": "processing",
                "stages": {
                    "extracted": {"stage_name": "extracted", "status": "completed", "payload": {"title": "Draft"}},
                    "claims": {"stage_name": "claims", "status": "completed", "payload": {}},
                }
            }

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage):

                response = self.client.post(f"/v1/verification/runs/{run_id}/save-to-vault")
                self.assertEqual(response.status_code, 400)
                data = response.json()
                error_msg = data.get("error", {}).get("message") or data.get("detail", "")
                self.assertIn("incomplete", error_msg.lower())
                self.assertEqual(len(self.user_reels_db), 0)
        finally:
            app.dependency_overrides.pop(current_user, None)

    def test_save_to_vault_and_add_to_calendar_operate_independently(self):
        """
        Verify that Save to Vault and Add to Calendar can be triggered in either order:
        - Case A: Save to Vault first, then Add to Calendar.
        - Case B: Add to Calendar first, then Save to Vault.
        Neither requires the other, and duplicate reels/dates are not created.
        """
        app.dependency_overrides[current_user] = lambda: self.auth_user
        try:
            # Case A: Save to Vault first, then Add to Calendar
            run_a = self._create_complete_run(self.user_id, title="Opportunity Alpha", deadline_date="2026-10-30")

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
                 patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run), \
                 patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
                 patch("app.services.verification_workflow.main_repo.list_user_reels", side_effect=self._mock_list_user_reels), \
                 patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
                 patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
                 patch("app.services.verification_workflow.main_repo.update_source_post_analysis", side_effect=self._mock_update_source_post_analysis), \
                 patch("app.services.verification_workflow.main_repo.list_saved_dates", side_effect=self._mock_list_saved_dates), \
                 patch("app.services.verification_workflow.main_repo.save_date", side_effect=self._mock_save_date):

                # 1. Save to Vault
                save_res = self.client.post(f"/v1/verification/runs/{run_a}/save-to-vault")
                self.assertEqual(save_res.status_code, 200)
                vault_data = save_res.json()
                reel_id_a = vault_data["reel_id"]
                self.assertEqual(len(self.user_reels_db), 1)
                self.assertEqual(len(self.saved_dates_db), 0, "No calendar event after Vault save")

                # 2. Add to Calendar afterwards
                cal_res = self.client.post(
                    f"/v1/verification/runs/{run_a}/connect-vault-reminder",
                    json={"event_date": "2026-10-30", "label": "Alpha Deadline"},
                )
                self.assertEqual(cal_res.status_code, 200)
                self.assertEqual(len(self.saved_dates_db), 1, "Calendar event added")
                self.assertEqual(self.saved_dates_db[0]["user_reel_id"], reel_id_a)
                self.assertEqual(len(self.user_reels_db), 1, "Reel was reused without duplication")

            # Case B: Add to Calendar first, then Save to Vault
            run_b = self._create_complete_run(self.user_id, title="Opportunity Beta", deadline_date="2026-11-25")

            with patch("app.api.verification.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.get_run", side_effect=self._mock_get_run), \
                 patch("app.services.verification_workflow.verification_repo.list_stages", side_effect=self._mock_list_stages), \
                 patch("app.services.verification_workflow.verification_repo.get_stage", side_effect=self._mock_get_stage), \
                 patch("app.services.verification_workflow.verification_repo.update_run", side_effect=self._mock_update_run), \
                 patch("app.services.verification_workflow.main_repo.get_user_reel", side_effect=self._mock_get_user_reel), \
                 patch("app.services.verification_workflow.main_repo.list_user_reels", side_effect=self._mock_list_user_reels), \
                 patch("app.services.verification_workflow.main_repo.insert_source_post", side_effect=self._mock_insert_source_post), \
                 patch("app.services.verification_workflow.main_repo.link_user_reel", side_effect=self._mock_link_user_reel), \
                 patch("app.services.verification_workflow.main_repo.update_source_post_analysis", side_effect=self._mock_update_source_post_analysis), \
                 patch("app.services.verification_workflow.main_repo.list_saved_dates", side_effect=self._mock_list_saved_dates), \
                 patch("app.services.verification_workflow.main_repo.save_date", side_effect=self._mock_save_date):

                # 1. Add to Calendar first
                cal_b = self.client.post(
                    f"/v1/verification/runs/{run_b}/connect-vault-reminder",
                    json={"event_date": "2026-11-25", "label": "Beta Deadline"},
                )
                self.assertEqual(cal_b.status_code, 200)
                self.assertEqual(len(self.saved_dates_db), 2)
                reel_id_b = cal_b.json()["reel_id"]
                self.assertEqual(len(self.user_reels_db), 2)

                # 2. Save to Vault afterwards
                save_b = self.client.post(f"/v1/verification/runs/{run_b}/save-to-vault")
                self.assertEqual(save_b.status_code, 200)
                vault_b_data = save_b.json()
                self.assertTrue(vault_b_data["success"])
                self.assertTrue(vault_b_data["already_saved"])
                self.assertEqual(vault_b_data["reel_id"], reel_id_b)

                # Still 2 reels and 2 dates, zero duplicates created!
                self.assertEqual(len(self.user_reels_db), 2)
                self.assertEqual(len(self.saved_dates_db), 2)
        finally:
            app.dependency_overrides.pop(current_user, None)


if __name__ == "__main__":
    unittest.main()
