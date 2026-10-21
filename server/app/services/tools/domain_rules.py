from urllib.parse import urlparse

HIGH_TRUST = (".gov.in", ".nic.in", ".ac.in", ".edu.in", ".edu", ".gov")
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "lnkd.in", "goo.gl", "linktr.ee"}
PLATFORMS = {
    "unstop.com",
    "devfolio.co",
    "internshala.com",
    "linkedin.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
    "facebook.com",
}
RISKY_TLDS = (".xyz", ".top", ".click", ".shop", ".site", ".online", ".icu", ".buzz")
BAIT_WORDS = ("free", "reward", "claim", "winner", "official-apply", "lucky")
STOP = {"the", "of", "and", "india", "indian", "ltd", "pvt", "private", "limited", "for", "inc"}


def check_domain(url: str, organizer: str = "") -> dict:
    p = urlparse(url)
    host = (p.hostname or "").lower().removeprefix("www.")
    tokens = [
        t
        for t in "".join(c if c.isalnum() else " " for c in organizer.lower()).split()
        if len(t) >= 3 and t not in STOP
    ]
    flat = host.replace("-", "").replace(".", "")
    name_match = bool(tokens) and sum(t in flat for t in tokens) >= min(2, len(tokens))
    shortener = host in SHORTENERS
    platform = any(host == d or host.endswith("." + d) for d in PLATFORMS)
    risky = host.endswith(RISKY_TLDS) or any(w in host for w in BAIT_WORDS)
    high = host.endswith(HIGH_TRUST)
    notes = []
    if shortener:
        notes.append("URL shortener")
    if platform:
        notes.append("third-party platform page (not the organizer's own site)")
    if risky:
        notes.append("risky TLD or bait words in domain")
    if p.scheme != "https":
        notes.append("not HTTPS")
    plausibly_official = (
        not shortener and not platform and not risky and p.scheme == "https" and (high or name_match)
    )
    return {
        "domain": host,
        "high_trust_suffix": high,
        "name_match": name_match,
        "is_shortener": shortener,
        "is_platform": platform,
        "risky": risky,
        "plausibly_official": plausibly_official,
        "notes": notes,
    }
