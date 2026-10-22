/**
 * Helper to resolve official company / organization links
 * and avoid generic google.com reference links.
 */

export const KNOWN_COMPANIES = [
  {
    regex: /\b(microsoft|msft)\b/i,
    name: "Microsoft",
    domain: "microsoft.com",
    url: "https://www.microsoft.com",
  },
  {
    regex: /\b(adobe)\b/i,
    name: "Adobe",
    domain: "adobe.com",
    url: "https://www.adobe.com",
  },
  {
    regex: /\b(paytm|paytem)\b/i,
    name: "Paytm",
    domain: "paytm.com",
    url: "https://paytm.com",
  },
  {
    regex: /\b(amazon|aws)\b/i,
    name: "Amazon",
    domain: "amazon.com",
    url: "https://www.amazon.com",
  },
  {
    regex: /\b(nvidia)\b/i,
    name: "NVIDIA",
    domain: "nvidia.com",
    url: "https://www.nvidia.com",
  },
  {
    regex: /\b(apple)\b/i,
    name: "Apple",
    domain: "apple.com",
    url: "https://www.apple.com",
  },
  {
    regex: /\b(meta|facebook)\b/i,
    name: "Meta",
    domain: "about.meta.com",
    url: "https://about.meta.com",
  },
  {
    regex: /\b(netflix)\b/i,
    name: "Netflix",
    domain: "netflix.com",
    url: "https://jobs.netflix.com",
  },
  {
    regex: /\b(flipkart)\b/i,
    name: "Flipkart",
    domain: "flipkart.com",
    url: "https://www.flipkart.com",
  },
  {
    regex: /\b(swiggy)\b/i,
    name: "Swiggy",
    domain: "swiggy.com",
    url: "https://www.swiggy.com",
  },
  {
    regex: /\b(zomato)\b/i,
    name: "Zomato",
    domain: "zomato.com",
    url: "https://www.zomato.com",
  },
  {
    regex: /\b(tcs|tata\s+consultancy)\b/i,
    name: "TCS",
    domain: "tcs.com",
    url: "https://www.tcs.com",
  },
  {
    regex: /\b(infosys)\b/i,
    name: "Infosys",
    domain: "infosys.com",
    url: "https://www.infosys.com",
  },
  {
    regex: /\b(wipro)\b/i,
    name: "Wipro",
    domain: "wipro.com",
    url: "https://www.wipro.com",
  },
  {
    regex: /\b(cognizant)\b/i,
    name: "Cognizant",
    domain: "cognizant.com",
    url: "https://www.cognizant.com",
  },
  {
    regex: /\b(accenture)\b/i,
    name: "Accenture",
    domain: "accenture.com",
    url: "https://www.accenture.com",
  },
  {
    regex: /\b(deloitte)\b/i,
    name: "Deloitte",
    domain: "deloitte.com",
    url: "https://www.deloitte.com",
  },
  {
    regex: /\b(ibm)\b/i,
    name: "IBM",
    domain: "ibm.com",
    url: "https://www.ibm.com",
  },
  {
    regex: /\b(oracle)\b/i,
    name: "Oracle",
    domain: "oracle.com",
    url: "https://www.oracle.com",
  },
  {
    regex: /\b(salesforce)\b/i,
    name: "Salesforce",
    domain: "salesforce.com",
    url: "https://www.salesforce.com",
  },
  {
    regex: /\b(uber)\b/i,
    name: "Uber",
    domain: "uber.com",
    url: "https://www.uber.com",
  },
  {
    regex: /\b(spotify)\b/i,
    name: "Spotify",
    domain: "spotify.com",
    url: "https://www.spotify.com",
  },
  {
    regex: /\b(intel)\b/i,
    name: "Intel",
    domain: "intel.com",
    url: "https://www.intel.com",
  },
  {
    regex: /\b(cisco)\b/i,
    name: "Cisco",
    domain: "cisco.com",
    url: "https://www.cisco.com",
  },
  {
    regex: /\b(canva)\b/i,
    name: "Canva",
    domain: "canva.com",
    url: "https://www.canva.com",
  },
  {
    regex: /\b(figma)\b/i,
    name: "Figma",
    domain: "figma.com",
    url: "https://www.figma.com",
  },
  {
    regex: /\b(notion)\b/i,
    name: "Notion",
    domain: "notion.so",
    url: "https://www.notion.so",
  },
  {
    regex: /\b(github)\b/i,
    name: "GitHub",
    domain: "github.com",
    url: "https://github.com",
  },
  {
    regex: /\b(openai)\b/i,
    name: "OpenAI",
    domain: "openai.com",
    url: "https://openai.com",
  },
  {
    regex: /\b(odoo)\b/i,
    name: "Odoo",
    domain: "odoo.com",
    url: "https://www.odoo.com",
  },
  {
    regex: /\b(quizlet)\b/i,
    name: "Quizlet",
    domain: "quizlet.com",
    url: "https://quizlet.com",
  },
  {
    regex: /\b(gsoc|summer\s*of\s*code)\b/i,
    name: "Google Summer of Code",
    domain: "summerofcode.withgoogle.com",
    url: "https://summerofcode.withgoogle.com",
  },
  {
    regex: /\b(isro)\b/i,
    name: "ISRO",
    domain: "isro.gov.in",
    url: "https://www.isro.gov.in",
  },
  {
    regex: /\b(drdo)\b/i,
    name: "DRDO",
    domain: "drdo.gov.in",
    url: "https://www.drdo.gov.in",
  },
];

