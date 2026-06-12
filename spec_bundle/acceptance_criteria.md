# Acceptance Criteria - File Canonicalizer v0.5

## AC-01 PASS on Complete Record
Given a document with recognized type explicit date and extractable key field
When the canonicalizer processes it
Then check_result is PASS all five manifest fields populated source_hint non-null
Test: test_pass_manifest_has_exactly_five_fields

## AC-02 PASS Canonical Name Format
Given a PASS record with doc_type date and key_field all populated
When canonical name is constructed
Then canonical_name follows YYYY-MM-DD_doc_type_key-field.ext exactly
Test: test_pass_has_canonical_name

## AC-03 Deterministic Output
Given the same input file
When submitted three consecutive times
Then doc_id and canonical_name identical across all three runs
Test: test_determinism_three_runs

## AC-04 WARN on Missing Date
Given a document with no date in first five lines
When canonicalizer processes it
Then check_result WARN today used as fallback reviewed_by and review_timestamp null
Test: test_warn_missing_date_uses_today_as_fallback

## AC-05 WARN on Ambiguous Type
Given a document heading matching more than one approved type
When canonicalizer processes it
Then check_result WARN candidate_doc_types lists all matches no extraction attempted
Test: test_ambiguous_meeting_report_returns_warn

## AC-06 FAIL on Empty File
Given a file with no extractable text
When canonicalizer processes it
Then check_result FAIL response contains exactly two fields
Test: test_fail_empty_file

## AC-07 FAIL on Unapproved Type
Given a document whose type is not in the approved list
When canonicalizer processes it
Then check_result FAIL failure_reason names approved list no manifest produced
Test: test_fail_unsupported_doc_type

## Traceability Matrix
| AC | Test | Status |
|----|------|--------|
| AC-01 | test_pass_manifest_has_exactly_five_fields | pass |
| AC-02 | test_pass_has_canonical_name | pass |
| AC-03 | test_determinism_three_runs | pass |
| AC-04 | test_warn_missing_date_uses_today_as_fallback | pass |
| AC-05 | test_ambiguous_meeting_report_returns_warn | pass |
| AC-06 | test_fail_empty_file | pass |
| AC-07 | test_fail_unsupported_doc_type | pass |
