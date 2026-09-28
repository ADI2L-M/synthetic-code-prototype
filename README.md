# Synthetic Novice Code Research Prototype

A Streamlit research dashboard for inspecting empirically estimated programming
defect prevalence from authentic, functionally correct CS1 submissions. The
current UI is organised around prototype tasks T1, T2, and T3 and their mapped
authentic Lab/Question reports.

## Run the application

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

## Verify the project

```powershell
python -m pytest -q
ruff check . --exclude .agents --exclude .claude --exclude .venv
```

## Architecture

```text
app.py                         Thin Streamlit entry point
app_pages/                     Home, Generation, and Defect detection pages
ui/                            Streamlit presentation modules
  home.py                      Application landing view
  generation.py                Generation controls, tabs, and results
  research_dashboard.py        Empirical prevalence and report navigation
models/                        Shared domain and research data structures
detectors/
  core/                        AST parsing and detector registry
  legacy/                      Demonstration heuristics
  research/                    Definition-driven research detectors
services/
  authentic/                   Workbook ingestion and functional filtering
  research/                    Eligibility, detection orchestration, prevalence
  generation/                  Generation, validation, comparison, calibration
  data/                        Tasks, profiles, and defect-definition loading
  providers/                   Generation-provider adapters for later synthesis
data/                          Legacy generation fixtures retained for service tests
tests/                         Unit, integration, and UI suites by function
```

The current Streamlit entry point provides three top-level pages: Home,
Generation, and Defect detection. Home is the central navigation page.
Generation is the primary working view: its sidebar selects the T1/T2/T3 task,
Ollama model, batch size, tolerance, and connection URL. Its main content is
organised into Target profile, Programming task, Prompt, Results, and Analytics
tabs before running the shared validation and detector workflow. Defect
detection remains a complementary page for authentic-submission analysis.
The legacy demonstration task controls are not exposed.

## Empirical research foundation

The authoritative research catalog is formalized in
`config/defect_specifications.json`. It records the 17 active YAML-defined defects,
conservative detection rules, exclusions, evidence requirements, and the
T1/T2/T3 eligibility matrix. Raw detection is intentionally separate from task
eligibility; low-opportunity defects remain eligible and carry a separate
opportunity level.

The exploratory `redundant_for` detector remains implemented and covered by
controlled tests, but is excluded from the active catalogue because no positive
authentic examples were found in the available T3 submissions.

The research services currently provide:

- typed detection results in `models/research.py`;
- strict Boolean-proof detection for `redundant_comparison` in
  `detectors/research/redundant_comparison.py`;
- task and defect eligibility in `services/research/eligibility.py`;
- task-first and equal-task-weighted family prevalence in
  `services/research/prevalence.py`;
- manual validation metrics in `services/research/validation_metrics.py`.

The authoritative detector registry is covered by definition-level tests.
Manual detector validation and empirical profile interpretation remain separate
research steps.

## Required workflow

```text
Authentic submission workbook
→ Functional validation
→ Shared research detectors
→ Per-Lab/Question reports
→ Prototype-task prevalence summary
→ Empirical generation target profile
→ Synthetic generation
```

The dashboard denominator is parseable submissions marked functionally correct
by the functional-validation dataset. Each prototype task page exposes its
mapped authentic tasks, detector eligibility, affected counts, task-level
prevalence, and report paths for auditability.

## Automated synthetic-generation comparison

The experiment runner compares three conditions using the same task, target
profile, batch size, model, validation tests, and repair budget:

- `non_adaptive_baseline`: task contract only; no intentional defect guidance;
- `task_aware_non_adaptive`: task-aware defect assignment in one generation
  pass, with up to the configured repair attempts;
- `task_aware_iterative`: the task-aware condition followed by bounded,
  non-regressive calibration iterations.

Run a local Ollama experiment with:

```powershell
python scripts/run_generation_experiment.py --task T1 --model qwen2.5-coder:1.5b
```

The command compares functional pass rate, task-independent coverage,
task-dependent coverage, category-requirement rate, mean absolute profile
error, root mean square profile error, and the proportion of defect rows within
tolerance. It appends one compact JSON record per experiment to
`research-notes/synthetic-generation-experiments/experiment-log.jsonl`.
The log stores configuration, condition summaries, iteration metrics, and stop
reasons; it intentionally excludes generated source and prompts so repeated
experiments remain reviewable without creating oversized repository files.
