# Implementation Slice Plan — File Canonicalizer v0.5

Feature: Document canonicalization — classify, extract, and produce a canonical filename and manifest for one submitted file.

---

## Slice Table

| Slice | Name | AC Addressed | Test Targets | Dependencies |
|-------|------|-------------|--------------|--------------|
| 1 | Empty and unreadable file rejection | AC-02 (FAIL), REQ-08, REQ-14 | `test_fail_empty_file` `test_fail_whitespace_only` `test_fail_response_has_exactly_two_fields` | None — first slice |
| 2 | Document type classification — approved types | AC-01-1, REQ-05 | `test_pass_meeting_with_clear_date` `test_classification_happy_path_meeting_heading` `test_pass_doc_id_uses_underscore_separator` | Slice 1 |
| 3 | Unsupported type rejection with FAIL response | AC-01-2, REQ-08, REQ-14 | `test_fail_unsupported_doc_type` `test_fail_has_no_manifest_key` | Slice 2 |
| 4 | Ambiguity detection — multiple type matches trigger WARN | AC-01-3, REQ-05 | `test_ambiguous_meeting_report_returns_warn` `test_ambiguous_warn_failure_reason_mentions_both_types` | Slice 2 |
| 5 | Date extraction and ISO normalization | AC-01-1, REQ-11 (WARN trigger) | `test_pass_meeting_with_clear_date` `test_pass_report_with_prose_date` `test_warn_missing_date_uses_today_as_fallback` | Slice 2 |
| 6 | Key field extraction with date guard | AC-01-1, AC-01-3, REQ-05 | `test_short_agenda_key_field_is_not_a_date` `test_date_as_key_field_fallback_triggers_warn` | Slice 5 |
| 7 | Flat manifest record assembly — PASS and WARN | AC-01-1, AC-01-4, REQ-25, REQ-03 | `test_pass_manifest_has_exactly_five_fields` `test_pass_check_result_in_manifest` `test_pass_has_canonical_name` `test_determinism_three_runs` | Slices 2, 5, 6 |
| 8 | WARN gate — reviewer fields block ingestion | AC-02-1, AC-02-2, AC-02-3, AC-02-4, REQ-11, REQ-09 | `test_warn_reviewed_by_is_null_initially` `test_warn_gate_rejects_automated_ingestion` `test_warn_resolution_trail_field_format` | Slice 7 |

---

## Slice Design Notes

**Slice boundary decision:** Date extraction (Slice 5) and key field extraction (Slice 6) are separate because the date WARN condition (inferred date) is independent from the key field WARN condition (date-as-key-field). Each slice has exactly one failure mode, making RED/GREEN cycles cleaner.

**AC spanning multiple slices:** AC-01-3 (ambiguous type) spans Slices 4 and 7. The WARN trigger happens in classification but the WARN record shape is built in manifest assembly. The interface contract between them must be explicit before Slice 7 starts.

**Review time per slice:** Each slice has 1–2 functions and 2–4 test targets. All are reviewable in under 15 minutes. Slice 7 (manifest assembly) is the largest with 4 tests but all assert against the same flat record schema.
