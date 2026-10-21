import re
from urllib.parse import urlsplit

# Legitimate government TLDs and second-level domain suffixes
GOVERNMENT_SUFFIXES = (
    ".gov.in", ".nic.in", ".gov", ".mil", ".gov.uk", ".gov.au",
    ".gc.ca", ".canada.ca", ".europa.eu", ".gov.sg", ".gov.za",
    ".gov.br", ".gov.ng",
)

# Known central/state statutory bodies and government portals
GOVERNMENT_EXACT_HOSTS = {
    "india.gov.in",
    "mygov.in",
    "digitalindia.gov.in",
    "ugc.gov.in",
    "aicte-india.org",
    "scholarships.gov.in",
    "swayam.gov.in",
    "nptel.ac.in",
    "nta.ac.in",
}

# Accredited academic and educational domain suffixes
ACADEMIC_SUFFIXES = (
    ".edu", ".ac.in", ".edu.in", ".ac.uk", ".edu.au",
    ".edu.sg", ".ac.za", ".ac.nz",
)

# Multi-part public suffixes for accurate registered domain parsing
MULTI_PART_SUFFIXES = (
    ".gov.in", ".nic.in", ".gov.uk", ".gov.au", ".gov.sg", ".gov.za", ".gov.br",
    ".gc.ca", ".canada.ca",
    ".ac.in", ".edu.in", ".ac.uk", ".edu.au", ".ac.za", ".edu.sg", ".ac.nz",
    ".co.in", ".co.uk", ".com.au", ".co.nz", ".co.za", ".com.br", ".com.sg",
    ".org.in", ".net.in", ".org.uk",
)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "lnkd.in",
    "goo.gl", "linktr.ee", "is.gd", "buff.ly", "ow.ly", "rebrand.ly",
}

SOCIAL_DOMAINS = {
    "instagram.com", "instagr.am", "youtube.com", "youtu.be",
    "tiktok.com", "facebook.com", "fb.com", "twitter.com",
    "x.com", "reddit.com", "linkedin.com", "threads.net",
    "t.me", "telegram.me", "whatsapp.com", "discord.com", "discord.gg",
}

GENERIC_DIRECTORIES = {
    "unstop.com", "devfolio.co", "devpost.com", "eventbrite.com", "eventbrite.in",
    "meetup.com", "hackerearth.com", "knowafest.com", "allevents.in",
    "dare2compete.com", "internshala.com", "opportunitydesk.org", "youthop.com",
    "buddy4study.com", "scholarships360.org", "fastweb.com", "scholarships.com",
    "chegg.com", "wayup.com", "angel.co", "wellfound.com", "indeed.com",
    "naukri.com", "glassdoor.com", "monster.com", "coursera.org", "edx.org",
    "udemy.com", "quora.com", "medium.com", "ycombinator.com", "geeksforgeeks.org",
}

REPUTABLE_MEDIA = {
    "bbc.com", "bbc.co.uk", "reuters.com", "thehindu.com", "timesofindia.com",
    "indianexpress.com", "hindustantimes.com", "techcrunch.com", "wired.com",
    "forbes.com", "bloomberg.com", "nature.com", "sciencemag.org", "ieee.org", "acm.org",
}

RISKY_TLDS = (
    ".xyz", ".top", ".click", ".shop", ".site", ".online", ".icu",
    ".buzz", ".club", ".work", ".biz", ".download", ".racing", ".cam",
    ".loan", ".live",
)

BAIT_PATTERNS = (
    "official-apply", "claim-reward", "win-cash", "free-giveaway",
    "lucky-draw", "instant-prize", "instant-cash", "quick-loan",
    "official-grant", "free-entry", "free-hackathon", "win-iphone",
)

STOP = {
    "the", "of", "and", "india", "indian", "ltd", "pvt", "private",
    "limited", "for", "inc", "corp", "corporation", "foundation",
    "institute", "university", "department", "ministry", "association",
    "organization", "national", "international", "annual",
}

GENERIC_OPPORTUNITY_TERMS = {
    "hackathon", "challenge", "competition", "opportunity", "announcement",
    "national", "international", "annual", "india", "student", "students",
    "bootcamp", "event", "tech", "online", "apply", "register", "registration",
    "scholarship", "fellowship", "internship", "job", "jobs", "grant", "grants",
    "course", "courses", "webinar", "workshop", "conference", "program",
    "programme", "summit", "admission", "admissions", "exam", "examination",
    "test", "testseries", "portal", "official", "career", "careers", "hiring",
    "2022", "2023", "2024", "2025", "2026", "2027", "free", "cash", "prize",
    "stipend", "salary", "award", "awards",
}


