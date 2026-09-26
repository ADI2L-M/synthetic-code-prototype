# Service-module navigation

The service layer is grouped by workflow responsibility. The old top-level
service files are compatibility facades; new code should import from the
functional subpackages below.

## Authentic-data preparation

- `authentic/ingestion.py` — read and normalize workbook submissions.
- `authentic/functional_validation.py` — load right-answer-derived test plans
  and classify a submission as pass/fail.
- `authentic/validation_runner.py` — execute isolated submission/reference
  calls with captured output and controlled input.
- `authentic/filter.py` — batch functional validation and write the complete
  and functionally-correct CSV outputs.
- `authentic/pilot_task.py` — Lab 12 Q2 pilot contract.

## Research analysis

- `research/eligibility.py` — determine whether a submission is eligible for a
  defect
  estimate.
- `research/prevalence.py` — calculate task-level and family-level prevalence.
- `research/validation_metrics.py` — detector validation metrics.
- `research/pipeline.py` — research detector orchestration.

## Prototype-generation workflow

- `generation/workflow.py`, `generation/analysis.py`,
  `generation/calibrator.py`, `generation/validator.py` — generation,
  validation, analysis, and calibration workflow.
- `generation/validation_runner.py`, `generation/prompt_builder.py` — isolated
  execution and generation specification support.
- `data/loader.py`, `data/profile_composer.py` — application data and profile
  support.
- `providers/demo.py`, `providers/llm.py`, `providers/ollama.py` — generation
  provider implementations.

The intended order for the authentic-data study is:

`authentic.ingestion` → `authentic.functional_validation` → detector registry
→ `research.eligibility` / `research.prevalence`.
