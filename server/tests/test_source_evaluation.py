import unittest
from app.schemas.verification import (
    ClaimItem,
    ClaimVerdictItem,
    ClaimVerdictLabel,
    ClaimsStagePayload,
    DeadlineInfo,
    EvidenceItem,
    EvidenceStagePayload,
    ExtractedStagePayload,
    VerdictStagePayload,
)
from app.services.tools.domain_rules import (
    classify_source,
    detect_deceptive_lookalike,
    evaluate_organizer_relationship,
    extract_hostname,
    get_domain_parts,
    is_academic_domain,
    is_government_domain,
)
from app.services.verification_workflow import (
    is_substantively_relevant,
    match_evidence_to_claims,
    run_card_stage,
)
from app.db import verification_repo


class TestHostnameAndURLParsing(unittest.TestCase):
    """Verifies safe URL extraction, normalization, and lookalike boundary enforcement."""

    def test_hostname_normalization_ports_userinfo_subdomains(self):
        self.assertEqual(extract_hostname("https://sub.events.stanford.edu/page"), "sub.events.stanford.edu")
        self.assertEqual(extract_hostname("https://portal.univ.ac.in:8080/apply"), "portal.univ.ac.in")
        self.assertEqual(extract_hostname("https://user:secret@example.com/path"), "example.com")
        self.assertEqual(extract_hostname("iitb.ac.in/events"), "iitb.ac.in")
        self.assertEqual(extract_hostname("  https://pib.gov.in./  "), "pib.gov.in")
        self.assertEqual(extract_hostname("https://www.google.com/"), "google.com")

    def test_malformed_and_missing_urls_handled_safely(self):
        self.assertEqual(extract_hostname(""), "")
        self.assertEqual(extract_hostname(None), "")
        self.assertEqual(extract_hostname("   "), "")
        self.assertEqual(extract_hostname("javascript:void(0)"), "")

        res_empty = classify_source("")
        self.assertEqual(res_empty["source_type"], "unverified_suspicious")
        self.assertEqual(res_empty["domain_trust"], "risky")

    def test_non_https_flagged_as_suspicious(self):
        res = classify_source("http://university.ac.in/hackathon", "University")
        self.assertEqual(res["source_type"], "unverified_suspicious")
        self.assertEqual(res["domain_trust"], "risky")
        self.assertIn("not HTTPS", res["notes"])


class TestGovernmentDomainsAndDeceptiveLookalikes(unittest.TestCase):
    """Verifies legitimate government domains and strict rejection of deceptive lookalikes."""

    def test_legitimate_government_domains(self):
        valid_gov_urls = [
            ("https://pib.gov.in/PressRelease.aspx", "pib.gov.in"),
            ("https://scholarships.gov.in/main.do", "scholarships.gov.in"),
            ("https://www.nsf.gov/funding/", "nsf.gov"),
            ("https://gov.uk/apply-grant", "gov.uk"),
            ("https://australia.gov.au/services", "australia.gov.au"),
            ("https://europa.eu/news", "europa.eu"),
            ("https://india.gov.in/my-government", "india.gov.in"),
        ]
        for url, expected_host in valid_gov_urls:
            host = extract_hostname(url)
            self.assertEqual(host, expected_host)
            self.assertTrue(is_government_domain(host), f"Expected {host} to be recognized as government")

    def test_deceptive_lookalikes_rejected(self):
        lookalike_urls = [
            "https://gov.in.attacker.com/apply",
            "https://pib.gov.in.phishing.net/press",
            "https://mit.edu.scam.org/admissions",
            "https://iitb.ac.in.fake.top/register",
        ]
        for url in lookalike_urls:
            host = extract_hostname(url)
            self.assertFalse(is_government_domain(host), f"{host} should NOT be recognized as government")
            self.assertFalse(is_academic_domain(host), f"{host} should NOT be recognized as academic")
            is_lookalike, reason = detect_deceptive_lookalike(host)
            self.assertTrue(is_lookalike, f"Expected {host} to be detected as deceptive lookalike")

            res = classify_source(url)
            self.assertEqual(res["source_type"], "unverified_suspicious")
            self.assertEqual(res["domain_trust"], "risky")

    def test_hyphenated_fake_gov_domains_rejected(self):
        fake_gov_urls = [
            "https://fake-gov.in/scholarship",
            "https://scholarships-gov.in/portal",
            "https://gov-portal.org/grants",
        ]
        for url in fake_gov_urls:
            host = extract_hostname(url)
            self.assertFalse(is_government_domain(host), f"{host} should NOT match government boundary")


