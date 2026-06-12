# Pairing Checklist - File Canonicalizer v0.5

## 3 Rules of TDD with AI
1. Write the test before asking AI for anything - the test is the spec
2. Read before you accept - AI makes choices inside the boundaries your test allows
3. Do not do more than asked - if AI adds something you did not specify that is a judgment call not a gift

## Phase 1 Checklist - Human Writes Tests AI Implements
- [ ] Write the failing test first - no exceptions
- [ ] Read every line of AI output before accepting
- [ ] Check: does the implementation add anything the test did not specify
- [ ] Verify imports are real and module is on pythonpath
- [ ] Run tests green before moving to next behavior
- [ ] Refactor only on green

## Phase 1 Results
| Behavior | Test Names | AI Added Unexpectedly |
|----------|-----------|----------------------|
| Document type classification | test_pass_meeting_with_clear_date test_classification_happy_path | Confidence score field - accepted as informational only per ADR-03 |
| Manifest check_result field | test_pass_check_result_in_manifest | check_result placed outside manifest as envelope field - rejected |
| WARN resolution fields | test_warn_reviewed_by_is_null_initially | Proposed updating existing run log row - rejected append-only required |

## Phase 2 Checklist - AI Proposes Human Evaluates
- [ ] Write down design decision instinct BEFORE asking AI
- [ ] Let AI propose both tests and implementations
- [ ] Evaluate each proposal before accepting
- [ ] Ask: does this refactor serve today code or tomorrow code
- [ ] Categorize AI suggestions: in scope premature or real gap

## Phase 2 Results
| Task | AI Proposed | Changed or Rejected | Why |
|------|------------|---------------------|-----|
| Gate condition | Confidence threshold PASS if score 0.7 or above | Rejected per ADR-03 | Non-deterministic across agents |
| Date extraction | Full document scan | Changed to lines 1-5 only | Body-text false positives |
| WARN reviewer fields | Auto-populate with system timestamp | Rejected | Bypasses accountability gate |

## AI Coding Guardrails
| Category | Rule |
|----------|------|
| Quality | Tests are contracts - if test is correct and passes implementation is correct |
| Security | Check for hardcoded secrets and injection vectors in every AI output |
| Licensing | Flag any external dependency |
| Scope | Every behavior must trace to a spec scenario. Do not do more than asked. |
