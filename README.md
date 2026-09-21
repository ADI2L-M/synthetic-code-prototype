# Synthetic Novice Code Generation and Calibration Prototype

A deterministic Streamlit proof of concept for generating functionally correct
synthetic novice Python submissions against a Context-Aware Target Profile.

The app supports deterministic Demo mode and local Ollama generation with
`qwen2.5-coder:7b`.

## Run the application

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

## Use the local Qwen model

Ollama must be running on its default URL. Since Ollama is already installed
with `qwen2.5-coder:7b`, start the app and select **Local Ollama** in the
sidebar. Do not run a second `ollama serve` process if Ollama is already
running in the background.

The default settings are:

```text
Model: qwen2.5-coder:7b
URL: http://localhost:11434
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