class TestAcademicAndUnrelatedInstitutionDomains(unittest.TestCase):
    """Verifies academic domain classification and ensures unrelated universities are rejected as evidence."""

    def test_official_academic_organizer_match(self):
        res1 = classify_source("https://cs.stanford.edu/admissions", organizer="Stanford University")
        self.assertEqual(res1["source_type"], "official_organizer")
        self.assertEqual(res1["domain_trust"], "official_match")

        res2 = classify_source("https://iitb.ac.in/events/hackathon", organizer="IIT Bombay")
        self.assertEqual(res2["source_type"], "official_organizer")
        self.assertEqual(res2["domain_trust"], "official_match")

        res3 = classify_source("https://ox.ac.uk/scholarships", organizer="University of Oxford")
        self.assertEqual(res3["source_type"], "official_organizer")
        self.assertEqual(res3["domain_trust"], "official_match")

    def test_unrelated_institution_detected_and_not_official(self):
        # MIT domain for a Stanford University fellowship opportunity
        res_mit = classify_source("https://mit.edu/fellowship", organizer="Stanford University")
        self.assertEqual(res_mit["source_type"], "unrelated_institution")
        self.assertEqual(res_mit["domain_trust"], "third_party")

        # IIT Delhi domain for an IIT Bombay event
        res_iitd = classify_source("https://iitd.ac.in/hackathon", organizer="IIT Bombay")
        self.assertEqual(res_iitd["source_type"], "unrelated_institution")
        self.assertEqual(res_iitd["domain_trust"], "third_party")

    def test_unrelated_institution_rejected_when_not_discussing_target(self):
        extracted = ExtractedStagePayload(
            title="Stanford Quantum Fellowship 2026",
            organizer="Stanford University",
        )
        # MIT's own robotics page should be rejected as irrelevant to Stanford Quantum Fellowship
        is_rel, reason = is_substantively_relevant(
            ev_title="MIT Robotics 2026",
            ev_snippet="MIT Department of EECS invites applicants to MIT Robotics Lab.",
            ev_url="https://mit.edu/robotics-lab",
            source_type="unrelated_institution",
            extracted=extracted,
        )
        self.assertFalse(is_rel)
        self.assertIn("Unrelated institution", reason)

        # But if an MIT page explicitly mentions the Stanford fellowship and Stanford, it is retained as third-party evidence
        is_rel_citing, _ = is_substantively_relevant(
            ev_title="Partner Opportunities: Stanford Quantum Fellowship 2026",
            ev_snippet="Stanford University announces the Stanford Quantum Fellowship 2026 for visiting scholars.",
            ev_url="https://mit.edu/bulletin/stanford-fellowship",
            source_type="unrelated_institution",
            extracted=extracted,
        )
        self.assertTrue(is_rel_citing)


class TestCorporateAndNonprofitOfficialSources(unittest.TestCase):
    """Verifies corporate, nonprofit, and event-specific domain relationship mapping."""

    def test_company_and_foundation_official_domains(self):
        res_google = classify_source("https://careers.google.com/jobs/results/", organizer="Google")
        self.assertEqual(res_google["source_type"], "official_organizer")
        self.assertEqual(res_google["domain_trust"], "official_match")

        res_gsoc = classify_source("https://summerofcode.withgoogle.com/", organizer="Google", event_title="Google Summer of Code")
        self.assertEqual(res_gsoc["source_type"], "official_organizer")

        res_redcross = classify_source("https://redcross.org/volunteer", organizer="American Red Cross")
        self.assertEqual(res_redcross["source_type"], "official_organizer")

    def test_risky_corporate_lookalikes_flagged_as_suspicious(self):
        res_scam = classify_source("https://google-free-rewards.xyz/apply", organizer="Google")
        self.assertEqual(res_scam["source_type"], "unverified_suspicious")
        self.assertEqual(res_scam["domain_trust"], "risky")


class TestGenericDirectoriesAndSocialMedia(unittest.TestCase):
    """Verifies directory aggregator platforms, social media, and shorteners are properly tagged."""

    def test_generic_directories(self):
        directories = [
            "https://unstop.com/hackathons/xyz",
            "https://devpost.com/software/xyz",
            "https://buddy4study.com/scholarship/xyz",
            "https://internshala.com/internship/detail/xyz",
            "https://eventbrite.com/e/xyz",
        ]
        for url in directories:
            res = classify_source(url, organizer="Tech Corp")
            self.assertEqual(res["source_type"], "generic_directory")
            self.assertEqual(res["domain_trust"], "third_party")

    def test_social_media(self):
        socials = [
            "https://instagram.com/reel/123",
            "https://twitter.com/creator/status/123",
            "https://youtube.com/watch?v=123",
            "https://linkedin.com/posts/123",
        ]
        for url in socials:
            res = classify_source(url, organizer="Tech Corp")
            self.assertEqual(res["source_type"], "social_media")
            self.assertEqual(res["domain_trust"], "platform")

    def test_url_shorteners(self):
        shorteners = [
            "https://bit.ly/3xyz",
            "https://tinyurl.com/fast-reg",
            "https://cutt.ly/apply",
        ]
        for url in shorteners:
            res = classify_source(url, organizer="Tech Corp")
            self.assertEqual(res["source_type"], "unverified_suspicious")
            self.assertEqual(res["domain_trust"], "risky")


