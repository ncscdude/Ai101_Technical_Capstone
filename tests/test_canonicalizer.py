from datetime import date
import unittest

from canonicalizer import canonicalize


TODAY = date(2026, 6, 9)


class CanonicalizerTests(unittest.TestCase):
    def test_pass_meeting(self):
        text = """Q2 Budget Review Meeting
Date: 2026-06-09
Attendees: R. McMillan, J. Smith
"""
        result = canonicalize(text, "Q2_Budget_Review_Notes.docx", TODAY)

        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "meeting")
        self.assertEqual(result["date"], "2026-06-09")
        self.assertTrue(result["canonical_name"].endswith(".docx"))
        self.assertIn("check_result", result)
        self.assertEqual(set(result["source_hint"]), {"doc_type", "date", "key_field"})

    def test_pass_sop(self):
        text = """Standard Operating Procedure: Onboarding New Vendors
Effective Date: 2026-05-01
Step 1: Collect vendor documentation.
"""
        result = canonicalize(text, "Onboarding_SOP.docx", TODAY)

        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "sop")
        self.assertEqual(result["date"], "2026-05-01")

    def test_pass_report_prose_date_normalized(self):
        text = """Q1 2026 Quarterly Report
Date: 15 March 2026
Prepared by: Finance Team
"""
        result = canonicalize(text, "Q1_Report.docx", TODAY)

        self.assertEqual(result["check_result"], "PASS")
        self.assertEqual(result["doc_type"], "report")
        self.assertEqual(result["date"], "2026-03-15")
        self.assertTrue(result["doc_id"].startswith("report_2026-03-15_"))

    def test_warn_missing_date_uses_today(self):
        text = """Weekly Team Meeting Notes
Attendees: Alice, Bob, Carol
Action items: update backlog.
"""
        result = canonicalize(text, "Team_Meeting.docx", TODAY)

        self.assertEqual(result["check_result"], "WARN")
        self.assertEqual(result["date"], "2026-06-09")
        self.assertIsNone(result["reviewed_by"])
        self.assertIsNone(result["review_timestamp"])

    def test_warn_ambiguous_type_blocks_extraction(self):
        text = """Meeting Summary - Q2 Report
Date: 2026-04-10
This document summarizes the Q2 planning session.
"""
        result = canonicalize(text, "Mixed.docx", TODAY)

        self.assertEqual(result["check_result"], "WARN")
        self.assertEqual(set(result["candidate_doc_types"]), {"meeting", "report"})
        self.assertNotIn("doc_id", result)

    def test_warn_date_only_agenda_does_not_use_date_as_key_field(self):
        text = """Agenda
2026-06-01
"""
        result = canonicalize(text, "Agenda.docx", TODAY)

        self.assertEqual(result["check_result"], "WARN")
        self.assertEqual(result["key_field"], "UNKNOWN")

    def test_fail_empty_file(self):
        result = canonicalize("", "empty.docx", TODAY)

        self.assertEqual(result["check_result"], "FAIL")
        self.assertEqual(set(result), {"check_result", "failure_reason"})

    def test_fail_unsupported_type(self):
        text = """Q2 Sales Presentation
Date: 2026-06-09
Slide 1: Revenue Overview
"""
        result = canonicalize(text, "Slides.pptx", TODAY)

        self.assertEqual(result["check_result"], "FAIL")
        self.assertNotIn("doc_id", result)
        self.assertNotIn("canonical_name", result)

    def test_determinism_three_runs(self):
        text = """Q2 Budget Review Meeting
Date: 2026-06-09
Attendees: R. McMillan, J. Smith
"""
        results = [canonicalize(text, "Q2_Budget_Review_Notes.docx", TODAY) for _ in range(3)]

        self.assertEqual(len({result["doc_id"] for result in results}), 1)
        self.assertEqual(len({result["check_result"] for result in results}), 1)


if __name__ == "__main__":
    unittest.main()

