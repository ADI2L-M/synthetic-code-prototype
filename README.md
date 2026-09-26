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
ui/                            Streamlit presentation modules
  home.py                      Application landing view
  generation.py                Empirical target handoff for synthesis
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

The current Streamlit entry point provides three top-level views: Home,
Generation, and Defect detection. It reads the persisted empirical reports
through `services/research/dashboard.py`. Generation services remain available
for the next phase, but the legacy Demo/Ollama controls are not exposed in the
current research UI.

## Empirical research foundation

The authoritative research catalog is formalized in
`config/defect_specifications.json`. It records all 18 YAML-defined defects,
conservative detection rules, exclusions, evidence requirements, and the
T1/T2/T3 eligibility matrix. Raw detection is intentionally separate from task
eligibility; low-opportunity defects remain eligible and carry a separate
opportunity level.

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
