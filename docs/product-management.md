# Product management

## Product objective

Provide a traceable local research tool for generating, validating, detecting,
comparing, and exporting synthetic novice-code batches against authentic CS1
defect profiles.

## In scope

- T1 conditional logic, T2 list processing, and T3 numeric iteration.
- Local Ollama generation with configurable model, temperature, batch size,
  tolerance, repair budget, and calibration iterations.
- Functional correctness filtering.
- Reusable AST/token detector evaluation.
- Profile comparison and iterative calibration.
- Local SQLite persistence and portable experiment exports.
- Streamlit inspection of tasks, prompts, submissions, iterations, analytics,
  experiment history, runtime provenance, and run lifecycle status.

## Out of scope for the prototype

- Multi-user access control.
- Cloud model orchestration.
- Parallel experiment scheduling.
- Production-grade hostile-code sandboxing.
- Claims that synthetic data is statistically equivalent to authentic data.

## Core user journeys

### Generate a benchmark batch

1. Select a prototype task and local model.
2. Set temperature, batch size, tolerance, and connection settings.
3. Generate and monitor the batch.
4. Inspect functional results, prompts, source, and detector outputs.
5. Calibrate when the profile is outside the decision margin.
6. Export the retained iteration and calibration lineage.

### Run a controlled experiment

1. Select task, model, batch size, temperature, repetitions, and conditions.
2. Run baseline, task-aware non-adaptive, and task-aware iterative conditions.
3. Compare functional validity, coverage, MAE, RMSE, and tolerance outcomes.
4. Preserve the experiment ID, configuration, provenance, and selected
   iterations.

The Experiments page provides the product-management view for this journey. It
keeps controlled JSONL comparisons separate from interactive SQLite runs while
making both inspectable and exportable from the application.

### Audit authentic evidence

1. Browse mapped Lab/Question tasks.
2. Inspect functional eligibility and detector evidence.
3. Review task-level prevalence.
4. Inspect the equal-task-weighted prototype profile.

## Run lifecycle

```text
draft -> running -> completed
             |-> cancelling -> cancelled
             |-> failed
```

Every transition should retain the run identifier and timestamps. A cancelled
run keeps completed iterations and submissions; an invalid submission remains
visible but is excluded from the prevalence denominator.

## Release gates

### R0: Research-safe baseline

- Latest benchmark logs are preserved.
- Baseline retries are task-only.
- Experiment configuration and seeds are recorded.
- `pytest`, Ruff, and diff checks pass.

### R1: Evaluation-ready prototype

- SQLite records run status and provenance.
- Runtime configuration has one source of truth.
- Legacy imports are removed or explicitly marked deprecated.
- Experiment history is browsable and exportable.

### R2: Extended evaluation

- Repeated runs across models and batch sizes.
- Detector validation evidence reconciled with target-profile metadata.
- Environment and model digests recorded.
- Uncertainty summaries and primary metrics pre-specified.

## Definition of done for a change

- The change has a clear product or research purpose.
- The owning module and data source are identified.
- Unit, integration, or AppTest coverage is added when behaviour changes.
- Existing experiment results are not silently overwritten.
- The report and user-facing labels match the implementation.
- The change passes the project verification commands.
