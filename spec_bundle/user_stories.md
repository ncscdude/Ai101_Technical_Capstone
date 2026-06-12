# User Stories — File Canonicalizer v0.5

---

## Story 1 — Document Type Classification

**Source EARS:** REQ-05

**As a** FILE_OWNER,  
**I want** the system to identify what type of document I submitted before doing anything else,  
**so that** the correct extraction rules are applied and I receive an accurate canonical filename and manifest.

### Acceptance Criteria

| AC | Given | When | Then |
|----|-------|------|------|
| AC-1 (happy path) | A text-readable meeting notes file with a clear heading on line 1 | File is submitted for canonicalization | System classifies `doc_type: meeting`, records `source_hint: Line 1: heading`, proceeds to extract date and key_field. Classification completes in under 3 seconds. |
| AC-2 (error/fallback) | A file whose detected type is "presentation" — not in the approved list | File is submitted | System returns `check_result: FAIL` with `failure_reason` stating detected type and approved list. No extraction runs. No manifest produced. |
| AC-3 (AI-specific) | A file with "Meeting Summary" as title but "Q2 Report" as a section heading — ambiguous | System attempts classification | System returns `check_result: WARN` with both candidate types in `failure_reason`. No extraction proceeds until REVIEWER resolves. |
| AC-4 (determinism) | Same file submitted three consecutive times | Classification runs each time | `doc_type` and `canonical_name` are identical across all three runs with zero variation. |

### Edge Cases

| # | Scenario | Expected Behavior | Why It Matters |
|---|----------|-------------------|----------------|
| E-1 | Empty input — blank file 0 bytes | `check_result: FAIL`, `failure_reason: "File is empty."` No classification attempted. | Attempting classification on empty input risks a hallucinated doc_type. |
| E-2 | Contradictory input — title says "Meeting" but body is structured as a numbered SOP | `check_result: WARN` with both candidate types and source_hints shown. Extraction blocked. | Wrong classification produces wrong key_field rule and unrecallable canonical filename. |

### NFR Metadata

| NFR | Value |
|-----|-------|
| Latency | p95 under 3 seconds. Failure threshold: 30 seconds → FAIL. |
| Privacy | No full document text logged. Only `source_hint` and `extraction_snippet` stored. |
| Auditability | Every run logged with: input filename, doc_type, source_hint, check_result, timestamp. Log is append-only. |
| Rollback | FILE_OWNER resubmits. Prior manifest not overwritten — new run creates new record. |
| Cost | Zero. Local processing only. No API call per run. |

---

## Story 2 — WARN Human Review Gate

**Source EARS:** REQ-11

**As a** REVIEWER,  
**I want** the system to block any WARN file from entering the canonical store until I have confirmed the resolution,  
**so that** incomplete or ambiguous records never contaminate the dataset without accountability.

### Acceptance Criteria

| AC | Given | When | Then |
|----|-------|------|------|
| AC-1 (happy path) | Manifest has `check_result: WARN`, `failure_reason: "Date not found — today used."`, `reviewed_by: null` | REVIEWER confirms today's date is correct and populates `reviewed_by` and `review_timestamp` | `check_result` updated to PASS. File accepted. Run log updated with reviewed_by, review_timestamp, and resolved state. Write completes under 3 seconds. |
| AC-2 (error/fallback) | Manifest has `check_result: WARN`, `reviewed_by: null` | Automated process attempts ingestion | System rejects ingestion: "reviewed_by and review_timestamp required before ingestion." Bypass attempt logged with timestamp. |
| AC-3 (AI-specific) | Manifest has WARN because system found conflicting dates — "Q1 2026" on line 1 and "Q2 2026" in body | REVIEWER presented with both candidates and source_hints | REVIEWER selects correct period. Manifest updated. `reviewed_by` and `review_timestamp` set. `check_result` → PASS. No re-run required. |
| AC-4 | Resolved WARN manifest has both reviewer fields populated | Manifest inspected | `reviewed_by` is non-null string ≤ 100 chars. `review_timestamp` is valid ISO 8601 datetime. Run log shows complete resolution trail. |

### Edge Cases

| # | Scenario | Expected Behavior | Why It Matters |
|---|----------|-------------------|----------------|
| E-1 | Missing input — REVIEWER submits `reviewed_by` as empty string | System rejects: "reviewed_by cannot be empty." Manifest stays WARN. No partial update saved. | Empty `reviewed_by` bypasses accountability gate without audit trail. |
| E-2 | Model failure — `failure_reason` is null on a WARN record | Manifest still blocked. `failure_reason` set to "[SYSTEM ERROR: failure_reason not populated — manual review required]". Run flagged for investigation. | WARN without `failure_reason` gives REVIEWER nothing to resolve. |

### NFR Metadata

| NFR | Value |
|-----|-------|
| Latency | REVIEWER resolution target: under 60 seconds of human effort. System write: under 3 seconds. No LLM call during resolution. |
| Privacy | `reviewed_by` stores reviewer name only — max 100 characters. No credentials or email stored. |
| Auditability | Every WARN state and resolution logged append-only: original WARN, failure_reason, reviewed_by, review_timestamp, resolved check_result. |
| Rollback | REVIEWER can revert to WARN by clearing both reviewer fields. Original WARN entry remains in log as audit record. |
| Cost | No LLM call during WARN resolution. Human effort only. |