def extract_hostname(url: str) -> str:
    """Safely extract and normalize the hostname from a URL.
    
    Handles missing schemes, port numbers, userinfo, trailing dots, and malformed inputs.
    Rejects non-web schemes (e.g. javascript:, mailto:, data:) and inputs without a valid domain structure.
    """
    if not url or not isinstance(url, str):
        return ""
    cleaned = url.strip()
    if not cleaned:
        return ""
    
    # Reject non-web or dangerous schemes immediately
    cleaned_lower = cleaned.lower()
    if cleaned_lower.startswith(("javascript:", "mailto:", "data:", "file:", "tel:", "ftp:", "about:", "blob:")):
        return ""

    # If missing scheme, prepend https://
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned):
        cleaned = "https://" + cleaned
    
    try:
        parsed = urlsplit(cleaned)
        if parsed.scheme.lower() not in ("http", "https"):
            return ""
        netloc = parsed.netloc or ""
        # Strip userinfo if present (e.g. user:pass@host)
        if "@" in netloc:
            netloc = netloc.rsplit("@", 1)[-1]
        # Strip port if present (e.g. host:8080)
        if ":" in netloc:
            netloc = netloc.split(":", 1)[0]
        # Remove trailing dot, strip www., and lowercase
        host = netloc.rstrip(".").lower()
        if host.startswith("www."):
            host = host[4:]
        # A valid internet hostname must contain at least one dot (e.g. example.com)
        if "." not in host:
            return ""
        # Hostnames cannot contain spaces, slashes, or invalid characters
        if re.search(r"[\s/\\?#%]", host):
            return ""
        return host
    except Exception:
        return ""


def get_domain_parts(host: str) -> tuple[str, str, str]:
    """Split a hostname into (registered_domain, main_label, public_suffix).
    
    Examples:
        'sub.iitb.ac.in' -> ('iitb.ac.in', 'iitb', '.ac.in')
        'careers.google.com' -> ('google.com', 'google', '.com')
        'gov.in.attacker.com' -> ('attacker.com', 'attacker', '.com')
    """
    if not host:
        return "", "", ""
    
    # Check multi-part suffixes first (e.g. .ac.in, .gov.in)
    for suffix in MULTI_PART_SUFFIXES:
        if host.endswith(suffix):
            prefix = host[: -len(suffix)]
            labels = prefix.split(".")
            main_label = labels[-1] if labels else ""
            reg_domain = f"{main_label}{suffix}" if main_label else suffix.lstrip(".")
            return reg_domain, main_label, suffix
            
    # Single-part TLD (e.g. .com, .edu, .gov, .org)
    parts = host.split(".")
    if len(parts) >= 2:
        suffix = "." + parts[-1]
        main_label = parts[-2]
        reg_domain = f"{main_label}{suffix}"
        return reg_domain, main_label, suffix
    
    return host, host, ""


def is_government_domain(host: str) -> bool:
    """Recognize legitimate government domains using strict domain boundaries.
    
    Guarantees lookalikes like 'gov.in.attacker.com' or 'fake-gov.in' return False.
    """
    if not host:
        return False
    host = host.lower()
    if host in GOVERNMENT_EXACT_HOSTS:
        return True
    for s in GOVERNMENT_SUFFIXES:
        if host == s.lstrip(".") or host.endswith(s):
            return True
    return False


def is_academic_domain(host: str) -> bool:
    """Recognize accredited academic / university domains with strict boundary checks."""
    if not host:
        return False
    host = host.lower()
    for s in ACADEMIC_SUFFIXES:
        if host == s.lstrip(".") or host.endswith(s):
            return True
    return False


def detect_deceptive_lookalike(host: str) -> tuple[bool, str]:
    """Detect deceptive domains embedding legitimate institutional/gov tokens as subdomains.
    
    Example: 'gov.in.attacker.com' has registered domain 'attacker.com' but embeds 'gov.in'
    in its subdomain to mislead users.
    """
    if not host or "." not in host:
        return False, ""
    reg_domain, _, _ = get_domain_parts(host)
    subdomain = host[: -len(reg_domain) - 1] if len(host) > len(reg_domain) else ""
    if subdomain:
        for high_kw in (".gov.in", ".nic.in", ".ac.in", ".edu.in", ".edu", ".gov", ".ac.uk", ".gov.uk"):
            trimmed_kw = high_kw.lstrip(".")
            if trimmed_kw in subdomain or any(s in {"gov", "nic", "edu", "ac"} for s in subdomain.split(".")):
                if not is_government_domain(reg_domain) and not is_academic_domain(reg_domain):
                    return True, f"Deceptive lookalike domain embedding '{trimmed_kw}' under unverified '{reg_domain}'"
    return False, ""


