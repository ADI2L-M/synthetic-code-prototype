# Synthetic Novice Code Research Prototype

Project architecture, product scope, and the controlled experiment protocol
are documented in:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/product-management.md`](docs/product-management.md)
- [`docs/experiment-protocol.md`](docs/experiment-protocol.md)

A Streamlit research prototype for studying whether task-aware LLM generation can
produce functionally correct synthetic CS1 Python submissions with defect
distributions comparable to authentic novice-code data. The application combines
authentic-submission profiling, AST-based defect detection, target-profile
construction, synthetic generation, functional validation, calibration, and
distribution-based evaluation.

The current UI is organised around prototype tasks T1, T2, and T3 and their mapped
authentic Lab/Question reports.

## Setup and run

### Prerequisites

- Windows PowerShell, macOS/Linux shell, or an equivalent terminal.
- Python 3.11 or newer.
- Git, if cloning the repository.
- Ollama only if you want to generate synthetic submissions. The Home and Defect
  detection pages can be inspected without a running Ollama service.

### Create the environment

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts for the current user, run PowerShell as
your user and allow local scripts once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then install the tested dependency set:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
```

For a faster, less strictly pinned development install, use:

```powershell
python -m pip install -r requirements.txt
```

### Start the Streamlit application

Run the command from the repository root so that the project data and research
artifacts resolve correctly:

```powershell
streamlit run app.py
```

Streamlit normally opens the application in a browser at
`http://localhost:8501`. If it does not open automatically, copy that address
into a browser. To use a different port:

```powershell
streamlit run app.py --server.port=8502
```

To stop the application, return to the terminal running Streamlit and press
`Ctrl+C`.

You can also start the app without activating the environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Use the application pages

The application exposes four top-level pages:

- **Home** — research overview, conceptual diagrams, empirical scope, and current
  evidence status.
- **Generation** — choose T1, T2, or T3; select an Ollama model; set batch size,
  temperature, tolerance, and connection URL; then generate and validate a batch.
- **Defect detection** — inspect authentic task reports, detector eligibility, and
  empirical prevalence targets.
- **Experiments** — review persisted interactive generation runs and formal CLI
  experiment logs.

## Ollama setup for synthetic generation

The Generation page and the experiment scripts call the Ollama HTTP API. Install
Ollama separately, start its local service, and pull at least one model listed by
the application:

```powershell
ollama serve
ollama pull qwen2.5-coder:1.5b
```

The available model choices are:

- `qwen2.5-coder:1.5b` — default;
- `deepseek-coder:1.3b`;
- `granite-code:3b`.

The default endpoint is `http://localhost:11434`. The Generation page exposes
this URL under **Connection settings**. The command-line experiment runner also
accepts `--base-url` when Ollama is hosted elsewhere.

Before generating, verify that Ollama can see the model:

```powershell
ollama list
```

Generation requests use a context length of 16,384 tokens, a maximum output of
1,200 tokens, and a default temperature of 0.2. The generated code is functionally
validated and analysed by the shared detector workflow before it is accepted.

## Verify the project

```powershell
python -m pytest -q
ruff check . --exclude .agents --exclude .claude --exclude .venv
```

The full test suite includes unit, integration, and Streamlit UI tests. The UI
tests use Streamlit's headless `AppTest` interface and do not require a browser
or a running Ollama service.

## Architecture

```text
app.py                         Thin Streamlit entry point
app_pages/                     Home, Generation, Defect detection, and Experiments pages
ui/                            Streamlit presentation modules
  home_research.py             Research overview and application landing view
  home.py                      Legacy landing-view module retained for compatibility
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
  legacy/                      Unused compatibility facades retained for migration
data/                          Legacy generation fixtures retained for service tests
tests/                         Unit, integration, and UI suites by function
```

The current Streamlit entry point provides four top-level pages: Home,
Generation, Defect detection, and Experiments. Home is the central navigation page.
Generation is the primary working view: its sidebar selects the T1/T2/T3 task,
Ollama model, batch size, tolerance, and connection URL. Its main content is
organised into Target profile, Programming task, Prompt, Results, and Analytics
tabs before running the shared validation and detector workflow. Defect detection
remains a complementary page for authentic-submission analysis, while
Experiments reviews controlled experiment logs and persisted run history.
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