class TestMultiCategoryOpportunityVerification(unittest.TestCase):
    """Verifies end-to-end classification and Stage 5 badge correctness across multiple opportunity categories."""

    def setUp(self):
        self.user_id = "test-multi-cat-user"

    def test_category_scholarship_official_government_authority(self):
        """A National Merit Scholarship administered by the Ministry of Education on scholarships.gov.in."""
        extracted = ExtractedStagePayload(
            title="National Merit Scholarship 2026",
            organizer="Ministry of Education",
            category="scholarship",
            deadline=DeadlineInfo(raw="31st October 2026", date="2026-10-31"),
        )
        claims = ClaimsStagePayload(
            claims=[
                ClaimItem(claim_id="c1", claim_text="National Merit Scholarship 2026", claim_type="event"),
                ClaimItem(claim_id="c2", claim_text="Administered by Ministry of Education", claim_type="organizer"),
            ]
        )
        cls_info = classify_source("https://scholarships.gov.in/merit-2026", extracted.organizer, extracted.title, category=extracted.category)
        self.assertEqual(cls_info["source_type"], "trusted_institution")
        self.assertEqual(cls_info["domain_trust"], "high")

        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=["c1", "c2"],
                    url="https://scholarships.gov.in/merit-2026",
                    title="National Merit Scholarship 2026 Portal",
                    snippet="Official portal for National Merit Scholarship 2026 under Ministry of Education.",
                    domain="scholarships.gov.in",
                    domain_trust=cls_info["domain_trust"],
                    source_type=cls_info["source_type"],
                )
            ],
            search_status="completed",
        )
        verdict = VerdictStagePayload(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="National Merit Scholarship 2026", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Verified via official portal.", cited_sources=["https://scholarships.gov.in/merit-2026"]),
                ClaimVerdictItem(claim_id="c2", claim_text="Administered by Ministry of Education", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Ministry authority verified.", cited_sources=["https://scholarships.gov.in/merit-2026"]),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Officially verified on government scholarship portal.",
        )

        dummy_run = verification_repo.create_run(self.user_id, "raw", "rvpack")
        stages = [
            {"stage_name": "extracted", "status": "completed", "payload": extracted.model_dump(mode="json")},
            {"stage_name": "claims", "status": "completed", "payload": claims.model_dump(mode="json")},
            {"stage_name": "evidence", "status": "completed", "payload": evidence.model_dump(mode="json")},
            {"stage_name": "verdict", "status": "completed", "payload": verdict.model_dump(mode="json")},
        ]
        card = run_card_stage(dummy_run["id"], stages, self.user_id)
        self.assertEqual(card.badge, "OFFICIAL CORROBORATED")

    def test_category_job_third_party_directory_only_gives_partially_supported(self):
        """A software engineering job listing found only on a generic directory gives PARTIALLY SUPPORTED."""
        extracted = ExtractedStagePayload(
            title="Junior Cloud Engineer Vacancy 2026",
            organizer="Apex Technologies",
            category="job",
        )
        claims = ClaimsStagePayload(
            claims=[
                ClaimItem(claim_id="c1", claim_text="Junior Cloud Engineer Vacancy 2026", claim_type="event"),
                ClaimItem(claim_id="c2", claim_text="Hiring at Apex Technologies", claim_type="organizer"),
            ]
        )
        # Sourced only from an internship directory
        cls_info = classify_source("https://internshala.com/job/detail/apex-2026", extracted.organizer, extracted.title, category=extracted.category)
        self.assertEqual(cls_info["source_type"], "generic_directory")

        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=["c1", "c2"],
                    url="https://internshala.com/job/detail/apex-2026",
                    title="Junior Cloud Engineer at Apex Technologies",
                    snippet="Apex Technologies invites applications for Junior Cloud Engineer.",
                    domain="internshala.com",
                    domain_trust="third_party",
                    source_type="generic_directory",
                )
            ],
            search_status="completed",
        )
        verdict = VerdictStagePayload(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="Junior Cloud Engineer Vacancy 2026", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Listed on job directory.", cited_sources=["https://internshala.com/job/detail/apex-2026"]),
                ClaimVerdictItem(claim_id="c2", claim_text="Hiring at Apex Technologies", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Company listing found.", cited_sources=["https://internshala.com/job/detail/apex-2026"]),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Job listed on third-party aggregator platform.",
        )

        dummy_run = verification_repo.create_run(self.user_id, "raw", "rvpack")
        stages = [
            {"stage_name": "extracted", "status": "completed", "payload": extracted.model_dump(mode="json")},
            {"stage_name": "claims", "status": "completed", "payload": claims.model_dump(mode="json")},
            {"stage_name": "evidence", "status": "completed", "payload": evidence.model_dump(mode="json")},
            {"stage_name": "verdict", "status": "completed", "payload": verdict.model_dump(mode="json")},
        ]
        card = run_card_stage(dummy_run["id"], stages, self.user_id)
        # MUST NOT be officially corroborated; third-party directory yields PARTIALLY SUPPORTED
        self.assertNotEqual(card.badge, "OFFICIAL CORROBORATED")
        self.assertEqual(card.badge, "PARTIALLY SUPPORTED")

    def test_category_grant_official_nsf_grant(self):
        """A research grant published on nsf.gov by National Science Foundation."""
        extracted = ExtractedStagePayload(
            title="Quantum Exploration Research Grant 2026",
            organizer="National Science Foundation",
            category="grant",
        )
        cls_info = classify_source("https://www.nsf.gov/funding/quantum-exploration-2026", extracted.organizer, extracted.title, category=extracted.category)
        self.assertEqual(cls_info["source_type"], "official_organizer")
        self.assertEqual(cls_info["domain_trust"], "official_match")

    def test_authoritative_source_not_citing_core_claims_cannot_grant_official_corroboration(self):
        """If an official domain exists in evidence but is NOT cited for supported core claims, badge cannot be OFFICIAL CORROBORATED."""
        extracted = ExtractedStagePayload(
            title="Global AI Challenge 2026",
            organizer="Tech Giant",
            category="competition",
        )
        claims = ClaimsStagePayload(
            claims=[ClaimItem(claim_id="c1", claim_text="Global AI Challenge 2026", claim_type="event")]
        )
        # Sourced from official site (e.g. general homepage) and a directory
        evidence = EvidenceStagePayload(
            evidence_items=[
                EvidenceItem(
                    id="ev_1",
                    claim_ids=[],
                    url="https://techgiant.com/about",
                    title="About Tech Giant",
                    snippet="General corporate overview with no mention of AI Challenge.",
                    domain="techgiant.com",
                    domain_trust="official_match",
                    source_type="official_organizer",
                ),
                EvidenceItem(
                    id="ev_2",
                    claim_ids=["c1"],
                    url="https://unstop.com/competitions/global-ai-challenge-2026",
                    title="Global AI Challenge 2026",
                    snippet="Unstop competition listing for Global AI Challenge.",
                    domain="unstop.com",
                    domain_trust="third_party",
                    source_type="generic_directory",
                )
            ],
            search_status="completed",
        )
        # The verdict supported c1 citing ONLY the unstop directory, NOT the official source
        verdict = VerdictStagePayload(
            claim_verdicts=[
                ClaimVerdictItem(claim_id="c1", claim_text="Global AI Challenge 2026", verdict=ClaimVerdictLabel.SUPPORTED, explanation="Corroborated by directory.", cited_sources=["https://unstop.com/competitions/global-ai-challenge-2026"]),
            ],
            overall_verdict=ClaimVerdictLabel.SUPPORTED,
            summary="Corroborated by directory only.",
        )

        dummy_run = verification_repo.create_run(self.user_id, "raw", "rvpack")
        stages = [
            {"stage_name": "extracted", "status": "completed", "payload": extracted.model_dump(mode="json")},
            {"stage_name": "claims", "status": "completed", "payload": claims.model_dump(mode="json")},
            {"stage_name": "evidence", "status": "completed", "payload": evidence.model_dump(mode="json")},
            {"stage_name": "verdict", "status": "completed", "payload": verdict.model_dump(mode="json")},
        ]
        card = run_card_stage(dummy_run["id"], stages, self.user_id)
        # Because the official source did not corroborate the claim, badge must remain PARTIALLY SUPPORTED
        self.assertNotEqual(card.badge, "OFFICIAL CORROBORATED")
        self.assertEqual(card.badge, "PARTIALLY SUPPORTED")


if __name__ == "__main__":
    unittest.main()
