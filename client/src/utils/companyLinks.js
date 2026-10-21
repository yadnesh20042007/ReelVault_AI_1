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

  // 1. Check known company/organization matches
  for (const comp of KNOWN_COMPANIES) {
    if (comp.regex.test(textToScan)) {
      return {
        name: comp.name,
        domain: comp.domain,
        url: comp.url,
        label: `${comp.name} Official Portal (${comp.domain})`,
      };
    }
  }

  // 2. Check candidate links that are valid and non-generic-google
  const candidateUrls = [
    ...(analysis.sources || []).map((s) => s.url),
    ...(analysis.resources || []).map((r) => r.url),
    ...(analysis.links || []),
  ].filter(Boolean);

  for (const rawUrl of candidateUrls) {
    if (isGenericGoogleUrl(rawUrl)) continue;
    if (/(instagram\.com|tiktok\.com|youtube\.com|youtu\.be|facebook\.com)/i.test(rawUrl)) continue;
    try {
      const u = new URL(rawUrl.startsWith("http") ? rawUrl : `https://${rawUrl}`);
      const hostname = u.hostname.replace(/^www\./, "");
      if (hostname && !hostname.includes("google.com")) {
        return {
          name: hostname,
          domain: hostname,
          url: rawUrl.startsWith("http") ? rawUrl : `https://${rawUrl}`,
          label: `Official Page (${hostname})`,
        };
      }
    } catch {}
  }

  return null;
}
