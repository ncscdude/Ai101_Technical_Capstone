# AI101 Technical Capstone - File Canonicalizer v0.5

This project is a small, deterministic MVP for the AI101 technical capstone.
It accepts extracted text from one file, classifies the document type, extracts
basic fields, and returns a canonical record or a failure response.

## What The MVP Does

- Processes one text-readable file per run.
- Classifies the file as one of six approved document types:
  `meeting`, `agenda`, `minutes`, `sop`, `checklist`, `report`.
- Extracts a date and normalizes it to ISO format.
- Extracts a key identifying field from the heading.
- Builds a canonical filename proposal.
- Returns `PASS`, `WARN`, or `FAIL`.
- Keeps human review gates explicit for ambiguous or inferred data.

It does not rename, move, upload, index, OCR, or modify files.

## Quick Start

Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

Run the CLI with a text file:

```powershell
python canonicalizer.py --text-file samples/pass_report.txt --filename Q1_Report.docx
```

Generate verification evidence:

```powershell
python scripts/generate_evidence.py
```

The evidence file is written to `evidence/test_results.txt`.

## Output Shapes

PASS and WARN return a canonical record with `check_result` inside the record.
This keeps each accepted or review-held record audit-ready by itself.

FAIL returns a separate failure response object only:

```json
{
  "check_result": "FAIL",
  "failure_reason": "File is empty. No content to classify or extract."
}
```

## Capstone Status

| Requirement | Status |
|---|---|
| Spec bundle | Documented in `docs/` |
| Implemented feature | `canonicalizer.py` |
| Test package | `tests/test_canonicalizer.py` |
| Verification evidence | `evidence/test_results.txt` |
| Review package | Ready for peer/AI review |
| Final presentation | Separate class deliverable |