## Interactive generation runs and outputs

When a batch is started from the **Generation** page, the application creates a
local generation run and records its lifecycle in SQLite. The run stores the
selected task, model, batch size, temperature, tolerance, timestamps, status, and
any completion error. Calibration iterations remain associated with the same run.

The **Experiments** page shows the 50 most recent interactive runs separately from
the formal CLI experiment logs. This history is useful for provenance and
troubleshooting; it is not itself a controlled comparison of generation
conditions.

Interactive run data is written to:

```text
outputs/synthetic-generation/generation.sqlite3
```

The `outputs/` directory is intentionally ignored by Git. Generated submissions,
prompts, iteration results, and export archives are local experimental artifacts
and should be reviewed before sharing or committing them.

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

To run T1, T2, and T3 sequentially from PowerShell:

```powershell
.\scripts\run_all_generation_experiments.ps1
```

The batch size and model can be changed without editing the script:

```powershell
.\scripts\run_all_generation_experiments.ps1 -BatchSize 100 -Model qwen2.5-coder:1.5b
```

The script continues to the next task after a failure. Add `-StopOnError` to
stop at the first failed experiment.

The command compares functional pass rate, task-independent coverage,
task-dependent coverage, category-requirement rate, mean absolute profile
error, root mean square profile error, and the proportion of defect rows within
tolerance. It writes one compact JSONL file per experiment using the filename
pattern `research-notes/synthetic-generation-experiments/experiment-log-DDMMYYHHMMSS.jsonl`.
The log stores configuration, condition summaries, iteration metrics, per-defect
comparisons, zero-observed defects, and stop reasons. It intentionally excludes
generated source and prompts so repeated experiments remain reviewable without
creating oversized repository files.

### Experiment runner options

The single-task runner accepts the following commonly used options:

```powershell
python scripts/run_generation_experiment.py `
  --task T1 `
  --model qwen2.5-coder:1.5b `
  --base-url http://localhost:11434 `
  --batch-size 10 `
  --temperature 0.2 `
  --tolerance 0.10 `
  --repetitions 1 `
  --max-iterations 3 `
  --max-repair-attempts 2
```

Use `--conditions` to run only selected conditions. For example, this runs only
the one-pass task-aware condition:

```powershell
python scripts/run_generation_experiment.py `
  --task T2 `
  --conditions task_aware_non_adaptive
```

Use `--log <path>` to write the JSONL record to a custom location. If no log path
is provided, the runner creates a timestamped file under
`research-notes/synthetic-generation-experiments/`.

### Running all prototype tasks

The PowerShell wrapper defaults to T1, T2, and T3 with a batch size of 50. Adjust
the run without editing the script:

```powershell
.\scripts\run_all_generation_experiments.ps1 `
  -Tasks T1,T2,T3 `
  -BatchSize 100 `
  -Repetitions 3 `
  -Model qwen2.5-coder:1.5b
```

The wrapper continues to the next task if one task fails. Add `-StopOnError` when
the run should stop at the first failure.

## Troubleshooting

### `streamlit` is not recognized

Activate `.venv` first, or invoke Streamlit through the environment's Python:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Generation cannot connect to Ollama

Check that the service is running and that the configured URL matches the service:

```powershell
ollama serve
ollama list
```

If Ollama is running on another host or port, update **Connection settings** on
the Generation page or pass `--base-url` to the experiment runner.

### A model is missing

Pull the selected model before generating:

```powershell
ollama pull qwen2.5-coder:1.5b
```

The model name must match one of the choices exposed by the application.

### Cached or persisted state looks stale

Streamlit caches dashboard data in memory. Restart the application, or clear its
cache from a terminal:

```powershell
streamlit cache clear
```

Interactive generation history is stored separately in
`outputs/synthetic-generation/generation.sqlite3`. Delete or archive that file
only when you intentionally want to reset local run history.

## Research status and limitations

This repository contains a research prototype rather than a completed benchmark.
The current interface supports the integrated workflow, but detector validity,
larger fixed-configuration experiments, and final comparison of adaptive and
non-adaptive generation conditions still require further evaluation. Results from
small batches should be interpreted with sampling uncertainty and should not be
treated as claims about individual student cognition.
