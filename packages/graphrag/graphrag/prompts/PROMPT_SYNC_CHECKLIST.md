# Prompt Sync Checklist (index <-> prompt_tune)

Use this checklist whenever updating extraction or summarization prompts.

## 1) Scope sync
- [ ] `prompts/index/*` changes are mirrored in `prompt_tune/template/*` where equivalent prompts exist.

## 2) Summary policy sync
- [ ] Latest-first conflict handling rules are consistent.
- [ ] Facts vs Inferences wording is consistent.
- [ ] Required section names are consistent.
- [ ] Compact slot templates are consistent.

## 3) Extraction policy sync
- [ ] Temporal/status/change guidance is consistent.
- [ ] Tag/field-required behavior is consistent when information is present.
- [ ] JSON variant field names align with non-JSON guidance.

## 4) Validation
- [ ] Run prompt contract checks for required keywords/sections.
- [ ] Confirm no unintended format breakage in output delimiters and completion tokens.
