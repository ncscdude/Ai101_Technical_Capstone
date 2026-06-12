# AGENTS.md - File Canonicalizer v0.5
## AI Agent Context and Guardrails

Read this before making any changes to canonicalizer.py, tests, or spec_bundle documents.

## What This Project Does
Reads one incoming file, classifies its document type, extracts a primary date and key
identifying field, and returns a canonical filename and metadata manifest with PASS WARN or FAIL.

## Approved Document Types (Locked)
meeting | agenda | minutes | sop | checklist | report
Do NOT add new types without a schema change PR.

## Critical Decisions - Do Not Reverse

### Gate Condition: Field Presence Not Confidence Score (ADR-03)
PASS WARN FAIL determined by whether required fields are present with source citations.
Do NOT add a numeric confidence score threshold. This was proposed and rejected.
Revisit only if false PASS rate exceeds 10 percent on a real file set.

### Header-Zone Date Extraction Lines 1-5 Only (ADR-04)
extract_date scans lines[:5] only. Do NOT change to full document scan.
Body-text dates produce false PASS results. Confirmed bug BUG-01.

### Priority Classification SOP Wins on Config Files (ADR-05)
PRIORITY_KEYWORDS maps system prompt and config keywords to sop.
Do NOT remove. Co-match with meeting keyword was confirmed bug BUG-02.

### No Files Modified on Disk (NG-01)
The canonicalizer proposes filenames only. Never renames moves or writes files.

### No External API Calls in app.py (ADR-06)
app.py calls canonicalizer.py directly. Do NOT re-add Anthropic API calls.

## Out of Scope v0.5 - Do NOT Build
- Batch processing or folder-watching
- Searchable index or recall interface
- External storage integrations
- OCR for scanned PDFs
- Input sanitization

## Test Requirements
Run python -m unittest discover -s tests -v before committing.
All 46 tests must pass. A failing test is a blocking issue.

## Manifest Schema (Locked v1.0)
PASS WARN: doc_id doc_type date key_field canonical_name check_result source_hint extraction_snippet
WARN only: failure_reason reviewed_by review_timestamp
FAIL only: check_result failure_reason

## References
- spec_bundle/architecture_decision_records.md
- spec_bundle/requirements_ears.md
- spec_bundle/goals_non_goals.md
- evidence/test_results.txt
