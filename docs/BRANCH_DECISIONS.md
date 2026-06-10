# Branch Decisions

This package is a clean branch from the earlier Copilot workflow. The earlier
package treated `check_result` as an envelope field and allowed evidence to drift
from the runnable code. This branch makes the implementation, tests, and evidence
agree.

## Schema Decision

PASS and WARN return one canonical record. The record includes:

- `doc_id`
- `doc_type`
- `date`
- `key_field`
- `canonical_name`
- `check_result`
- `source_hint`
- `extraction_snippet`

WARN records also include:

- `failure_reason`
- `reviewed_by`
- `review_timestamp`

FAIL is not a canonical record. It returns only:

- `check_result`
- `failure_reason`

## Why `check_result` Is Inside PASS/WARN

The capstone values auditability and review readiness. A reviewer should be able
to inspect one canonical record and know whether the record is accepted, blocked,
or waiting for review. Keeping `check_result` inside PASS/WARN records supports
that goal.

## Fixed Branch Issues

- Prose dates such as `15 March 2026` normalize to `2026-03-15`.
- `doc_id` uses the normalized ISO date.
- Ambiguous headings such as `Meeting Summary - Q2 Report` return WARN and block extraction.
- A date-only agenda does not use the date as `key_field`; it returns WARN.
- Verification evidence is generated from the runnable code.

