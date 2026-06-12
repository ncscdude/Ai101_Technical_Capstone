"""
Tests for canonicalizer.py

Coverage:
  - PASS / WARN / FAIL gate logic
  - Header-zone date constraint (lines[:5] only)
  - Body-date false-positive regression
  - Priority classification: system prompt / config → sop
  - Ambiguous doc type → WARN
  - Unknown doc type → FAIL
  - Empty input → FAIL
  - Date format variants (ISO, slash, day-month, month-day)
  - key_field fallback when not found
"""

import unittest
from datetime import date

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canonicalizer import canonicalize, classify_doc_type, extract_date, parse_date


TODAY = date(2026, 6, 11)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_text(*lines: str) -> str:
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gate logic: PASS
# ---------------------------------------------------------------------------

class TestPass(unittest.TestCase):

    def test_report_with_iso_date_in_header(self):
        text = make_text("Report: Q1 Summary", "Date: 2026-01-15", "Body text here.")
        result = canonicalize(text, "q1.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "report")
        self.assertEqual(result["date"], "2026-01-15")

    def test_meeting_with_slash_date(self):
        text = make_text("Meeting: Sprint Kickoff", "05/20/2026", "Attendees: Alice")
        result = canonicalize(text, "sprint.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["date"], "2026-05-20")

    def test_canonical_name_format(self):
        text = make_text("Agenda: Quarterly Review", "2026-03-10")
        result = canonicalize(text, "agenda.docx", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertTrue(result["canonical_name"].endswith(".docx"))
        self.assertIn("agenda", result["canonical_name"])
        self.assertIn("2026-03-10", result["canonical_name"])

    def test_checklist_pass(self):
        text = make_text("Checklist: Onboarding", "2026-04-01", "Step 1: Do thing")
        result = canonicalize(text, "onboard.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "checklist")

    def test_minutes_pass(self):
        text = make_text("Minutes: Q4 Review", "2026-02-28", "Resolved: item A")
        result = canonicalize(text, "board.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "minutes")

    def test_sop_pass(self):
        text = make_text("SOP: Data Backup Procedure", "2026-05-01", "Step 1: ...")
        result = canonicalize(text, "backup.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "sop")


# ---------------------------------------------------------------------------
# Gate logic: WARN
# ---------------------------------------------------------------------------

class TestWarn(unittest.TestCase):

    def test_warn_when_date_missing(self):
        text = make_text("Report: Annual Summary", "No date here.", "Body.")
        result = canonicalize(text, "annual.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertIn("2026-06-11", result["failure_reason"])
        self.assertIsNone(result["reviewed_by"])
        self.assertIsNone(result["review_timestamp"])

    def test_warn_when_key_field_missing(self):
        # Heading is only the doc-type keyword with nothing else extractable
        text = make_text("Meeting", "2026-06-01")
        result = canonicalize(text, "sparse.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertIn("key_field", result["failure_reason"])

    def test_warn_ambiguous_doc_type(self):
        # "agenda" and "meeting" both present in first heading
        text = make_text("Meeting Agenda: Sprint 5", "2026-06-01")
        result = canonicalize(text, "sprint5.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertIn("Ambiguous", result["failure_reason"])
        self.assertIn("candidate_doc_types", result)

    def test_warn_includes_both_reasons_when_date_and_key_missing(self):
        text = make_text("Report")
        result = canonicalize(text, "r.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertIn("Date not found", result["failure_reason"])
        self.assertIn("key_field", result["failure_reason"])


# ---------------------------------------------------------------------------
# Gate logic: FAIL
# ---------------------------------------------------------------------------

class TestFail(unittest.TestCase):

    def test_fail_empty_input(self):
        result = canonicalize("", "empty.txt", today=TODAY)
        self.assertEqual(result["check_result"], "FAIL")
        self.assertIn("empty", result["failure_reason"].lower())

    def test_fail_whitespace_only(self):
        result = canonicalize("   \n\n\t  ", "blank.txt", today=TODAY)
        self.assertEqual(result["check_result"], "FAIL")

    def test_fail_unapproved_doc_type(self):
        text = make_text("Presentation: Q4 Results", "2026-06-01")
        result = canonicalize(text, "deck.txt", today=TODAY)
        self.assertEqual(result["check_result"], "FAIL")
        self.assertIn("approved list", result["failure_reason"])

    def test_fail_has_only_two_fields(self):
        result = canonicalize("", "x.txt", today=TODAY)
        self.assertEqual(set(result.keys()), {"check_result", "failure_reason"})


# ---------------------------------------------------------------------------
# Header-zone date constraint — body-date false-positive regression
# ---------------------------------------------------------------------------

class TestHeaderZoneDateConstraint(unittest.TestCase):
    """
    Regression suite for the header-zone fix.
    extract_date scans lines[:5] only (non-empty lines after stripping).
    A date appearing only in the body must NOT be picked up.
    """

    def test_date_on_line_6_triggers_warn(self):
        # Lines 1-5: heading + empty padding; date on effective line 6
        text = make_text(
            "Report: Infrastructure Audit",
            "Author: J. Smith",
            "Version: 1.0",
            "Classification: Internal",
            "Status: Draft",
            "2026-03-15",          # effective line 6 — must NOT be picked up
            "Body content starts here.",
        )
        result = canonicalize(text, "infra.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertIn("Today", result["failure_reason"])
        self.assertEqual(result["date"], TODAY.isoformat())

    def test_date_on_line_5_is_accepted(self):
        # Date lands exactly on effective line 5 — should still be picked up
        text = make_text(
            "Report: Infrastructure Audit",
            "Author: J. Smith",
            "Version: 1.0",
            "Classification: Internal",
            "2026-03-15",          # effective line 5 — must be picked up
            "Body content starts here.",
        )
        result = canonicalize(text, "infra.txt", today=TODAY)
        self.assertEqual(result["date"], "2026-03-15")

    def test_body_date_in_sop_system_prompt_does_not_become_document_date(self):
        """
        Regression: meeting_v0_5_prompt.txt embeds '(2026-06-11)' in Section 2 body.
        Before the fix, extract_date picked it up and returned PASS.
        After the fix, no header date → WARN with today as fallback.
        """
        text = (
            "# System Prompt: File Canonicalizer v0.5 — Meetings/Ops\n"
            "# Prompt Version: 0.5\n"
            "# Schema Version: 1.0\n"
            "# Core Profile: Processing Engine\n"
            "\n"
            "## 1. Classification Matrix\n"
            "You must evaluate the document content.\n"
            "\n"
            "## 2. Metadata Extraction Hierarchy\n"
            "- **Date Selection:** fallback order: ... System Date (2026-06-11).\n"
        )
        result = canonicalize(text, "meeting_v0_5_prompt.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertEqual(result["date"], TODAY.isoformat())
        self.assertIn("Today", result["failure_reason"])

    def test_blank_lines_do_not_inflate_header_zone(self):
        """
        Blank lines are stripped before indexing.
        A date after 4 blank lines + 1 heading lands on effective line 2, not line 6.
        """
        text = "Report: Quarterly\n\n\n\n\n2026-04-10\nBody"
        result = canonicalize(text, "q.txt", today=TODAY)
        # Effective lines: [1] "Report: Quarterly"  [2] "2026-04-10" — within zone
        self.assertEqual(result["date"], "2026-04-10")
        self.assertEqual(result["check_result"], "PASS")


# ---------------------------------------------------------------------------
# Priority classification: system prompt / config → sop
# ---------------------------------------------------------------------------

class TestPriorityClassification(unittest.TestCase):

    def test_system_prompt_heading_maps_to_sop(self):
        lines = ["# System Prompt: File Canonicalizer v0.5 — Meetings/Ops"]
        result = classify_doc_type(lines)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "sop")

    def test_prompt_version_header_maps_to_sop(self):
        lines = ["# Prompt Version: 1.2", "# Schema Version: 2.0"]
        result = classify_doc_type(lines)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "sop")

    def test_priority_overrides_co_match_with_meeting(self):
        """
        'System Prompt: ... Meetings/Ops' contains both 'system prompt' (→ sop priority)
        and 'meeting'. Priority rule must win; result must not be WARN/ambiguous.
        """
        lines = ["# System Prompt: File Canonicalizer v0.5 — Meetings/Ops"]
        result = classify_doc_type(lines)
        self.assertNotEqual(result["check_result"], "WARN")
        self.assertEqual(result["doc_type"], "sop")

    def test_priority_overrides_co_match_with_report(self):
        lines = ["# Core Profile: Monthly Report Processing Engine"]
        result = classify_doc_type(lines)
        self.assertEqual(result["doc_type"], "sop")

    def test_schema_version_header_maps_to_sop(self):
        lines = ["# Schema Version: 3.1"]
        result = classify_doc_type(lines)
        self.assertEqual(result["doc_type"], "sop")


# ---------------------------------------------------------------------------
# Date parsing variants
# ---------------------------------------------------------------------------

class TestDateParsing(unittest.TestCase):

    def test_iso_format(self):
        self.assertEqual(parse_date("Date: 2026-05-01"), "2026-05-01")

    def test_slash_format(self):
        self.assertEqual(parse_date("05/01/2026"), "2026-05-01")

    def test_day_month_year(self):
        self.assertEqual(parse_date("1 May 2026"), "2026-05-01")

    def test_month_day_year(self):
        self.assertEqual(parse_date("May 1, 2026"), "2026-05-01")

    def test_abbreviated_month(self):
        self.assertEqual(parse_date("Jan 15, 2026"), "2026-01-15")

    def test_no_date_returns_none(self):
        self.assertIsNone(parse_date("No dates here at all."))


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Slice plan alignment tests — names match implementation_slice_plan.md
# ---------------------------------------------------------------------------

class TestSlicePlanAlignment(unittest.TestCase):
    """Tests named to match the slice plan exactly for traceability."""

    # Slice 1
    def test_fail_empty_file(self):
        result = canonicalize("", "empty.txt", today=TODAY)
        self.assertEqual(result["check_result"], "FAIL")

    def test_fail_response_has_exactly_two_fields(self):
        result = canonicalize("", "x.txt", today=TODAY)
        self.assertEqual(set(result.keys()), {"check_result", "failure_reason"})

    # Slice 2
    def test_pass_meeting_with_clear_date(self):
        text = make_text("Meeting: Sprint Review", "2026-05-10", "Attendees: Alice")
        result = canonicalize(text, "sprint.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "meeting")
        self.assertEqual(result["date"], "2026-05-10")

    def test_classification_happy_path_meeting_heading(self):
        text = make_text("Meeting: Q2 Planning", "2026-04-01")
        result = canonicalize(text, "q2.txt", today=TODAY)
        self.assertEqual(result["doc_type"], "meeting")
        self.assertIn("Line 1", result["source_hint"]["doc_type"])

    def test_pass_doc_id_uses_underscore_separator(self):
        text = make_text("Report: Annual Summary", "2026-03-01")
        result = canonicalize(text, "annual.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        parts = result["doc_id"].split("_")
        self.assertGreaterEqual(len(parts), 3)

    # Slice 3
    def test_fail_has_no_manifest_key(self):
        text = make_text("Presentation: Q4 Results", "2026-06-01")
        result = canonicalize(text, "deck.txt", today=TODAY)
        self.assertEqual(result["check_result"], "FAIL")
        self.assertNotIn("doc_id", result)
        self.assertNotIn("doc_type", result)

    # Slice 4
    def test_ambiguous_meeting_report_returns_warn(self):
        text = make_text("Meeting Report: Q3 Review", "2026-06-01")
        result = canonicalize(text, "q3.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")

    def test_ambiguous_warn_failure_reason_mentions_both_types(self):
        text = make_text("Meeting Report: Q3 Review", "2026-06-01")
        result = canonicalize(text, "q3.txt", today=TODAY)
        self.assertIn("meeting", result["failure_reason"].lower())
        self.assertIn("report", result["failure_reason"].lower())

    # Slice 5
    def test_pass_report_with_prose_date(self):
        text = make_text("Report: Q1 Summary", "March 15, 2026", "Body text.")
        result = canonicalize(text, "q1.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["date"], "2026-03-15")

    def test_warn_missing_date_uses_today_as_fallback(self):
        text = make_text("Report: Undated Summary", "No date here.")
        result = canonicalize(text, "undated.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertEqual(result["date"], TODAY.isoformat())

    # Slice 6
    def test_short_agenda_key_field_is_not_a_date(self):
        text = make_text("Agenda: Board Meeting", "2026-06-01", "Item 1: Budget")
        result = canonicalize(text, "board.txt", today=TODAY)
        if result["check_result"] == "PASS":
            self.assertIsNone(parse_date(result["key_field"]))

    # Slice 7
    def test_pass_manifest_has_exactly_five_fields(self):
        text = make_text("Report: Quarterly Summary", "2026-04-01", "Body.")
        result = canonicalize(text, "q.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        required = {"doc_id", "doc_type", "date", "key_field", "canonical_name"}
        for field in required:
            self.assertIn(field, result)

    def test_pass_check_result_in_manifest(self):
        text = make_text("Report: Annual Review", "2026-01-15", "Body.")
        result = canonicalize(text, "annual.txt", today=TODAY)
        self.assertIn("check_result", result)
        self.assertEqual(result["check_result"], "PASS")

    def test_pass_has_canonical_name(self):
        text = make_text("Report: Year End", "2026-12-01", "Body.")
        result = canonicalize(text, "yearend.txt", today=TODAY)
        self.assertEqual(result["check_result"], "PASS")
        self.assertIn("canonical_name", result)
        self.assertTrue(result["canonical_name"].endswith(".txt"))

    def test_determinism_three_runs(self):
        text = make_text("Report: Determinism Test", "2026-06-01", "Body.")
        r1 = canonicalize(text, "det.txt", today=TODAY)
        r2 = canonicalize(text, "det.txt", today=TODAY)
        r3 = canonicalize(text, "det.txt", today=TODAY)
        self.assertEqual(r1["canonical_name"], r2["canonical_name"])
        self.assertEqual(r2["canonical_name"], r3["canonical_name"])
        self.assertEqual(r1["doc_id"], r3["doc_id"])

    # Slice 8
    def test_warn_reviewed_by_is_null_initially(self):
        text = make_text("Report: No Date", "Body only.")
        result = canonicalize(text, "nodate.txt", today=TODAY)
        self.assertEqual(result["check_result"], "WARN")
        self.assertIsNone(result["reviewed_by"])
        self.assertIsNone(result["review_timestamp"])

    def test_warn_resolution_trail_field_format(self):
        text = make_text("Report: No Date", "Body only.")
        result = canonicalize(text, "nodate.txt", today=TODAY)
        self.assertIn("reviewed_by", result)
        self.assertIn("review_timestamp", result)
        self.assertIn("failure_reason", result)
        self.assertIsNotNone(result["failure_reason"])
