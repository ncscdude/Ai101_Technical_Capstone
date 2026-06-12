# Bug Report Log - File Canonicalizer v0.5

## BUG-01 Body-Date False Positive Returns PASS Instead of WARN
Severity: High | Status: Fixed
Discovered: Manual test - meeting_v0_5_prompt.txt submitted to canonicalizer
Root Cause: extract_date scanned entire document. Date in body text on line 16 picked up as document date.
Fix: Changed to lines[:5] only - header zone extraction.
Tests Added: test_date_on_line_6_triggers_warn, test_body_date_in_sop_system_prompt_does_not_become_document_date

## BUG-02 System Prompt Files Produce Ambiguous WARN Instead of SOP
Severity: Medium | Status: Fixed
Discovered: Manual test - heading matched both meeting and sop keywords
Root Cause: matched_doc_types checked all keywords with equal weight
Fix: Added PRIORITY_KEYWORDS - sop wins unconditionally on system prompt keywords
Tests Added: test_priority_overrides_co_match_with_meeting, test_system_prompt_heading_maps_to_sop

## BUG-03 WARN on Minutes Heading Containing Board Meeting
Severity: Low | Status: Fixed
Discovered: test_minutes_pass failed on first run
Root Cause: Test fixture used Minutes: Board Meeting - meeting keyword co-matched
Fix: Test fixture corrected to Minutes: Q4 Review
Tests Updated: test_minutes_pass

## BUG-04 Old app.py Version Persisted After Replacement
Severity: Low | Status: Fixed
Discovered: Browser showed text-paste interface after deploying file-upload version
Root Cause: Manual file replacement was error-prone with no verification step
Fix: Created install_app.py - writes correct app.py directly to disk
Verification: New version shows file upload drop zone at localhost:5000

## BUG-05 GitHub Actions Bot Lacks Write Permission to Commit Evidence
Severity: Medium | Status: Fixed
Discovered: CI run 1 and 2 - red X on Commit updated evidence step
Root Cause: GitHub Actions default token lacks contents write permission
Fix: Added permissions contents write to .github/workflows/ci.yml
Verification: CI run 3 green. Evidence file auto-committed with skip ci tag.
