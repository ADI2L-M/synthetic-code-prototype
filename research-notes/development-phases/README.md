# Authentic defect-detection development

This folder is the navigation point for analysing authentic student Python
submissions and producing empirical defect-prevalence profiles for synthetic
code generation.

The implementation follows `detection-flow.md`. The four analytical concerns
remain separate throughout the workflow:

1. Functional filtering: determine whether a submission satisfies the task.
2. Raw detection: determine whether the source contains a defined defect.
3. Task eligibility: determine whether that defect is a valid opportunity for
   the mapped prototype task.
4. Prevalence: aggregate one binary observation per submission and task.

## Quick navigation

| Phase | Purpose | Primary project locations | Main output |
|---|---|---|---|
| 0. Inputs and mapping | Connect authentic Lab/Question pairs to T1, T2, or T3 | `data-identification/`, `task-def-yaml/`, `data-identification/cs1_regeneration_task_groups.json` | Reproducible task map |
| 1. Defect definitions | Read and formalise each authoritative defect rule | `defect_definitions_yaml/`, `programming-defects.md` | Machine-oriented defect specification |
| 2. Detector architecture | Implement one detector per defect using AST/token analysis | `detectors/`, `config/defect_specifications.json` | Raw `DetectionResult` records |
| 3. Eligibility | Classify each task-defect pair as eligible, not applicable, or instruction-confounded | `services/eligibility.py`, `config/defect_specifications.json` | Eligibility matrix |
| 4. Detector tests | Verify positive, negative, boundary, and false-positive cases | `tests/unit/detectors/` | Detector unit-test results |
| 5. Functional filtering | Retain only functionally correct and constraint-compliant submissions | `services/validator.py`, `services/authentic_functional_validation.py`, `functional-tests/authentic_test_cases.json`, `tests/unit/services/` | Valid-submission set |
| 6. Authentic analysis | Combine ingestion, parsing, functional status, raw detection, and eligibility | `services/authentic_ingestion.py`, `services/research_pipeline.py` | One record per submission |
| 7. Prevalence | Calculate task prevalence, then family mean and pooled prevalence | `services/prevalence.py` | Task and family prevalence tables |
| 8. Validation and export | Report detector validation and export empirical target profiles | `services/validation_metrics.py`, `outputs/` | Reproducible research outputs |

Each authentic Lab/Question task must have an individual detection record
based on [task-detection-record-template.md](task-detection-record-template.md)
before task-family prevalence is calculated.

## Data-flow rule

```text
Excel submissions
    -> Lab/Question-to-prototype mapping
    -> functional and constraint filtering
    -> raw defect detection
    -> task-defect eligibility
    -> task-level prevalence
    -> task-family mean and pooled prevalence
    -> empirical target profile
```

The `Right answer n` column is used to construct or validate functional test
oracles. It is not used for source-code comparison or defect detection.

Functional contracts are stored in
`functional-tests/authentic_test_cases.json` and executed by
`services/authentic_functional_validation.py`. The isolated runner supports
function submissions, interactive scripts, file-backed functions, and
structured answer values.

## Prevalence rule

For each authentic Lab/Question task `q` and defect `d`:

```text
p(q, d) = affected valid eligible submissions / valid eligible submissions
```

For each prototype task family, the primary estimate is the arithmetic mean of
the available task-level prevalences. Pooled prevalence is retained as a
secondary statistic. A not-applicable or instruction-confounded combination is
not converted into a zero observation.

## Prototype-task coverage

The task grouping currently defines:

- T1 Conditional Logic: 20 authentic Lab/Question tasks
- T2 List Processing: 19 authentic Lab/Question tasks
- T3 Numeric Iteration: 7 authentic Lab/Question tasks

The authoritative task-family definitions are in `task-def-yaml/`. The
authentic task mapping is in
`data-identification/cs1_regeneration_task_groups.json`.

## Per-defect navigation convention

For every detector, keep the following trail together:

1. authoritative YAML definition;
2. machine-oriented specification entry;
3. detector implementation;
4. positive/negative/boundary tests;
5. manual validation labels and metrics, where available;
6. prevalence output.

This prevents a detector implementation from silently changing the research
definition or mixing raw detection with task eligibility.