def evaluate_organizer_relationship(
    host: str,
    organizer: str = "",
    event_title: str = "",
    category: str = "",
) -> tuple[bool, str, str]:
    """Evaluate whether host has an established official relationship to the organizer/event.
    
    Returns:
        (is_official: bool, source_type: str, reason: str)
    """
    is_lookalike, lookalike_reason = detect_deceptive_lookalike(host)
    if is_lookalike:
        return False, "unverified_suspicious", lookalike_reason

    # URL Shorteners
    if host in SHORTENERS:
        return False, "unverified_suspicious", "URL shortener obscures destination authority"

    # Social Media
    if any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS):
        return False, "social_media", "Social media platform; not organizer official site"

    # Generic Directories
    if any(host == d or host.endswith("." + d) for d in GENERIC_DIRECTORIES):
        return False, "generic_directory", "Third-party aggregator / event directory platform"

    # Reputable Independent Media
    if any(host == d or host.endswith("." + d) for d in REPUTABLE_MEDIA):
        return False, "reputable_media", "Reputable independent news/media publication"

    # Risky TLDs and Bait Words
    has_risky_tld = host.endswith(RISKY_TLDS)
    has_bait = any(w in host for w in BAIT_PATTERNS)
    if has_risky_tld or has_bait:
        return False, "unverified_suspicious", "Risky TLD or bait patterns detected in hostname"

    reg_domain, main_label, _ = get_domain_parts(host)
    subdomain = host[: -len(reg_domain) - 1] if len(host) > len(reg_domain) else ""
    is_gov = is_government_domain(host)
    is_acad = is_academic_domain(host)

    org_clean = (organizer or "").strip().lower()
    is_unverified_org = not org_clean or org_clean in {
        "unverified organizer", "unknown", "admin", "admin user", "reel", "official",
    }

    LITTLE_WORDS = {"the", "of", "and", "for", "in", "to", "a", "an", "at", "by", "from", "on"}
    raw_org_tokens = [w for w in re.findall(r"[a-z0-9]+", org_clean) if len(w) >= 1]
    meaningful_org_words = [w for w in raw_org_tokens if w not in LITTLE_WORDS]

    # Full acronym across all meaningful words (e.g. National Science Foundation -> nsf, World Health Organization -> who)
    org_acronym = "".join(w[0] for w in meaningful_org_words) if len(meaningful_org_words) >= 2 else ""

    # Blended acronym for compound names where first word is an abbreviation (e.g. IIT Bombay -> iit + b -> iitb)
    blended_acronym = ""
    if len(meaningful_org_words) >= 2 and len(meaningful_org_words[0]) in (2, 3, 4):
        blended_acronym = meaningful_org_words[0] + "".join(w[0] for w in meaningful_org_words[1:])

    # Meaningful organizer tokens excluding generic type words
    org_tokens = [w for w in meaningful_org_words if w not in STOP]
    compact_org = "".join(org_tokens) if org_tokens else ""

    # Distinct event tokens
    title_clean = (event_title or "").strip().lower()
    raw_title_tokens = [w for w in re.findall(r"[a-z0-9]+", title_clean) if len(w) >= 2 and w not in LITTLE_WORDS]
    event_tokens = [w for w in raw_title_tokens if w not in STOP and w not in GENERIC_OPPORTUNITY_TERMS]
    event_acronym = "".join(w[0] for w in event_tokens) if len(event_tokens) >= 3 else ""

    # Check 1: Organizer Acronym or Blended Acronym Match (e.g. nsf on nsf.gov, iitb on iitb.ac.in, who on who.int)
    for acr in (org_acronym, blended_acronym):
        if acr and len(acr) >= 3 and main_label == acr:
            if is_acad:
                return True, "official_organizer", f"Official university domain matching organizer acronym '{acr}'"
            if is_gov:
                return True, "official_organizer", f"Official government domain matching agency acronym '{acr}'"
            if reg_domain.endswith((".org", ".int", ".com", ".net", ".io", ".ai")):
                return True, "official_organizer", f"Official organization domain matching organizer acronym '{acr}'"

    # Check 2: Academic Domain Prefix / Institution Match
    if is_acad and not is_unverified_org:
        # Exact token match (e.g. stanford on stanford.edu, mit on mit.edu, harvard on harvard.edu)
        if any(tok == main_label for tok in org_tokens if len(tok) >= 3):
            return True, "official_organizer", f"Official educational domain for '{main_label}'"
        # Truncation/abbreviation match (e.g. iitbombay starts with iitb)
        if compact_org and len(main_label) >= 3 and compact_org.startswith(main_label):
            return True, "official_organizer", f"Official educational domain abbreviation '{main_label}' for '{compact_org}'"
        # Known university prefix conventions (e.g. oxford -> ox.ac.uk, cambridge -> cam.ac.uk)
        for tok in org_tokens:
            if len(main_label) >= 2 and len(tok) >= 5 and tok.startswith(main_label):
                return True, "official_organizer", f"Official educational domain prefix '{main_label}' for '{tok}'"

    # Check 3: Exact Organizer Token Match for General / Corporate / Government Bodies
    if not is_unverified_org and org_tokens:
        for tok in org_tokens:
            if len(tok) >= 4 and main_label == tok:
                if any(w in org_clean for w in ("ministry", "department", "government", "commission", "bureau")):
                    if is_gov:
                        return True, "official_organizer", f"Official government domain for '{tok}'"
                else:
                    return True, "official_organizer", f"Official organizer domain for '{tok}'"

    # Check 4: Compound Organizer Name (e.g. redcross.org for American Red Cross, iitbombay.org)
    if not is_unverified_org and len(org_tokens) >= 2:
        if len(compact_org) >= 5 and (main_label == compact_org or reg_domain.startswith(compact_org + ".")):
            return True, "official_organizer", f"Official domain matching organizer name '{compact_org}'"
        # Match core compound name without geographic/nationality prefix (e.g. redcross for American Red Cross)
        core_tokens = [w for w in org_tokens if w not in {"american", "british", "canadian", "australian", "german", "french", "global", "international"}]
        compact_core = "".join(core_tokens)
        if len(compact_core) >= 5 and (main_label == compact_core or reg_domain.startswith(compact_core + ".")):
            return True, "official_organizer", f"Official domain matching core organization name '{compact_core}'"
        # Truncation or suffix match for significant compound names (e.g. redcross in americanredcross)
        if len(main_label) >= 6 and (compact_org.endswith(main_label) or compact_org.startswith(main_label)):
            return True, "official_organizer", f"Official domain matching organization component '{main_label}'"

    # Check 5: Corporate Outreach / Program Portals (e.g. summerofcode.withgoogle.com, join{org}.com)
    if not is_unverified_org and org_tokens:
        for tok in org_tokens:
            if len(tok) >= 4:
                # Secondary domain pattern like withgoogle, joingoogle, googlecareers
                is_company_portal_label = main_label in {
                    f"with{tok}", f"join{tok}", f"workat{tok}", f"lifeat{tok}", f"careers{tok}", f"{tok}careers",
                }
                # Or subdomain matches event while domain embeds organizer token
                title_words_no_org = [w for w in re.findall(r"[a-z0-9]+", title_clean) if w != tok]
                compact_event_sub = "".join(title_words_no_org)
                is_event_subdomain = bool(subdomain and compact_event_sub and subdomain == compact_event_sub)
                
                if (is_company_portal_label or (tok in main_label and not is_lookalike)) and (is_event_subdomain or is_company_portal_label):
                    return True, "official_organizer", f"Official corporate program portal for '{tok}'"

    # Check 6: Distinct Event Portal Domain (e.g. pycon.org for PyCon India)
    if event_tokens:
        for etok in event_tokens:
            if len(etok) >= 4 and main_label == etok:
                return True, "official_organizer", f"Official event portal domain matching '{etok}'"
    if event_acronym and len(event_acronym) >= 4 and main_label == event_acronym:
        return True, "official_organizer", f"Official event portal domain matching acronym '{event_acronym}'"

    # Check 7: Authoritative Government Governing Portal for public schemes/grants/scholarships
    cat_lower = (category or "").lower()
    if is_gov and (cat_lower in {"government_scheme", "scholarship", "grant"} or any(w in org_clean for w in ("ministry", "government", "department"))):
        return True, "trusted_institution", "Official government authority domain administering public opportunity"

    # Check 8: Reputable Academic Domain of an Unrelated Institution
    if is_acad:
        return False, "unrelated_institution", f"Reputable academic domain ({reg_domain}) belonging to an unrelated institution"

    # Check 9: Reputable Government Domain unrelated to target opportunity
    if is_gov:
        return False, "unrelated_institution", f"Government domain ({reg_domain}) not matching target organizer"

    return False, "third_party", "Independent third-party web source"


