# Requirements — File Canonicalizer v0.5 (Meetings/Ops)
## EARS Format

**Version:** 0.5  
**Project:** File Canonicalizer  
**Owner:** Robert McMillan  
**Last updated:** 2026-06-09  

---

## EARS Pattern Reference (Applied to This Workflow)

| Sentence Pattern | Canonicalizer Example | Behavior Type in Workflow |
|---|---|---|
| **Normal Behavior** | The system shall include schema_version, generator_version, and prompt_version in every manifest it produces. | Always-on behavior — applies to every run regardless of input. |
| **Event-Driven** | When a file is submitted for canonicalization, the system shall classify its doc_type against the six approved values before any extraction step. | Triggered action — starts when a file enters the pipeline. |
| **State-Driven** | While a manifest has check_result = WARN, the system shall keep reviewed_by and review_timestamp null until a human reviewer resolves the issue. | Conditional behavior — active while the manifest is in a WARN state. |
| **Unwanted Behavior** | If a file is unreadable or its doc_type is not in the approved list, the system shall return FAIL and shall log failure_reason stating the cause. | Error handling and safety — prevents invalid or unsafe ingestion. |
| **Optional** | Where the extraction agent returns a confidence value, the system shall record it in the manifest as informational only and shall not use it as a gate condition. | Configurable feature — behavior present only when the agent supports it. |

---

## Normal Behavior
*The [system] shall [behavior] — always-on, no trigger needed*

**REQ-01**  
The system shall include schema_version, generator_version, and prompt_version in every manifest it produces.

**REQ-02**  
The system shall record a source_hint for every extracted field referencing the page or line in the source document.

**REQ-03**  
The system shall produce canonical filenames in the format YYYY-MM-DD_doc_type_key-field.ext.

**REQ-04**  
The system shall store a complete manifest record for every file that returns check_result PASS.

---

## Event-Driven
*When [event], the [system] shall [behavior] — triggered actions*

**REQ-05**  
When a file is submitted for canonicalization, the system shall classify its doc_type against the six approved values before any extraction step.

**REQ-06**  
When all required fields are extracted with source citations, the system shall return check_result PASS and shall log the run to run_log.csv.

**REQ-07**  
When one required field is missing or ambiguous but the file is otherwise processable, the system shall return check_result WARN, shall populate failure_reason with the specific field and issue, and shall log the run to run_log.csv.

**REQ-08**  
When the document date cannot be found in the file content, the system shall check for an effective date, and when neither is present the system shall use today's date and shall set date_source to assumed.

**REQ-09**  
When a WARN manifest is resolved by a reviewer, the system shall require reviewed_by and review_timestamp to be set before check_result is updated to PASS.

**REQ-10**  
When a file is submitted and the prompt_version recorded in the manifest does not match the current prompt file version, the system shall flag the run as a version mismatch in the run log before processing continues.

---

## State-Driven
*While [state], the [system] shall [behavior] — conditional behaviors*

**REQ-11**  
While a manifest has check_result = WARN, the system shall keep reviewed_by and review_timestamp null until a human reviewer resolves the issue.

**REQ-12**  
While the LLM API is unavailable or returns no response within [NEEDS CLARIFICATION: acceptable timeout — 10 seconds? 30 seconds?], the system shall return check_result FAIL and shall log the outage with timestamp and error reason.

**REQ-13**  
While temperature is not set to zero on a Claude LLM run, the system shall block the run and shall return a configuration error before processing any file.

---

## Unwanted Behavior
*If [condition], the [system] shall [action] and shall [audit action] — error handling, safety*

**REQ-14**  
If a file is unreadable or its doc_type is not in the approved list, the system shall return check_result FAIL and shall log failure_reason stating the cause. No manifest shall be produced.

**REQ-15**  
If a required field cannot be determined from the source document, the system shall set that field to null and shall set check_result to WARN with failure_reason naming the specific missing field.

**REQ-16**  
If a file exceeds [NEEDS CLARIFICATION: maximum file size for v0.5 — 50 pages? 100 pages? token limit?], the system shall return check_result FAIL and shall log the rejection with failure_reason stating the file exceeds the size limit.

**REQ-17**  
If the key field cannot be found in the first heading or subject line, the system shall search [NEEDS CLARIFICATION: first paragraph only? first 500 words? entire document?] before setting key_field to null and returning check_result WARN.

**REQ-18**  
If the schema_version in a manifest does not equal 1.0, the system shall flag the manifest as invalid and shall prevent sign-off until the version mismatch is resolved.

**REQ-19**  
If a WARN or FAIL file is submitted for ingestion without a human reviewer signature, the system shall reject the ingestion and shall log an error stating that reviewed_by and review_timestamp are required.

---

## Optional
*Where [feature], the [system] shall [behavior] — configurable features*

**REQ-20**  
Where the extraction agent returns a confidence value, the system shall record it in the manifest as informational only and shall not use it as a gate condition.

**REQ-21**  
Where a source_hint cannot be determined to a specific page, the system shall record the nearest available reference such as section title or document position.

---

## Feature Spec Worksheet — Two EARS Examples

These two requirements map directly to the Feature Spec Worksheet goals and unwanted behaviors.

**From Goal 1 (deterministic filename):**

Event-Driven  
When a text-readable Meetings/Ops file is submitted, the system shall produce a canonical filename in the format YYYY-MM-DD_doc_type_key-field.ext and shall return a four-field manifest within one processing turn.

**From Non-Goal 3 (no search interface) and Non-Goal 2 (no batch processing):**

Unwanted Behavior  
If a request is made to process more than one file in a single run, the system shall reject the request and shall return an error stating that v0.5 supports one file per run only.

Unwanted Behavior  
If a request is made to query, search, or retrieve previously filed manifests, the system shall return an error stating that recall and search are out of scope for v0.5.

---

## Open Clarifications (search [NEEDS CLARIFICATION] to find all)

| Req | Question | Owner |
|---|---|---|
| REQ-12 | Acceptable LLM timeout threshold | Robert McMillan |
| REQ-16 | Maximum file size for v0.5 | Robert McMillan |
| REQ-17 | Key field search depth beyond first heading | Robert McMillan |
