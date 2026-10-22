/**
 * Utility functions for robust calendar date extraction, validation,
 * relative-date normalization with strict source anchors, and display formatting.
 *
 * Enforces date correctness across ReelVault:
 * - Rejects placeholders ("Date unavailable", "not specified", "soon", etc.)
 * - Validates true calendar dates (rejects non-existent dates like 2026-02-31)
 * - Normalizes relative dates only when a reliable source anchor date is provided
 * - Never invents dates or defaults to today/current date
 */

export const PLACEHOLDER_DATE_TERMS = new Set([
  "date unavailable",
  "unavailable",
  "not specified",
  "unknown",
  "tbd",
  "tba",
  "soon",
  "coming soon",
  "closed",
  "expired",
  "none",
  "null",
  "n/a",
  "na",
  "unspecified",
  "to be announced",
  "to be determined",
]);

/**
 * Checks if a string represents an unestablished or placeholder date.
 */
export function isPlaceholderDate(str) {
  if (!str) return true;
  const clean = String(str).trim().toLowerCase().replace(/[._-]/g, " ");
  return PLACEHOLDER_DATE_TERMS.has(clean) || clean.length === 0;
}

/**
 * Validates whether a YYYY-MM-DD string is an authentic, real calendar date.
 * Rejects out-of-range dates like 2026-02-31 or 2026-04-31.
 */
export function isValidCalendarDate(str) {
  if (!str || typeof str !== "string") return false;
  const match = str.trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return false;
  const y = parseInt(match[1], 10);
  const m = parseInt(match[2], 10);
  const d = parseInt(match[3], 10);
  if (m < 1 || m > 12 || d < 1 || d > 31 || y < 1900 || y > 2200) return false;
  const dt = new Date(Date.UTC(y, m - 1, d));
  return (
    dt.getUTCFullYear() === y &&
    dt.getUTCMonth() === m - 1 &&
    dt.getUTCDate() === d
  );
}

/**
 * Normalizes relative dates (e.g. "7 days left", "in 2 weeks") ONLY when
 * a reliable source anchor date is provided (e.g., post created_at).
 * Never uses current date / today if anchor is missing.
 */
export function parseRelativeDate(phrase, anchorDateStr) {
  if (!phrase || typeof phrase !== "string") return null;
  if (!anchorDateStr) return null;

  // Extract YYYY-MM-DD from anchor
  const anchorIso = String(anchorDateStr).slice(0, 10);
  if (!isValidCalendarDate(anchorIso)) return null;

  const clean = phrase.trim().toLowerCase();
  let daysOffset = null;

  const daysMatch = clean.match(/(?:in\s+)?(\d+)\s+days?(?:\s+left|\s+remaining)?/i);
  if (daysMatch) {
    daysOffset = parseInt(daysMatch[1], 10);
  } else {
    const weeksMatch = clean.match(/(?:in\s+)?(\d+)\s+weeks?(?:\s+left|\s+remaining)?/i);
    if (weeksMatch) {
      daysOffset = parseInt(weeksMatch[1], 10) * 7;
    } else if (/\btomorrow\b/i.test(clean)) {
      daysOffset = 1;
    }
  }

  if (daysOffset === null || Number.isNaN(daysOffset)) return null;

  const [y, m, d] = anchorIso.split("-").map((v) => parseInt(v, 10));
  const anchorDt = new Date(Date.UTC(y, m - 1, d));
  anchorDt.setUTCDate(anchorDt.getUTCDate() + daysOffset);

  const resY = anchorDt.getUTCFullYear();
  const resM = String(anchorDt.getUTCMonth() + 1).padStart(2, "0");
  const resD = String(anchorDt.getUTCDate()).padStart(2, "0");
  const resIso = `${resY}-${resM}-${resD}`;

  return isValidCalendarDate(resIso) ? resIso : null;
}

const MONTH_NAMES = {
  jan: 1, january: 1,
  feb: 2, february: 2,
  mar: 3, march: 3,
  apr: 4, april: 4,
  may: 5,
  jun: 6, june: 6,
  jul: 7, july: 7,
  aug: 8, august: 8,
  sep: 9, sept: 9, september: 9,
  oct: 10, october: 10,
  nov: 11, november: 11,
  dec: 12, december: 12,
};

/**
 * Parses textual dates that contain an explicit year (e.g., "15 November 2026", "October 26, 2026").
 * Rejects dates without an explicit year to prevent fabricating deadlines.
 */
