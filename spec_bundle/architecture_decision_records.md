# Architecture Decision Records — File Canonicalizer v0.5

---

## ADR-01 — Deterministic Rules-Based Core

**Date:** 2026-06-10 | **Status:** Accepted

**Context:** The canonicalizer must produce identical output for identical input on every run. LLM inference is non-deterministic and cannot guarantee this property.

**Decision:** Core classification and extraction logic uses deterministic keyword matching and regex patterns only. No LLM calls in the core processing path.

**Consequences:** Output is fully reproducible. Classification depends on explicit keywords — unusual headings may require manual review (WARN).

---

## ADR-02 — Six Approved Document Types Only

**Date:** 2026-06-10 | **Status:** Accepted

**Context:** An open-ended type system produces inconsistent metadata and makes the file store unsearchable.

**Decision:** Only six types accepted: `meeting`, `agenda`, `minutes`, `sop`, `checklist`, `report`. Any other type returns FAIL immediately.

**Consequences:** File store remains consistently typed. New types require updating `APPROVED_DOC_TYPES`, `DOC_TYPE_KEYWORDS`, tests, and documentation.

---

## ADR-03 — Field Presence as PASS/WARN/FAIL Gate Condition

**Date:** 2026-06-10 | **Status:** Accepted

**Context:** The system needs a rule to decide when a manifest qualifies as PASS, WARN, or FAIL. Two reasonable approaches exist: check whether a numeric confidence score exceeds a threshold, or check whether all required fields are present with source citations. The choice determines whether the gate is deterministic across agents and repeated runs.

**Decision:** Gate conditions are based on field presence only: PASS when all required fields are extracted with source citations, WARN when one field is missing or ambiguous, FAIL when the file is unreadable or the doc_type is not in the approved list.

### Options Considered

| | Option A — Confidence Score Threshold | Option B — Field Presence Check |
|--|--------------------------------------|----------------------------------|
| **Description** | PASS if confidence ≥ 0.7, WARN if 0.4–0.7, FAIL if < 0.4 | PASS when all required fields extracted with source citation, WARN when one field missing, FAIL when unreadable or unapproved type |
| **Pros** | Familiar to ML teams. Provides granular signal about model certainty. | Fully deterministic. Model-agnostic. No calibration required between agents. |
| **Cons** | LLM confidence scores vary between runs even at temperature 0. Claude and Copilot return scores in different formats — not directly comparable. Thresholds require 100-file validation dataset to justify. | Binary — does not distinguish barely-extracted vs clearly-stated fields. Confidence still recorded as informational only. |

**Rationale:** The project requires parity between Claude and Copilot on all PASS cases. A confidence threshold gate produces different results between agents because their score outputs are not on the same scale. Field presence is observable and consistent regardless of which agent runs.

**Consequences:** A file where the model extracts a field with low confidence but technically meets the field presence rule will return PASS even if the extracted value is uncertain. Mitigated by the `source_hint` requirement and human reviewer gate.

**Revisit triggers:**
- Field presence alone produces too many false PASS results on a real file set
- A calibrated confidence mapping between agents is established on a 100-file validated dataset
- PASS cases produce obviously wrong canonical filenames in production

---

## ADR-04 — Header-Zone Date Extraction (Lines 1–5)

**Date:** 2026-06-11 | **Status:** Accepted

**Context:** Early implementation scanned the entire document for dates, causing false positives when documents contained dates in body text.

**Decision:** `extract_date` scans only the first five non-empty lines. Dates beyond line 5 are ignored; system falls back to today's date and returns WARN.

**Revisit triggers:** Documents with consistently valid dates beyond line 5 in a real file set.

---

## ADR-05 — Priority Classification for System Prompt / Config Files

**Date:** 2026-06-11 | **Status:** Accepted

**Context:** System prompt files contain "system prompt" in headings that also incidentally contain words like "Meeting," causing ambiguous co-matches.

**Decision:** `PRIORITY_KEYWORDS` dictionary introduced. When any priority keyword matched, that type returned immediately. Current mapping: `system prompt`, `prompt version`, `schema version`, `core profile` → `sop`.

**Revisit triggers:** Priority mapping needs expansion for new file classes.

---

## ADR-06 — Web Interface Uses Local Processing Only

**Date:** 2026-06-11 | **Status:** Accepted

**Context:** Earlier version called Anthropic API, requiring an API key and incurring per-request costs — a barrier for reviewers running the tool locally.

**Decision:** Flask web interface calls `canonicalizer.py` directly. No external API calls. Zero cost to run.

**Revisit triggers:** Feature requirements exceed deterministic rule capabilities and LLM integration becomes necessary.