def classify_source(
    url: str,
    organizer: str = "",
    event_title: str = "",
    category: str = "",
) -> dict:
    """Classify evidence source domain, trustworthiness, and relationship to the opportunity.
    
    Returns structured evaluation with:
        domain: normalized hostname
        registered_domain: base registrable domain
        domain_trust: 'official_match' | 'high' | 'platform' | 'third_party' | 'risky'
        source_type: 'official_organizer' | 'trusted_institution' | 'reputable_media' |
                     'unrelated_institution' | 'generic_directory' | 'third_party' |
                     'social_media' | 'unverified_suspicious'
        source_label: human readable summary
        high_trust_suffix: bool
        is_government: bool
        is_academic: bool
        is_shortener: bool
        is_platform: bool
        is_directory: bool
        is_media: bool
        risky: bool
        plausibly_official: bool
        notes: list of diagnostic notes
    """
    host = extract_hostname(url)
    if not host:
        return {
            "domain": "",
            "registered_domain": "",
            "domain_trust": "risky",
            "source_type": "unverified_suspicious",
            "source_label": "Missing or malformed URL",
            "high_trust_suffix": False,
            "is_government": False,
            "is_academic": False,
            "is_shortener": False,
            "is_platform": False,
            "is_directory": False,
            "is_media": False,
            "risky": True,
            "plausibly_official": False,
            "notes": ["missing or unparseable URL"],
        }

    is_https = isinstance(url, str) and url.strip().lower().startswith("https://")
    reg_domain, main_label, suffix = get_domain_parts(host)
    is_gov = is_government_domain(host)
    is_acad = is_academic_domain(host)
    is_short = host in SHORTENERS
    is_social = any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS)
    is_dir = any(host == d or host.endswith("." + d) for d in GENERIC_DIRECTORIES)
    is_med = any(host == d or host.endswith("." + d) for d in REPUTABLE_MEDIA)
    is_risky_tld = host.endswith(RISKY_TLDS)
    has_bait = any(w in host for w in BAIT_PATTERNS)
    is_lookalike, lookalike_msg = detect_deceptive_lookalike(host)

    is_risky = is_short or is_risky_tld or has_bait or is_lookalike or not is_https

    is_official, source_type, rel_reason = evaluate_organizer_relationship(
        host=host,
        organizer=organizer,
        event_title=event_title,
        category=category,
    )

    notes = []
    if is_lookalike:
        notes.append(lookalike_msg)
    if not is_https:
        notes.append("not HTTPS")
        source_type = "unverified_suspicious"
    if is_short:
        notes.append("URL shortener")
    if is_risky_tld or has_bait:
        notes.append("risky TLD or bait words in hostname")

    # Determine domain-level infrastructure trust
    if source_type == "official_organizer":
        domain_trust = "official_match"
        source_label = "Official organizer / primary event source"
    elif source_type == "trusted_institution":
        domain_trust = "high"
        source_label = "Official governing authority / institutional source"
    elif source_type == "unrelated_institution":
        domain_trust = "third_party"
        source_label = "Unrelated institutional source (not organizer)"
    elif source_type == "reputable_media":
        domain_trust = "third_party"
        source_label = "Reputable independent news/media publication"
    elif source_type == "generic_directory":
        domain_trust = "third_party"
        source_label = "Generic event directory / platform"
    elif source_type == "social_media":
        domain_trust = "platform"
        source_label = "Social media post"
    elif source_type == "unverified_suspicious":
        domain_trust = "risky"
        source_label = "Unverified or suspicious source"
    else:
        domain_trust = "third_party"
        source_label = "Third-party source"

    high_trust_suffix = is_gov or is_acad
    plausibly_official = is_official and is_https and not is_risky

    return {
        "domain": host,
        "registered_domain": reg_domain,
        "domain_trust": domain_trust,
        "source_type": source_type,
        "source_label": source_label,
        "high_trust_suffix": high_trust_suffix,
        "is_government": is_gov,
        "is_academic": is_acad,
        "is_shortener": is_short,
        "is_platform": is_social or is_dir,
        "is_directory": is_dir,
        "is_media": is_med,
        "risky": is_risky,
        "plausibly_official": plausibly_official,
        "notes": notes,
    }


def check_domain(url: str, organizer: str = "") -> dict:
    """Backward-compatible wrapper for toolkit.py and legacy callers."""
    return classify_source(url=url, organizer=organizer)