function parseTextDateWithYear(str) {
  if (!str || typeof str !== "string") return null;
  const clean = str.trim();

  // Pattern 1: DD Month YYYY (e.g., "15th November 2026", "26 October 2026")
  const p1 = clean.match(/^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)[,\s]+(\d{4})$/i);
  if (p1) {
    const d = parseInt(p1[1], 10);
    const m = MONTH_NAMES[p1[2].toLowerCase()];
    const y = parseInt(p1[3], 10);
    if (m && y) {
      const iso = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      if (isValidCalendarDate(iso)) return iso;
    }
  }

  // Pattern 2: Month DD, YYYY (e.g., "November 15, 2026", "Oct 26, 2026")
  const p2 = clean.match(/^([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?[,\s]+(\d{4})$/i);
  if (p2) {
    const m = MONTH_NAMES[p2[1].toLowerCase()];
    const d = parseInt(p2[2], 10);
    const y = parseInt(p2[3], 10);
    if (m && y) {
      const iso = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      if (isValidCalendarDate(iso)) return iso;
    }
  }

  return null;
}

/**
 * Parses textual dates without an explicit year (e.g. "October 30", "30th October", "runs until October 30th")
 * ONLY when a reliable contextual year (e.g. from event title "Hacktoberfest 2026" or post metadata) is provided.
 * Never invents a year if context year is missing or ambiguous.
 */
function parseTextDateWithContextYear(str, contextYear) {
  if (!str || !contextYear) return null;
  const yearInt = parseInt(contextYear, 10);
  if (Number.isNaN(yearInt) || yearInt < 1900 || yearInt > 2200) return null;

  const clean = str.trim();

  // Pattern 1: DD Month (e.g. "30th October", "30 Oct")
  const p1 = clean.match(/(?:until|by|before|on|is|ends|closes)?\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\b/i);
  if (p1 && MONTH_NAMES[p1[2].toLowerCase()]) {
    const d = parseInt(p1[1], 10);
    const m = MONTH_NAMES[p1[2].toLowerCase()];
    const iso = `${yearInt}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    if (isValidCalendarDate(iso)) return iso;
  }

  // Pattern 2: Month DD (e.g. "October 30th", "Oct 30", "runs until October 30th")
  const p2 = clean.match(/(?:until|by|before|on|is|ends|closes)?\s*([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b/i);
  if (p2 && MONTH_NAMES[p2[1].toLowerCase()]) {
    const m = MONTH_NAMES[p2[1].toLowerCase()];
    const d = parseInt(p2[2], 10);
    const iso = `${yearInt}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    if (isValidCalendarDate(iso)) return iso;
  }

  return null;
}

/**
 * Returns an established YYYY-MM-DD date if usable, or null if unestablished.
 * Does NOT invent dates or substitute current date.
 */
export function resolveUsableIsoDate(value, anchorDateStr = null, contextText = null) {
  if (!value) return null;
  const str = String(value).trim();
  if (isPlaceholderDate(str)) return null;

  // Direct ISO check (YYYY-MM-DD)
  const isoMatch = str.match(/\b(20\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))\b/);
  if (isoMatch && isValidCalendarDate(isoMatch[1])) {
    return isoMatch[1];
  }

  // Textual date with explicit year
  const textDateIso = parseTextDateWithYear(str);
  if (textDateIso) {
    return textDateIso;
  }

  // Relative date check (requires valid anchorDateStr)
  if (anchorDateStr) {
    const relIso = parseRelativeDate(str, anchorDateStr);
    if (relIso) return relIso;
  }

  // Partial date check with reliable contextual year (e.g. "Hacktoberfest 2026 ... October 30th")
  const context = `${contextText || ""} ${anchorDateStr || ""}`;
  const contextYearMatch = context.match(/\b(20\d{2})\b/);
  if (contextYearMatch) {
    const contextIso = parseTextDateWithContextYear(str, contextYearMatch[1]);
    if (contextIso) return contextIso;
  }

  return null;
}

/**
 * Formats a calendar date for user display. Returns "Date unavailable" if invalid.
 */
export function formatDisplayDate(value, anchorDateStr = null, contextText = null) {
  const iso = resolveUsableIsoDate(value, anchorDateStr, contextText);
  if (!iso) return "Date unavailable";
  const [y, m, d] = iso.split("-").map((v) => parseInt(v, 10));
  const dt = new Date(Date.UTC(y, m - 1, d));
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(dt);
}