export function isGenericGoogleUrl(url) {
  if (!url) return false;
  try {
    const raw = String(url).trim().toLowerCase();
    if (raw === "google.com" || raw === "www.google.com" || raw === "https://google.com" || raw === "https://www.google.com") {
      return true;
    }
    const parsed = new URL(raw.startsWith("http") ? raw : `https://${raw}`);
    const host = parsed.hostname.toLowerCase();
    if (host === "summerofcode.withgoogle.com" || host === "buildyourfuture.withgoogle.com") {
      return false;
    }
    return host === "google.com" || host === "www.google.com";
  } catch {
    return /^(https?:\/\/)?(www\.)?google\.com(\/)?$/i.test(String(url).trim());
  }
}

/**
 * Checks whether a URL is a generic root homepage (e.g. https://www.nvidia.com or https://microsoft.com/)
 * with no event, opportunity, or registration path.
 */
export function isGenericRootUrl(url) {
  if (!url) return false;
  try {
    const raw = String(url).trim();
    const parsed = new URL(raw.startsWith("http") ? raw : `https://${raw}`);
    const p = parsed.pathname.replace(/\/+$/, "").toLowerCase();
    const isRoot = p === "" || /^\/(?:en|en-[a-z]{2}|in|us|global)?$/i.test(p);
    return isRoot && !parsed.search && !parsed.hash;
  } catch {
    return false;
  }
}

const DEDICATED_OPPORTUNITY_DOMAINS = new Set([
  "summerofcode.withgoogle.com",
  "buildyourfuture.withgoogle.com",
  "aifoundersgrant.org",
  "stemleadersfund.org",
  "devpost.com",
  "unstop.com",
  "mlh.io",
  "hackerearth.com",
  "kaggle.com",
]);

const SOCIAL_OR_AGGREGATOR_DOMAINS = new Set([
  "instagram.com",
  "facebook.com",
  "tiktok.com",
  "youtube.com",
  "youtu.be",
  "twitter.com",
  "x.com",
  "linkedin.com",
  "reddit.com",
  "bit.ly",
  "tinyurl.com",
  "t.co",
]);

/**
 * Verifies whether a candidate URL actually relates to the specific opportunity
 * rather than being a generic corporate root homepage, social post, or search engine.
 */
