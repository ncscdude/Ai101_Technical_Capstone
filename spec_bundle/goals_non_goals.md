# Goals and Non-Goals - File Canonicalizer v0.5

## Goals
| ID | Goal |
|----|------|
| G-01 | Classify each file as one of six approved doc types |
| G-02 | Extract date and normalize to ISO format |
| G-03 | Extract one key field from first heading |
| G-04 | Produce canonical filename YYYY-MM-DD_doc_type_key-field.ext |
| G-05 | Return PASS WARN or FAIL on every run |
| G-06 | Require human review for ambiguous records |
| G-07 | Deterministic output - same input same output every run |
| G-08 | Support PDF DOCX TXT via web interface |

## Non-Goals v0.5
| ID | Out of Scope |
|----|-------------|
| NG-01 | Moving renaming or modifying files on disk |
| NG-02 | Processing more than one file per run |
| NG-03 | Searchable index or recall interface |
| NG-04 | Redacting or anonymizing content |
| NG-05 | External storage integrations |
| NG-06 | OCR for scanned PDFs |
| NG-07 | Types outside the six approved |
| NG-08 | Input sanitization |

## Success Criteria
- Same input produces same canonical filename on every run
- Manifest contains all four fields with source citations
- Missing date or unrecognized type returns WARN or FAIL
- Reviewer can verify output in under 60 seconds
- PASS WARN FAIL all demonstrated in test run
