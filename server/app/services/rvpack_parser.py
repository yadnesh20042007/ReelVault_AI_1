import json
import re
from typing import Any

from app.schemas.verification import RVPackData

_HEADER_PATTERN = re.compile(
    r"^(?:---|\=\=\=|\[|#+\s*)?(TRANSCRIPT|AUDIO_TRANSCRIPT|SPEECH|ON[-_ ]SCREEN(?:[-_ ]TEXT)?|ONSCREEN|META(?:DATA)?)(?:\]|---|\=\=\=|\:)?\s*$",
    re.IGNORECASE,
)


def _canonical_section_name(raw_name: str) -> str:
    norm = re.sub(r"[-_ ]", "", raw_name).upper()
    if "TRANSCRIPT" in norm or "SPEECH" in norm:
        return "TRANSCRIPT"
    if "SCREEN" in norm:
        return "ON_SCREEN"
    if "META" in norm:
        return "META"
    return norm


def _parse_meta_section(meta_text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    cleaned = meta_text.strip()
    if not cleaned:
        return meta

    # Check if the entire meta block is JSON
    if cleaned.startswith("{") and cleaned.endswith("}"):
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    for line in cleaned.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
        elif "=" in line:
            k, v = line.split("=", 1)
            meta[k.strip().lower()] = v.strip()
    return meta


def parse_rvpack(content: str) -> RVPackData:
    """Parse a .rvpack text input containing TRANSCRIPT, ON_SCREEN, and META sections.
    
    Robust to multiple delimiter conventions (---, ===, [], markdown headings, colons).
    """
    if not content or not content.strip():
        return RVPackData(raw_text="")

    sections: dict[str, list[str]] = {
        "TRANSCRIPT": [],
        "ON_SCREEN": [],
        "META": [],
    }
    sections_found: list[str] = []
    current_section: str | None = None

    for line in content.splitlines():
        header_match = _HEADER_PATTERN.match(line.strip())
        if header_match:
            c_name = _canonical_section_name(header_match.group(1))
            current_section = c_name
            if c_name not in sections_found:
                sections_found.append(c_name)
            if c_name not in sections:
                sections[c_name] = []
            continue

        if current_section:
            sections[current_section].append(line)
        else:
            # Lines before any header - if no header seen yet, accumulate under TRANSCRIPT
            sections["TRANSCRIPT"].append(line)

    transcript_text = "\n".join(sections.get("TRANSCRIPT", [])).strip()
    on_screen_text = "\n".join(sections.get("ON_SCREEN", [])).strip()
    meta_text = "\n".join(sections.get("META", [])).strip()
    meta_dict = _parse_meta_section(meta_text)

    return RVPackData(
        transcript=transcript_text,
        on_screen=on_screen_text,
        meta=meta_dict,
        raw_text=content,
        sections_found=sections_found,
    )