export function verifyRegistrationLink(url, opportunityTitle = "", organizer = "") {
  if (!url) {
    return { isValid: false, status: "not_found", reason: "No link provided." };
  }

  if (isGenericGoogleUrl(url)) {
    return { isValid: false, status: "unable_to_verify", reason: "Generic search engine URL." };
  }

  let parsed;
  try {
    const raw = String(url).trim();
    parsed = new URL(raw.startsWith("http") ? raw : `https://${raw}`);
  } catch {
    return { isValid: false, status: "unable_to_verify", reason: "Invalid URL format." };
  }

  const hostname = parsed.hostname.replace(/^www\./, "").toLowerCase();

  // 1. Reject social media, aggregators, link shorteners
  for (const blocked of SOCIAL_OR_AGGREGATOR_DOMAINS) {
    if (hostname === blocked || hostname.endsWith(`.${blocked}`)) {
      return { isValid: false, status: "unable_to_verify", reason: "Social media or shortener URL." };
    }
  }

  // 2. Check if dedicated opportunity domain
  for (const dedicated of DEDICATED_OPPORTUNITY_DOMAINS) {
    if (hostname === dedicated || hostname.endsWith(`.${dedicated}`)) {
      return { isValid: true, status: "verified", reason: "Dedicated opportunity domain." };
    }
  }

  const path = parsed.pathname.toLowerCase();
  const search = parsed.search.toLowerCase();
  const fullPath = `${path}${search}`;

  // 3. Reject generic root homepage of large companies/organizations
  if (isGenericRootUrl(url)) {
    return {
      isValid: false,
      status: "unable_to_verify",
      reason: `Generic corporate homepage (${hostname}) is not an official registration link.`,
    };
  }

  // 4. Check for registration/opportunity path intent
  const hasRegIntent = /(?:register|registration|apply|application|signup|sign-up|portal|form|participate|contest|challenge|hackathon|internship|fellowship|scholarship|grants|careers|jobs)/i.test(fullPath);

  // 5. Check for opportunity title or organizer tokens in path
  const tokens = `${opportunityTitle} ${organizer}`
    .toLowerCase()
    .split(/[\s,._-]+/)
    .filter((t) => t.length >= 3 && !/^(the|and|for|with|from|2026|hackathon|grant|program|opportunity)$/i.test(t));

  const hasTokenMatch = tokens.some((token) => fullPath.includes(token) || hostname.includes(token));

  if (hasRegIntent && hasTokenMatch) {
    return { isValid: true, status: "verified", reason: "Verified registration path with opportunity keywords." };
  }

  if (hasRegIntent) {
    return { isValid: true, status: "verified", reason: "Registration path detected on official domain." };
  }

  if (hasTokenMatch && path.length > 3) {
    return { isValid: true, status: "verified", reason: "Dedicated opportunity page detected on official domain." };
  }

  return {
    isValid: false,
    status: "unable_to_verify",
    reason: "Link does not show direct relation or registration intent for this opportunity.",
  };
}

/**
 * Searches candidate URLs from analysis, resources, and links to find an authentic official registration link.
 * Never defaults to corporate root homepages.
 */
export function findOfficialRegistrationLink(candidateUrls = [], opportunityTitle = "", organizer = "") {
  for (const rawUrl of candidateUrls) {
    if (!rawUrl) continue;
    const check = verifyRegistrationLink(rawUrl, opportunityTitle, organizer);
    if (check.isValid) {
      let label = "Official Registration Page";
      if (/apply/i.test(rawUrl)) label = "Official Application Portal";
      else if (/hackathon/i.test(rawUrl)) label = "Official Hackathon Portal";
      return {
        url: rawUrl.startsWith("http") ? rawUrl : `https://${rawUrl}`,
        label,
        status: "verified",
        reason: check.reason,
      };
    }
  }

  return {
    url: null,
    label: null,
    status: candidateUrls.length > 0 ? "unable_to_verify" : "not_found",
    reason: "Official registration link not found in verified sources.",
  };
}

/**
 * Backward compatibility: returns company reference info WITHOUT labeling it as an official registration link.
 */
export function resolveCompanyLink(reel) {
  if (!reel) return null;
  const analysis = reel.analysis || {};
  const explore = analysis.explore || {};

  const textToScan = [
    explore.organizer || "",
    reel.title || "",
    analysis.summary || "",
    reel.caption || "",
    reel.transcript || "",
    ...(analysis.tags || []),
  ].join(" ");

  for (const comp of KNOWN_COMPANIES) {
    if (comp.regex.test(textToScan)) {
      return {
        name: comp.name,
        domain: comp.domain,
        url: comp.url,
        label: `${comp.name} (${comp.domain})`,
        isGenericRoot: true,
      };
    }
  }

  return null;
}

