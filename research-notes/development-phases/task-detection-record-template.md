# Authentic task detection record

Create one completed record for every authentic Lab/Question task before
family-level prevalence is reported.

## Task identity

- Authentic task: `Lab __ Q__`
- Mapping type: `direct` / `supporting`
- Prototype task: `T__`
- Task family: `conditional_logic` / `list_processing` / `numeric_iteration`
- Source workbook and response column: `cs1_labs_responses.xlsx`, `Response __`
- Right-answer column used for functional testing: `Right answer __`
- Functional-test contract: `functional-tests/authentic_test_cases.json`

## Functional filtering

- Raw submission count:
- Functionally correct count:
- Functionally incorrect count:
- Constraint-compliance rule:
- Exclusion reasons and counts:
- Validation output reference:

Only functionally correct and constraint-compliant submissions enter prevalence
denominators.

## Defect-detection evidence

For every defect relevant to the mapped prototype task, record one row:

| Defect | Raw detected submissions | Eligibility | Eligible denominator | Affected eligible submissions | Task prevalence | Detector evidence/output |
|---|---:|---|---:|---:|---:|---|
| `defect_id` |  | eligible / not_applicable / instruction_confounded |  |  |  |  |

Raw detection must be retained even when eligibility is not applicable or
instruction-confounded. Prevalence uses binary presence per submission, not
the number of defect instances.

## Detector validation notes

- Detector implementation:
- Definition file:
- Unit-test reference:
- Manual validation sample:
- Known false-positive risks:
- Known false-negative risks:
- Unresolved ambiguity:

## Task-level conclusion

- Eligible defects with prevalence:
- Defects excluded from prevalence and why:
- Submission-level output:
- Review status:
