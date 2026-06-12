# Feature Spec Worksheet - File Canonicalizer v0.5

## Project Selection
| Field | Answer |
|-------|--------|
| Project name | File Canonicalizer |
| Problem statement | Files arrive with inconsistent names and no structured metadata making them impossible to audit |
| Software capability | Reads one file classifies type extracts date and key field produces canonical filename and manifest |
| Canonical filename | YYYY-MM-DD_doc_type_key-field.ext |
| Manifest fields | doc_id doc_type date key_field check_result |
| Technical track | Track B LLM integrated |
| API access | Claude Sonnet 4.6 via claude.ai Projects |

## Goals
| Field | Answer |
|-------|--------|
| Goal 1 | Same input produces same canonical filename on three consecutive runs with zero variation |
| Goal 2 | All PASS files produce correct manifest. All WARN files resolvable in under 60 seconds. |
| Non-goal 1 | Do not move rename or modify any file on disk |
| Non-goal 2 | Do not process more than one file per run in v0.5 |
| Non-goal 3 | Do not build a search or recall interface |
| Constraint 1 | All processing local. No sensitive content sent to unapproved tools. |
| Constraint 2 | Manifest schema locked at version 1.0 for v0.5 |
| Assumption 1 | All files have a readable text layer |
| If wrong | Return FAIL - manual OCR required |
| Assumption 2 | Every file maps to one of the six approved types |
| If wrong | Return FAIL - expand approved list via schema change PR |

## AI Stress-Test Findings
| Gap | Fix |
|-----|-----|
| WARN vs FAIL boundary undefined | Locked WARN to recoverable fields FAIL to unreadable or unapproved |
| Key field extraction rule undefined | Locked extraction rule for all six types |
| No rule for conflicting dates | Locked order: document date then effective date then today |
| Body-text dates picked up as document dates | Limited extraction to header zone lines 1-5 |

## Definition of Done
- [x] Project selected
- [x] One software capability identified
- [x] Success criteria defined
- [x] Out-of-scope items defined
- [x] Technical track selected
- [x] Team roles assigned
- [x] Team can explain feature in one sentence
