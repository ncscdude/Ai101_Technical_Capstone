# Implementation Slice Plan - File Canonicalizer v0.5

| Slice | Name | AC Addressed | Test Targets | Dependencies |
|-------|------|-------------|--------------|--------------|
| 1 | Empty and unreadable file rejection | AC-06 AC-07 | test_fail_empty_file test_fail_whitespace_only test_fail_response_has_exactly_two_fields | None |
| 2 | Document type classification | AC-01 | test_pass_meeting_with_clear_date test_classification_happy_path test_pass_doc_id_uses_underscore_separator | Slice 1 |
| 3 | Unsupported type rejection | AC-07 | test_fail_unsupported_doc_type test_fail_has_no_manifest_key | Slice 2 |
| 4 | Ambiguity detection | AC-05 | test_ambiguous_meeting_report_returns_warn test_ambiguous_warn_failure_reason_mentions_both_types | Slice 2 |
| 5 | Date extraction and ISO normalization | AC-04 | test_pass_meeting_with_clear_date test_pass_report_with_prose_date test_warn_missing_date_uses_today_as_fallback | Slice 2 |
| 6 | Key field extraction with date guard | AC-01 | test_short_agenda_key_field_is_not_a_date | Slice 5 |
| 7 | Flat manifest assembly PASS and WARN | AC-01 AC-02 AC-03 | test_pass_manifest_has_exactly_five_fields test_pass_has_canonical_name test_determinism_three_runs | Slices 2 5 6 |
| 8 | WARN gate reviewer fields block ingestion | AC-04 AC-06 | test_warn_reviewed_by_is_null_initially test_warn_gate_rejects_automated_ingestion | Slice 7 |
