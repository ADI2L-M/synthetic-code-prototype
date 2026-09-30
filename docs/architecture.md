# Architecture and ownership

## Product boundary

The prototype has one primary product capability: generating functionally
correct synthetic novice Python submissions for T1, T2, and T3. Authentic
defect detection is a complementary research capability used to construct and
audit the empirical target profile.

## Runtime layers

```text
app.py
  -> app_pages/
    -> ui/
      -> services/
        -> models/
        -> detectors/
        -> local Ollama provider
        -> SQLite generation storage
```

### Application layer

- `app.py` owns Streamlit navigation and page registration.
- `app_pages/` owns page orchestration and session-state transitions.
- `ui/` owns presentation, controls, tabs, progress, and export actions.

The top-level pages are deliberately separated by responsibility: Home explains
the artefact, Generation runs the primary workflow, Defect detection audits the
authentic evidence, and Experiments reviews reproducible CLI records and the
interactive run store.

### Domain and workflow layer

- `models/` contains shared typed data structures.
- `services/generation/` owns assignment, prompting, generation, validation,
  detection, comparison, calibration, export, and persistence.
- `services/research/` owns authentic-data eligibility, prevalence, target
  construction, and detector-review workflows.
- `services/authentic/` owns workbook ingestion and functional filtering.
- `services/providers/` owns model-provider adapters.
- `detectors/research/` is the reusable detector registry for authentic and
  synthetic submissions.

## Source-of-truth rules

- `config/` contains runtime configuration consumed by the application. The
  defect semantics and eligibility catalogue live in
  `defect_specifications.json`; generation task contracts and prompt policy
  live in `generation_configuration.json`, both loaded through
  `services/generation/configuration.py`.
- `research-notes/` contains research definitions, source evidence, generated
  reports, and experiment artefacts; it is not a second runtime implementation.
- `outputs/` contains local generated databases and other derived artefacts.
- Legacy compatibility facades have been removed from the active source tree;
  new internal imports target the functional subpackages directly.

## Persistence boundary

SQLite is the local authoritative store for interactive generation runs,
iterations, submissions, prompts, validation, and detector outputs. JSONL is a
portable export format for controlled CLI experiments. A JSONL record must be
reproducible from its configuration and provenance fields without storing the
entire generated source corpus.

## Change rules

1. Keep generation, validation, detection, and comparison independent of
   Streamlit.
2. Add UI orchestration only in `app_pages/` or presentation code in `ui/`.
3. Add new detector logic under `detectors/research/` and register it through
   the research registry.
4. Add tests beside the affected layer before removing a compatibility facade.
5. Run `pytest -q`, `ruff check .`, and `git diff --check` before committing.
