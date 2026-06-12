"""
File Canonicalizer v0.5.

Deterministic capstone MVP:
- classify before extraction
- allow six approved document types only
- return PASS/WARN canonical records with check_result inside the record
- return FAIL as a two-field failure response
- never rename, move, or modify files on disk
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


APPROVED_DOC_TYPES = ("meeting", "agenda", "minutes", "sop", "checklist", "report")

DOC_TYPE_KEYWORDS = {
    "meeting": ("meeting",),
    "agenda": ("agenda",),
    "minutes": ("minutes",),
    # Operator mapping rule: system prompt and config files propagate to sop (ADR-03)
    "sop": (
        "sop",
        "standard operating procedure",
        "standard operating",
        "procedure",
        "system prompt",
        "prompt version",
        "schema version",
        "core profile",
    ),
    "checklist": ("checklist", "check list"),
    "report": ("report",),
}

# Priority overrides: if any keyword matches here, that doc_type wins unconditionally.
# Prevents co-matches when a system prompt heading also contains incidental type words.
PRIORITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sop": ("system prompt", "prompt version", "schema version", "core profile"),
}

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


@dataclass(frozen=True)
class ExtractedDate:
    value: str
    source_hint: str
    snippet: str
    inferred: bool = False


def canonicalize(text: str, filename: str, today: date | None = None) -> dict[str, Any]:
    """Return a PASS/WARN canonical record or a FAIL failure response."""
    today = today or date.today()

    if not text or not text.strip():
        return failure_response("File is empty. No content to classify or extract.")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    doc_type_result = classify_doc_type(lines)

    if doc_type_result["check_result"] == "FAIL":
        return failure_response(
            "Detected type 'unknown' is not in the approved list: "
            + ", ".join(APPROVED_DOC_TYPES)
            + "."
        )

    if doc_type_result["check_result"] == "WARN":
        return {
            "check_result": "WARN",
            "failure_reason": doc_type_result["failure_reason"],
            "candidate_doc_types": doc_type_result["candidate_doc_types"],
            "source_hint": doc_type_result["source_hint"],
            "reviewed_by": None,
            "review_timestamp": None,
        }

    doc_type = doc_type_result["doc_type"]
    doc_type_hint = doc_type_result["source_hint"]
    doc_type_snippet = doc_type_result["snippet"]

    extracted_date = extract_date(lines, today)
    key_field, key_hint, key_snippet = extract_key_field(lines, doc_type)

    warn_reasons: list[str] = []
    if extracted_date.inferred:
        warn_reasons.append(
            f"Date not found in document. Today ({extracted_date.value}) used as fallback. "
            "Reviewer must confirm."
        )

    if key_field is None:
        key_field = "UNKNOWN"
        key_hint = "[manual review required: key_field not found]"
        key_snippet = ""
        warn_reasons.append("key_field could not be extracted. Reviewer must supply it.")

    doc_id = build_doc_id(doc_type, extracted_date.value, key_field)
    canonical_name = doc_id + Path(filename).suffix.lower()

    record: dict[str, Any] = {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "date": extracted_date.value,
        "key_field": key_field,
        "canonical_name": canonical_name,
        "check_result": "WARN" if warn_reasons else "PASS",
        "source_hint": {
            "doc_type": doc_type_hint,
            "date": extracted_date.source_hint,
            "key_field": key_hint,
        },
        "extraction_snippet": {
            "doc_type": doc_type_snippet,
            "date": extracted_date.snippet,
            "key_field": key_snippet,
        },
    }

    if warn_reasons:
        record["failure_reason"] = " | ".join(warn_reasons)
        record["reviewed_by"] = None
        record["review_timestamp"] = None

    return record


def classify_doc_type(lines: list[str]) -> dict[str, Any]:
    """Classify from the first meaningful heading; ambiguous headings become WARN."""
    for index, line in enumerate(lines[:10], start=1):
        matches = matched_doc_types(line)
        if len(matches) == 1:
            return {
                "check_result": "PASS",
                "doc_type": matches[0],
                "source_hint": f"Line {index}: heading",
                "snippet": line,
            }
        if len(matches) > 1:
            return {
                "check_result": "WARN",
                "failure_reason": (
                    "Ambiguous document type. Candidate types found in the heading: "
                    + ", ".join(matches)
                    + ". Reviewer must choose before extraction."
                ),
                "candidate_doc_types": matches,
                "source_hint": f"Line {index}: heading",
                "snippet": line,
            }

    return {"check_result": "FAIL"}


def matched_doc_types(line: str) -> list[str]:
    lower = line.lower()
    # Priority check: operator mapping rule wins unconditionally (ADR-03).
    for doc_type, keywords in PRIORITY_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return [doc_type]
    matches: list[str] = []
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            matches.append(doc_type)
    return matches


def extract_date(lines: list[str], today: date) -> ExtractedDate:
    for index, line in enumerate(lines[:5], start=1):
        parsed = parse_date(line)
        if parsed:
            return ExtractedDate(parsed, f"Line {index}: date", line)

    fallback = today.isoformat()
    return ExtractedDate(
        fallback,
        "[inferred: today's date - not found in document]",
        "",
        inferred=True,
    )


def parse_date(text: str) -> str | None:
    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if iso:
        return f"{iso.group(1)}-{iso.group(2)}-{iso.group(3)}"

    slash = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if slash:
        month, day, year = map(int, slash.groups())
        return datetime(year, month, day).date().isoformat()

    day_month = re.search(
        r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b",
        text,
        re.IGNORECASE,
    )
    if day_month:
        day = int(day_month.group(1))
        month = month_number(day_month.group(2))
        year = int(day_month.group(3))
        if month:
            return datetime(year, month, day).date().isoformat()

    month_day = re.search(
        r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})\b",
        text,
        re.IGNORECASE,
    )
    if month_day:
        month = month_number(month_day.group(1))
        day = int(month_day.group(2))
        year = int(month_day.group(3))
        if month:
            return datetime(year, month, day).date().isoformat()

    return None


def month_number(value: str) -> int | None:
    return MONTHS.get(value.lower().rstrip("."))


def extract_key_field(lines: list[str], doc_type: str) -> tuple[str | None, str, str]:
    for index, line in enumerate(lines[:15], start=1):
        if parse_date(line):
            continue

        candidate = strip_doc_type_words(line, doc_type)
        if candidate and len(candidate) >= 3 and not parse_date(candidate):
            return candidate, f"Line {index}: heading", line

    return None, "[key_field not found]", ""


def strip_doc_type_words(value: str, doc_type: str) -> str:
    cleaned = value
    for keyword in DOC_TYPE_KEYWORDS[doc_type]:
        cleaned = re.sub(re.escape(keyword), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*[:\-–—]+\s*", "", cleaned)
    cleaned = re.sub(r"\s*[:\-–—]+\s*$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def build_doc_id(doc_type: str, iso_date: str, key_field: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", key_field).strip("_")
    return f"{doc_type}_{iso_date}_{slug}"


def failure_response(reason: str) -> dict[str, str]:
    return {"check_result": "FAIL", "failure_reason": reason}


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonicalize extracted file text.")
    parser.add_argument("--text-file", required=True, help="Path to a plain-text extracted file.")
    parser.add_argument("--filename", required=True, help="Original filename, used for extension.")
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8")
    print(json.dumps(canonicalize(text, args.filename), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

