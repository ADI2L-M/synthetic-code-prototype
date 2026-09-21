# Synthetic Novice Code Generation and Calibration Prototype

A deterministic Streamlit proof of concept for generating functionally correct
synthetic novice Python submissions against a Context-Aware Target Profile.

The current implementation intentionally uses Demo/Mock mode. A live LLM is
not connected.

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
app.py                     Thin Streamlit entry point
ui/                        Session state and presentation modules
  sections/                Configure, Generate, Results, Analyse & Calibrate
services/workflow.py       End-to-end iteration orchestration
services/validator.py      Timed subprocess controller
services/validation_runner.py
                            Submission execution inside the subprocess
detectors/                 One AST detector per defect plus a registry
models/types.py            Shared domain data structures
data/                      Tasks, profiles, defect repository, Demo fixtures
tests/                     Domain, workflow, and Streamlit AppTest coverage
```

The workflow service is independent of Streamlit and of any particular
generation provider. `DemoProvider` implements the same provider protocol that
a future live provider can implement.

## Required workflow

```text
Programming Task
→ Task Context Profile
→ Context-Aware Target Profile
→ Generation Specification
→ Demo Generation
→ Functional Validation
→ Defect Detection
→ Observed Synthetic Defect Profile
→ Target/Observed Comparison
→ Calibration
```

Calibration changes generation constraints only. It never changes the
Context-Aware Target Profile.

## Demonstration data

All target prevalence values and generated examples are deterministic
demonstration data:

- `data/tasks.json`
- `data/demonstration_profiles.json`
- `data/defect_repository.json`
- `data/demo_submissions.json`

They are not empirical findings and are labelled as a **Demonstration
Profile** in the interface.
