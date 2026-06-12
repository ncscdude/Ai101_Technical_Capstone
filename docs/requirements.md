# Requirements — File Canonicalizer v0.5
## EARS Notation (Easy Approach to Requirements Syntax)

---

## REQ-05 — Document Type Classification (Event-driven)

**Original:** The system should classify the document type before doing anything else.

**EARS:** When a file is submitted for canonicalization, the system SHALL classify its `doc_type` against the six approved values — `meeting`, `agenda`, `minutes`, `sop`, `checklist`, `report` — before any field extraction step runs.

**Example (correct):**
- Input: file with heading "Q2 Budget Review Meeting"
- System classifies `doc_type: meeting`, records `source_hint: Line 1: heading`
- Extraction of date and key_field proceeds only after classification returns a valid type

**Counter-example (incorrect):**
- Input: file with heading "Q2 Slides" — no approved type match
- ❌ System continues to extract fields using a presentation rule
- ✅ System halts and returns `check_result: FAIL` with `failure_reason` naming the approved list

**Needs clarification:** None. The six approved types are locked.

---

## REQ-08 / REQ-14 — Unreadable and Unsupported File Rejection (Unwanted behavior)

**Original:** The system should not accept files it cannot read or files of the wrong type.

**EARS:** If a file is unreadable or its `doc_type` is not in the approved list, the system SHALL return `check_result: FAIL` and SHALL log `failure_reason` stating the specific cause. No manifest SHALL be produced for a FAIL result.

**Example (correct):**
- Input: scanned PDF with no text layer
- System returns `check_result: FAIL`, `failure_reason: "File contains no extractable text. Manual OCR required."`
- No manifest written

**Counter-example (incorrect):**
- Input: same scanned PDF
- ❌ System returns partial manifest with null fields and `check_result: WARN`
- ✅ FAIL only — WARN implies the reviewer can fix it manually; an unreadable file cannot be fixed without OCR

**FAIL response shape:** exactly two fields — `check_result` and `failure_reason`. No other keys.

---

## REQ-11 — WARN Human Review Gate (State-driven)

**Original:** A file with a WARN result should not be allowed into the system until a human reviews it.

**EARS:** While a manifest has `check_result: WARN`, the system SHALL keep `reviewed_by` and `review_timestamp` null until a human reviewer resolves the issue. The file SHALL NOT be accepted into the canonical store until both fields are populated.

**Example (correct):**
- Input: meeting note with no date in first five lines
- System returns `check_result: WARN`, `failure_reason: "Date not found. Today used. Reviewer must confirm."`
- `reviewed_by: null`, `review_timestamp: null`
- Reviewer confirms, populates both fields — file accepted

**Counter-example (incorrect):**
- Same meeting note with no date
- ❌ System auto-accepts because `check_result` is not FAIL
- ✅ Ingestion blocked until `reviewed_by` and `review_timestamp` are both populated

---

## REQ-03 — Canonical Filename Format (Ubiquitous)

The system SHALL construct the canonical filename as: `YYYY-MM-DD_doc_type_key-field.ext`
- Separator between all components: underscore `_`
- `key_field` slug: alphanumeric and underscores only
- Extension: preserved from original filename, lowercased

---

## REQ-25 — Four-Field Manifest (Ubiquitous)

Every PASS or WARN record SHALL contain exactly these fields:
`doc_id` | `doc_type` | `date` | `key_field` | `check_result`

Plus: `source_hint`, `extraction_snippet`, and on WARN: `failure_reason`, `reviewed_by`, `review_timestamp`.

`source_hint` SHALL be present and non-null on every PASS record.

---

## REQ-09 — Reviewer Identity Format (Ubiquitous)

`reviewed_by` SHALL accept a free-text name string, maximum 100 characters. No credentials, email, or personal identifiers stored.
