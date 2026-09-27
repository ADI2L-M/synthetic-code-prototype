# Detector validation

This folder contains the validation artefacts for the 18 research AST
detectors. The validation has two separate layers:

1. Controlled fixtures verify that each detector recognises a known positive
   case and rejects a known negative or boundary case.
2. Manual labels from authentic submissions estimate precision, recall, and F1
   against human-reviewed ground truth.

## Current criteria

These are project acceptance criteria for the pilot, not universal standards:

| Measure | Target |
|---|---:|
| Controlled fixture accuracy | 100% |
| Precision | 0.90 or higher |
| Recall | 0.85 or higher |
| F1 | 0.87 or higher |
| Reviewed positive examples | At least 20 where available |
| Reviewed negative examples | At least 20 where available |

The readiness status is reported per detector:

- `validated`: metric targets and minimum review counts are met.
- `pilot_validated`: metric targets are met, but more examples are needed.
- `preliminary`: one or more metric targets are not met.
- `pending`: no manual labels have been recorded.

## Run controlled validation

From the project root:

```text
.venv\\Scripts\\python.exe scripts/validate_detectors.py --mode controlled
```

This writes `controlled-fixture-report.json`. It checks both a positive and a
negative case for every registered detector. The fixture report is an
engineering check; it is not a substitute for authentic-submission review.

## Manual validation workflow

### Create the authentic review sample

From the project root, run:

```text
.venv\\Scripts\\python.exe scripts/validate_detectors.py --mode authentic
```

This reads `research-notes/data-identification/cs1_labs_responses.xlsx`, runs
all 18 detectors, and writes:

- `authentic-detector-review.jsonl`: selected cases containing source code,
  detector labels, detector evidence, and blank `manual_label` fields;
- `authentic-detector-review.meta.json`: counts, sampling information, and
  skipped parse failures.

The default sample contains up to 40 detector-positive and 40
detector-negative cases per defect. Sampling is deterministic. Use
`--per-class 0` to export every task-eligible parseable case, or provide a
different `--seed` to create a different reproducible sample.

The runner excludes defects marked `not_applicable` or
`instruction_confounded` by default. Add `--include-noneligible` only when
you explicitly need those cases for a separate detector audit.

Before annotating, make a copy so a later sample regeneration does not erase
your labels:

```text
Copy-Item research-notes\\detector-validation\\authentic-detector-review.jsonl research-notes\\detector-validation\\authentic-detector-gold-labels.jsonl
```

### Complete the manual labels

Review the source code in `authentic-detector-gold-labels.jsonl` and set:

- `manual_label: 1` when the defect is genuinely present;
- `manual_label: 0` when the defect is absent;
- `manual_label: "uncertain"` while reviewing; uncertain rows are excluded.

Do not replace `manual_label` with `detector_label`; the two values must remain
independent for precision and recall to be meaningful.

Then run:

```text
.venv\\Scripts\\python.exe scripts/validate_detectors.py --mode manual --labels research-notes\\detector-validation\\authentic-detector-gold-labels.jsonl
```

The result is written to `manual-validation-report.json` unless `--output` is
provided.
