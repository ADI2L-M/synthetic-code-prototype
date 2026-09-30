# Section 3: Design Artefact Evaluation

## Evaluation basis and scope

This report evaluates the repository as it exists on 1 October 2026. It uses the evaluation prompt supplied for Section 3 and distinguishes implemented behaviour from intended or proposed behaviour. The report does not treat a passing software test as proof that the research claims are externally valid.

The artefact is an iteratively calibrated synthetic-generation framework for functionally correct novice Python code:

```text
authentic submissions
    -> functional eligibility and AST detection
    -> task-family prevalence profile
    -> prototype-task target profile
    -> task-aware prompt and defect assignment
    -> local LLM generation
    -> functional validation
    -> AST defect detection
    -> synthetic prevalence and uncertainty-aware comparison
    -> optional calibration or automated iterative calibration
    -> retained synthetic artefact and experiment log
```

### Verification snapshot

| Evidence | Current result | Interpretation |
|---|---:|---|
| Automated repository tests | 150 passed | Current automated implementation behaviour is passing. |
| Ruff | `All checks passed!` | The current Ruff verification reports no findings. |
| Controlled detector fixtures | 34/34 passed across 17 active detectors | The controlled positive/negative detector suite passes. |
| Manually reviewed detector labels | 1,332 | Evidence exists for detector-readiness assessment. |
| Detector readiness | 15 validated; 2 pilot-validated | The catalogue is not fully at the configured evidence threshold. |
| Experiment logs | 12 JSONL files, 13 records | Baseline, task-aware, and iterative conditions have been executed across T1-T3. The latest completed suite contains one record per task, three repetitions per condition, batch size 20, temperature 0.2, and up to three iterative generations. |

The results support the claim that this is a working research prototype. They do not yet establish that the synthetic code is statistically equivalent to authentic student code, that all detectors are fully validated, or that the approach generalises beyond the selected tasks, models, and local Ollama environment.

## A. Prototype overview

### Intended purpose

The prototype generates synthetic novice Python submissions for three task families while preserving functional correctness and measuring task-independent and task-dependent defect styles:

| Prototype task | Task family | Function | Main task-dependent defect scope |
|---|---|---|---|
| T1 | Conditional logic | `classify_temperature(temp)` | Redundant conditionals and conditional-structure defects |
| T2 | List processing | `total_scores(scores)` | Redundant indexing, misleading iterator names, duplicate expressions, augmentable assignments |
| T3 | Numeric iteration | `sum_to_n(n)` | `while_as_for` and augmentable assignments |

The target profile is derived from authentic CS1 submissions. The primary estimator is the equal-task-weighted arithmetic mean of eligible task-level prevalence. The stored profile also includes pooled prevalence, task minimum and maximum, standard deviation, eligible task count, valid submission count, and affected submission count.

### Current end-to-end workflow

1. Authentic submissions are functionally filtered and mapped to prototype-task families.
2. Parseable, functionally eligible submissions are analysed with the research detector registry.
3. Task-level prevalence reports and grouped prototype-task reports are written as JSON.
4. `build_empirical_target_profile()` averages eligible task-level prevalence and omits defects that are not applicable to a prototype task.
5. The Streamlit user selects T1, T2, or T3, a local Ollama model, batch size, tolerance, and endpoint.
6. `plan_defect_assignments()` creates reproducible fractional assignments, including rare-defect assignments with expected counts below one.
7. `build_generation_specification()` constructs a task-family brief, and `build_submission_specification()` constructs a per-submission brief.
8. Ollama produces one submission per request. The active provider uses a 16,384-token context, 1,200-token output limit, default temperature 0.2, and a deterministic seed derived from experiment repetition, task, iteration, submission, and repair-attempt information. Initial batches use a matched seed namespace across the baseline and task-aware conditions.
9. Each submission is functionally validated in a timed subprocess.
10. A failed or incomplete submission can receive up to two repairs, giving three total attempts. The workflow retains the best attempt according to functional validity and unresolved repair requirements rather than automatically accepting the last attempt.
11. Functionally valid submissions are analysed with the same research AST/token detectors used for authentic prevalence.
12. Observed prevalence uses only functionally valid submissions as its denominator.
13. `compare_profiles()` compares target and observed prevalence using target-relative tolerance plus a sampling-aware margin when counts are available.
14. The Streamlit user can manually apply calibration and regenerate.
15. The experiment runner can automatically compare baseline, task-aware non-adaptive, and task-aware iterative conditions, with repetitions, a maximum iteration limit, repair limits, temperature, and explicit condition selection.
16. The retained Streamlit artefact and its calibration lineage can be exported as a ZIP archive. CLI experiments are written as compact timestamped JSONL records.

### Technologies, libraries, and models

- Python and the standard-library `ast`, `tokenize`, `subprocess`, `urllib`, `json`, and `zipfile` modules.
- Streamlit for the multi-page research interface.
- pandas for tabular display and transformation.
- Ollama's local HTTP API for LLM generation.
- pytest for unit, integration, and AppTest UI verification.
- Ruff for static checks.
- JSON, JSONL, CSV, XLSX, and ZIP research artefacts.
- Configured UI models: `qwen2.5-coder:1.5b`, `deepseek-coder:1.3b`, and `granite-code:3b`.
- `google-genai` is listed in `requirements.txt`, but it is not used by the current generation path.

### Main modules

| Concern | Evidence |
|---|---|
| Streamlit entry point and navigation | `app.py` |
| Home page | `app_pages/home.py`, `ui/home.py` |
| Generation page | `app_pages/generation.py`, `ui/generation.py` |
| Authentic detection page | `app_pages/defect_detection.py`, `ui/research_dashboard.py` |
| Session-state iteration storage | `ui/state.py` |
| Prototype task contracts | `services/generation/prototype_tasks.py` |
| Defect assignment | `services/generation/assignment.py` |
| Prompt construction | `services/generation/prompt_builder.py` |
| Generation and repairs | `services/generation/workflow.py`, `services/generation/prototype_runner.py` |
| Local model adapter | `services/providers/ollama.py` |
| Functional validation | `services/generation/validator.py`, `services/generation/validation_runner.py` |
| Research detector registry | `detectors/research/registry.py` and `detectors/research/` |
| Prevalence and profile comparison | `services/generation/analysis.py`, `services/research/prevalence.py` |
| Empirical target construction | `services/research/target_profile.py` |
| Calibration | `services/generation/calibrator.py` |
| Automated experiment runner | `services/generation/experiment.py`, `scripts/run_generation_experiment.py` |
| Sequential task runner | `scripts/run_all_generation_experiments.ps1` |
| Export | `services/generation/export.py` |
| Tests | `tests/unit/`, `tests/integration/`, `tests/ui/` |

### Framework implementation status

| Conceptual element | Status | Evidence |
|---|---|---|
| Context-aware empirical target profile | Implemented | `services/research/target_profile.py`; stored in `research-notes/authentic-submission-outputs/empirical-target-profile.json` |
| Task-family eligibility and omission of non-applicable defects | Implemented | `services/research/eligibility.py`, `target_profile.py` |
| Task-aware generation constraints | Implemented | `prompt_builder.py`, `assignment.py`, `workflow.py` |
| Local LLM generation | Implemented | `services/providers/ollama.py` |
| Functional correctness gate | Implemented | `validator.py`, `validation_runner.py` |
| Reusable research detectors | Implemented | `detectors/research/registry.py` |
| Synthetic prevalence profile | Implemented | `services/generation/analysis.py` |
| Uncertainty-aware target comparison | Implemented | `compare_profiles()` |
| Manual Streamlit calibration | Implemented | `app_pages/generation.py`, `ui/generation.py` |
| Non-regressive calibration guard | Implemented | `calibrator.py` |
| Automated baseline comparison | Implemented in service/CLI | `experiment.py`, `run_generation_experiment.py`; not exposed as a Streamlit experiment screen |
| Automated iterative calibration | Implemented in service/CLI | `run_experiment()` with `task_aware_iterative`; evaluates all configured iterations unless an iteration reaches the tolerance objective, then retains the best eligible iteration. |
| Persistent compact experiment logging | Implemented for CLI experiments | Schema-versioned timestamped JSONL logs store configuration, condition summaries, per-iteration metrics, constraints, selected iteration, out-of-tolerance defects, and zero-observed defects. |
| Persistent Streamlit iteration history | Implemented | Local SQLite storage persists runs, iterations, submissions, prompts, validation, and detector results. |
| Fully automatic UI convergence loop | Not implemented | The user manually triggers the next Streamlit calibration iteration. |
| Complete detector validation for all active detectors | Not yet complete | Two detectors remain pilot-validated by the current review evidence; the validation workflow itself is implemented. |

## B. Functionality

| Functionality | Status | Relevant implementation | Behaviour |
|---|---|---|---|
| Load authentic research outputs | Implemented | `services/research/dashboard.py`, `ui/app_data.py` | Loads the prepared reports and profile used by the application. |
| Build task-level prevalence | Implemented | `task_prevalence()` | Uses valid and defect-eligible submissions only. |
| Build family prevalence | Implemented | `family_prevalence()` | Equal-weights eligible tasks and also reports pooled prevalence. |
| Build prototype target | Implemented | `build_empirical_target_profile()` | Converts grouped prevalence into T1/T2/T3 generation-ready values and omits non-applicable defects. |
| Select task | Implemented | `load_prototype_tasks()`, `render_generation_sidebar()` | Provides T1, T2, and T3 task contracts. |
| Plan rare assignments | Implemented | `plan_defect_assignments()` | Uses fractional expected quotas and reproducible stable seeds. |
| Build task prompt | Implemented | `build_generation_specification()` | Lists functional requirements and all applicable defect names without embedding prevalence percentages. |
| Build submission prompt | Implemented | `build_submission_specification()` | Adds assigned defect briefs, observable signatures, task-specific patterns, category requirements, and unassigned-style avoidance guidance. |
| Build baseline prompt | Implemented | `build_baseline_specification()` | Gives the task contract without defect-generation guidance. |
| Call local LLM | Implemented | `OllamaProvider._generate_one()` | Sends a non-streaming `/api/generate` request and extracts Python source. |
| Repair output | Implemented | `_repair_specification()`, `run_iteration()` | Requests correction of functional failures, missing assigned defects/categories, and unexpected defects. |
| Functional testing | Implemented | `validate_source()` | Executes submissions in a timed subprocess and compares return values or expected exceptions. |
| Detect defects | Implemented | `detect_research_defects()` | Runs the research detector registry on parsed source. |
| Construct synthetic profile | Implemented | `observed_profile()`, `observed_counts()` | Counts each defect over functionally valid submissions. |
| Compare profiles | Implemented | `compare_profiles()` | Stores difference, target standard error, Wilson interval, decision margin, status, and recommended action. |
| Calibrate manually | Implemented | `calibration_constraints()`, Streamlit generation page | Converts Increase/Reduce/Maintain actions into the next prompt constraints. |
| Protect against regression | Implemented | `calibration_is_non_regressive()` | Requires the next candidate to preserve functional pass rate, independent coverage, dependent coverage, and category requirement rate. |
| Repeat generation | Implemented in two forms | Streamlit session state and `run_experiment()` | Streamlit repeats on user action; CLI experiments repeat automatically up to the configured limit. |
| Baseline comparison | Implemented | `BASELINE_CONDITION`, `run_experiment()` | Supports baseline, task-aware non-adaptive, and task-aware iterative conditions. |
| Export code | Implemented | `iteration_export_archive()` | Exports source files, a manifest, and a lossless `iteration.json` payload. |
| Export calibrated artefact | Implemented | `calibrated_artifact_export_archive()` | Exports the selected batch, calibration lineage, and replayable payload. |
| Visualise results | Implemented | `ui/generation.py`, `ui/research_dashboard.py` | Displays task details, prompts, code, functional outcomes, profile alignment, category coverage, and calibration history. |

Generated submissions that remain invalid or incomplete after the repair budget are still recorded for review but do not contribute to the observed prevalence denominator.

## C. Usability evaluation

### User operation

The current Streamlit workflow is:

1. Open Home, which is the default page.
2. Navigate to Generation.
3. Select a prototype task, local model, batch size, tolerance, and Ollama URL.
4. Generate a batch.
5. Inspect the Programming task, Target profile, Prompt, Results, and Analytics tabs.
6. Review functional validation, assigned defects, detected defects, source code, and prompts.
7. Inspect individual iterations in an overlay card.
8. Export an iteration or the retained calibrated artefact.
9. Use the calibration action when the profile needs improvement.

During generation, the sidebar controls and generation-related inspection/export
actions are disabled. A native Streamlit modal overlay runs the generation job in
the background, reports the selected task, model, batch, iteration, current
submission, repair attempt, validation phase, and final profile-calculation
phase, and provides a cancellation action.

### Usability strengths

- Home, Generation, and Defect detection are separate navigable application pages.
- Generation controls are separated into the sidebar, leaving the main area for research evidence.
- The Programming task tab is first, followed by target profile, prompt, results, and analytics.
- Exact per-submission prompts are visible after generation.
- Generation exposes a live viewport overlay and disables conflicting controls
  while the background generation job is running.
- Generated code and functional-test failures are visible per submission.
- Analytics separates category coverage from defect-level profile alignment.
- Defect alignment can be filtered by category or defects outside tolerance.
- Detailed uncertainty and detector counts are available in an expander.
- The Analytics tab explicitly identifies the retained iteratively calibrated artefact.
- Calibrated outputs can be exported with their lineage rather than only as anonymous source files.

### Usability limitations

- The local Ollama service must be available at the configured endpoint.
- Generation runs in a background job but can still be slow for larger batches or repeated repairs.
- Iteration history is persisted in the local SQLite store, but there is not yet a multi-user or remote database.
- The Analytics tab provides a compact browser for JSONL experiment records; it does not yet provide repeated-run uncertainty plots.
- Experiment conditions, repetitions, maximum iterations, and repair budgets are configured in the CLI rather than in the Generation UI.
- The user must explicitly request calibration in Streamlit.
- There is no automatic convergence recommendation in the UI.
- The UI presents three configured models; it does not discover installed Ollama models dynamically.

## D. Static analysis

### Modularity and separation of concerns

The current architecture has a sensible separation between domain models, UI, generation services, providers, research processing, detector implementations, and tests. Prompt generation is not embedded in the Streamlit page. Functional validation and prevalence comparison are also separate from UI rendering.

The shared `run_iteration()` function is the key integration boundary. Both the interactive Streamlit wrapper and the experiment runner use the same generation, validation, detector, and comparison mechanics. Their orchestration differs, but the lower-level evaluation principle is shared.

### Configuration and traceability

The active defect catalogue is `config/defect_specifications.json`, with 17 configured defects. Task-specific YAML files are retained under `research-notes/task-def-yaml/`, and detector-validation records are under `research-notes/detector-validation/`. Prototype task contracts are defined in Python in `services/generation/prototype_tasks.py`.

Within an iteration, traceability is strong:

```text
target profile
    -> assignment plan and selected defect styles
    -> exact captured prompt
    -> generated source
    -> validation result
    -> detector output
    -> observed counts and prevalence
    -> comparison and calibration action
```

`IterationResult` and `SubmissionResult` preserve target values, constraints, prompts, seeds, source code, validation, detected defects, attempt count, and category status.

### Static strengths

- Business logic is separated from the Streamlit presentation.
- The same detector registry is reused for authentic and synthetic submissions.
- Experiment configuration is explicit through `ExperimentConfig`.
- The calibrated-artifact manifest improves provenance of exported batches.
- The current test suite and Ruff verification pass after the latest workflow and maintenance updates.

### Static limitations

- `requirements.txt` does not pin dependency versions.
- Model versions and Ollama runtime versions are not captured in experiment records.
- Several compatibility or legacy modules remain alongside the newer `services/generation`, `services/research`, and `services/providers` structure.
- `ui/sections/` contains older UI-oriented modules that may confuse future maintenance even though the current page uses `ui/generation.py`.
- The functional validator executes generated code with `exec()` in a timed subprocess. The subprocess and timeout reduce risk but are not a complete security sandbox.
- The target-profile JSON still labels its detector source as `preliminary_raw_detector_estimates`, even though a separate detector-readiness report now provides pilot validation evidence. These evidence-status descriptions should be reconciled before final research reporting.
- The active prompt catalogue and task-specific patterns are partly configured in Python and partly in JSON/YAML, increasing the risk of configuration drift.

## E. Dynamic analysis

### One interactive generation

`app_pages/generation.py` loads dashboard data and calls `run_prototype_iteration()`. The wrapper calls `run_iteration()` with the selected task, target profile, batch size, model, context length, tolerance, target standard errors, and active constraints.

For each submission, `run_iteration()`:

1. selects mandatory task-independent and task-dependent styles;
2. adds target-driven assignments from the assignment plan;
3. builds the exact submission brief;
4. calls the provider with a reproducible seed;
5. validates the returned source;
6. runs detector analysis only when functional validation passes;
7. checks assigned styles, required categories, and unexpected styles;
8. issues a repair request when required, up to the attempt limit;
9. stores all evidence in `SubmissionResult`.

### Functional failure

When generated code fails to parse, raises an unexpected exception, returns an incorrect value, or times out, validation returns `FAIL`. The workflow can send a revision request. If all attempts fail, the submission remains visible but is excluded from the valid denominator used for prevalence.

### Detection behaviour

For parseable valid source, the research registry returns detector results containing presence, count, locations, evidence, and notes. In the generation workflow the submission stores Boolean defect presence for the relevant defect IDs. Parse-invalid source is not passed to the research detectors for prevalence.

Unexpected detector exceptions are allowed to surface as run failures rather than being silently converted into prevalence values. The current policy is explicit failure and requires the caller to retry or inspect the error; it is not a recovery or sandbox policy.

### Profile comparison

For each target defect, the comparison stores:

- target prevalence;
- observed prevalence;
- signed difference;
- valid denominator and observed count;
- target standard error;
- Wilson 95% interval for the synthetic sample;
- combined allowed difference;
- `Within tolerance`, `Underrepresented`, or `Overrepresented` status;
- `Maintain`, `Increase`, or `Reduce` action.

When a valid denominator and target standard errors are available, the allowed difference is the larger of target-relative tolerance and the combined 95% sampling margin. Consequently, a 10% setting is not interpreted as a universal 10 percentage-point interval.

### Calibration behaviour

Streamlit calibration is optional and user initiated. The current comparison is converted into constraints, a new batch is generated, and the candidate is rejected if it decreases any of the four protected quality dimensions:

- functional pass rate;
- task-independent coverage;
- task-dependent coverage;
- category requirement rate.

The CLI experiment runner performs the same kind of iterative comparison automatically for `task_aware_iterative`. It evaluates every configured iteration unless a batch reaches the tolerance objective early. When the objective is not reached, it continues calibration from the latest observed batch even if that batch is worse than the current best. The initial batch is the quality floor: a later batch can replace it only when it preserves functional validity, task-independent coverage, task-dependent coverage, and category-requirement coverage. Among eligible batches, the runner retains the best profile-aligned iteration, with within-tolerance and coverage measures used as tie-breakers.

## F. Optimisation and resource use

| Mechanism | Status and evidence |
|---|---|
| Configurable sample size | Implemented; Streamlit allows 1-50, CLI accepts `--batch-size`. |
| Repair limit | Implemented; default two repairs, three total attempts. |
| Iteration limit | Implemented in experiment runner; default maximum three iterative iterations. |
| Early acceptance | Implemented in experiment runner when all profile rows are within tolerance. |
| Non-regressive selection guard | Implemented in experiment runner and Streamlit calibration path; it prevents a worse calibrated batch from replacing the retained batch but does not prematurely stop the configured iterative evaluation. |
| Stable assignment and generation seeds | Implemented in `assignment.py` and `OllamaProvider`. |
| Cached dashboard loading | Implemented through `@st.cache_data`. |
| Subprocess timeout | Implemented for functional validation. |
| Provider batching | Not used as a multi-submission model request; submissions are requested individually. |
| Parallel generation | Not implemented. |
| Persistent result cache | Implemented for Streamlit run history through local SQLite; cross-process caching is not implemented. |
| Automatic UI convergence loop | Not implemented. |
| Experiment scheduling/parallel jobs | Not implemented; the Streamlit page has a background generation job, but there is no experiment scheduler or parallel batch-generation service. |

The main resource-saving mechanism is bounded repair and iteration control. The current architecture prioritises traceability and per-submission inspection over throughput.

## G. Black-box testing

Black-box evidence is strongest in integration tests and Streamlit `AppTest` tests because those tests exercise externally observable outcomes through public workflow or UI entry points.

| Test ID or group | Input/condition | Expected external behaviour | Repository evidence | Result |
|---|---|---|---|---|
| `test_demo_generation_validates_and_detects_defects` | Demo provider and a prototype task | Valid source passes and selected defects are detected | `tests/integration/test_workflow.py` | Passed in the 150-test run |
| `test_failed_submissions_are_excluded_from_denominator` | One valid and one failed submission | Observed profile uses only valid submissions | `tests/integration/test_workflow.py` | Passed |
| `test_comparison_and_tolerance_actions` | Target and observed profile with discrepancy | Status and action are produced | `tests/integration/test_workflow.py` | Passed |
| `test_sampling_aware_comparison_records_counts_and_wilson_interval` | Counts and denominator supplied | Comparison contains sampling interval and decision margin | `tests/integration/test_workflow.py` | Passed |
| `test_calibration_rejects_regression_in_mandatory_category_coverage` | Candidate loses category coverage | Candidate is rejected by non-regression guard | `tests/integration/test_workflow.py` | Passed |
| `test_calibration_allows_equal_or_better_quality` | Candidate is equal or better on protected dimensions | Candidate is accepted by guard | `tests/integration/test_workflow.py` | Passed |
| `test_home_is_the_default_view` | App initialisation | Home is the first view | `tests/ui/test_app.py` | Passed |
| `test_generation_view_exposes_main_controls` | Generation page | Task, model, batch, tolerance, and generation controls are visible | `tests/ui/test_app.py` | Passed |
| `test_generation_main_content_has_task_and_prompt_tabs` | Generation page and tab changes | Programming task and prompt tabs render expected content | `tests/ui/test_app.py` | Passed |
| `test_defect_detection_is_a_separate_complementary_view` | Defect detection page | Detection is separated from generation controls | `tests/ui/test_app.py` | Passed |
| `test_authentic_task_browser_exposes_lab_12_q2_report` | Detection page with T2 and Lab 12 Q2 | Authentic task report is discoverable | `tests/ui/test_app.py` | Passed |
| Research-pipeline integration tests | Authentic observations including parse failures and unknown correctness | Eligibility and raw detection are preserved or excluded as specified | `tests/integration/test_research_pipeline.py` | Passed |

### Black-box gaps

The repository does not currently provide dedicated black-box tests for:

- missing or malformed empirical profile files in the Streamlit path;
- unavailable Ollama model or network failure through the UI;
- a full browser-level presentation of an Ollama network/model failure;
- recovery across separate application processes or database corruption;
- automated statistical comparison of multiple independent repetitions.

## H. White-box testing

White-box coverage verifies internal rules, detector structures, and edge cases.

| Component | Internal behaviour tested | Evidence |
|---|---|---|
| `plan_defect_assignments()` | Stable, balanced, fractional assignment for rare defects | `tests/unit/services/test_assignment.py` |
| `build_generation_specification()` | Task contract, category lists, prevalence redaction | `tests/unit/services/test_prototype_generation.py` |
| `build_submission_specification()` | Assigned guidance, required signatures, avoidance of unassigned styles | `tests/unit/services/test_prototype_generation.py` |
| `OllamaProvider._build_prompt()` | Baseline and guided instruction construction | `tests/unit/providers/test_ollama_prompt.py`, prototype-generation tests |
| `validate_source()` and runner | Correct results, failures, exception handling, and timeout path | `services/generation/validator.py`, integration tests |
| Research detector registry | Catalogue coverage, selected dispatch, parse-failure records | `tests/unit/detectors/test_research_detectors.py` |
| Individual AST detectors | Positive and negative structural patterns | `tests/unit/detectors/test_research_detectors.py` |
| `redundant_comparison` detector | Boolean-comparison scope and false-positive rejection | `tests/unit/detectors/test_research_redundant_comparison.py` |
| `task_prevalence()` and `family_prevalence()` | Valid/eligible denominator, equal task weighting, non-applicable omission | `tests/unit/services/test_prevalence.py` |
| `build_empirical_target_profile()` | Flat values and omission of non-applicable defects | `tests/unit/services/test_target_profile.py` |
| `compare_profiles()` | Relative tolerance, sampling intervals, rare and zero observations | `tests/integration/test_workflow.py` |
| `calibration_is_non_regressive()` | Functional and category coverage protection | `tests/integration/test_workflow.py` |
| `run_experiment()` | Conditions, iteration records, compact JSONL output, input validation | `tests/unit/services/test_generation_experiment.py` |
| Export functions | Source files, manifests, and calibrated lineage | `tests/unit/services/test_generation_export.py` |
| Detector readiness metrics | Confusion metrics, pending/pilot/validated status, label loading | `tests/unit/services/test_detector_validation.py`, `test_validation_metrics.py` |

### White-box gaps

- The invariant tests cover bounded Wilson intervals, comparison action consistency, and assignment-plan caps, but there is no property-based test suite.
- Detector tests are controlled structural examples; they do not cover all semantic variations in authentic code.
- Unsafe imports/calls are rejected before execution and non-terminating code is timed out, but this is not a complete sandbox against every malicious or resource-exhaustive program.
- Export replay is tested through `load_iteration_export_archive()`, but a full regenerated experiment replay is not yet tested.
- Detector co-occurrence is implemented and tested; causal interaction effects, such as whether one injected style changes another detector's result, remain unevaluated.

## I. Experimental simulation capability

### Conditions

The experiment service implements three conditions:

1. `non_adaptive_baseline`: task-only prompt, no intentional defect assignment.
2. `task_aware_non_adaptive`: target-aware assignment and defect guidance, without iterative constraint updates.
3. `task_aware_iterative`: target-aware generation followed by calibration constraints and bounded regeneration.

These conditions share `run_iteration()` for generation, validation, detection, and comparison. The experiment service adds orchestration, repetition, condition summaries, stop reasons, and JSONL logging.

### Testing protocol and prompt treatment

Each experiment uses the same prototype-task contract, functional evaluator,
research detector registry, target profile, batch size, tolerance, model,
context length, temperature, and repair budget for all conditions. For each
repetition, the initial random seed namespace is matched across the baseline
and task-aware conditions. This controls the assignment/generation draw as far
as the condition-specific prompt permits. The task-aware iterative condition
then receives new iteration numbers and calibration constraints, so later
iterations are intentionally different treatments.

The testing sequence for each generated submission is:

1. Send one prompt to the local Ollama `/api/generate` endpoint.
2. Extract the required Python function from the response.
3. Execute the function against every task evaluator case in a timed subprocess.
4. If the source fails or does not meet the assigned-style requirements, issue
   up to two revision requests. The workflow retains the best attempt by
   functional validity and unresolved repair requirements, rather than always
   accepting the last attempt.
5. Run the reusable research AST/token detector registry only for functionally
   valid submissions.
6. Compute defect prevalence using the valid-submission denominator, compare it
   with the empirical target, and aggregate the resulting metrics across
   repetitions.

The prompts are condition-specific as follows. The provider sends one combined
plain-text prompt; there is no separate system-message channel in the current
Ollama adapter.

#### 1. Non-adaptive baseline prompt

The baseline is the control treatment. Its initial specification is built by
`build_baseline_specification(task)` and contains only the task contract:

```text
PROMPTING CONDITION: NON-ADAPTIVE BASELINE

Generate a conventional implementation from the task contract only.
Do not add any generation objective beyond functional correctness.

PROGRAMMING TASK
[task description]

FUNCTIONAL REQUIREMENTS
- [functional requirement 1]
- [functional requirement 2]
- ...

IMPORTANT
The program must remain functionally correct.
```

The Ollama adapter then appends the common execution instructions and the
functional evaluator cases:

```text
You are generating one Python submission for a programming task
from its task contract only.

FUNCTIONAL TEST CASES
- args=[...]; expected=...
- args=[...]; expected=...

INSTRUCTIONS
- Implement the required function.
- The submission must pass every functional test case above.
- Follow only the programming task and functional requirements.
- Return only executable Python source code.
```

The baseline prompt does not include defect names, defect examples, category
requirements, target percentages, or calibration actions. Its purpose is to
measure the defect distribution that emerges from ordinary task-only
generation.

#### 2. Task-aware non-adaptive prompt

The task-aware non-adaptive condition uses the same task and functional cases,
but adds task-aware defect guidance. The task-level specification is built by
`build_generation_specification()`, while every submission receives a separate
`build_submission_specification()` containing its assigned styles:

```text
PROGRAMMING TASK
[task description and functional requirements]

POTENTIAL TASK-INDEPENDENT DEFECTS
- [applicable names only]

POTENTIAL TASK-DEPENDENT DEFECTS
- [applicable names only]

GENERATION FOCUS
Task-dependent structural defects are the primary research focus.
When a task-dependent defect is assigned in the submission brief,
implement that exact structure while preserving functional correctness.
```

The per-submission section then adds:

```text
MANDATORY SELECTED DEFECTS — implement every listed style

Task-independent:
- [assigned task-independent defect]

ASSIGNED TASK-DEPENDENT DEFECTS TO PRIORITISE:
- [assigned task-dependent defect]

MANDATORY CATEGORY REQUIREMENT:
- Include at least one task-independent defect.
- Include at least one task-dependent defect.

MANDATORY DEFECT IMPLEMENTATION GUIDANCE
- [definition or construction hint]
  Required observable signature: [detector signature]
  Example pattern: [short contrastive example]
  Task-specific valid pattern to adapt: [task-specific pattern]

UNASSIGNED DEFECTS TO AVOID
- [unassigned style guidance]
```

The assignment planner uses the empirical target profile to select styles and
plan expected frequencies, but prevalence percentages are deliberately not
shown to the model. This separates target estimation from prompt execution and
tests whether structural guidance produces the intended defects.

#### 3. Task-aware iterative prompt

Iteration 1 uses the same task-aware submission prompt as the non-adaptive
condition. After the batch is validated and compared, the next prompt appends
calibration actions derived from the latest observed profile:

```text
CALIBRATION ADJUSTMENTS

These actions update the next iteration's defect emphasis. Follow them
without breaking functional correctness or the mandatory category requirement.
- inappropriate formatting: strengthen the generation constraint
- magic number: reduce the generation constraint
- duplicate expression: maintain the generation constraint
```

The iterative condition regenerates and evaluates every configured iteration
unless a batch reaches the tolerance objective early. If tolerance is not
reached, calibration continues from the latest observed batch even when that
batch is worse than the retained batch. The initial batch remains the quality
floor; a later batch replaces it only when it preserves functional pass rate,
task-independent coverage, task-dependent coverage, and category-requirement
coverage. The experiment log records every iteration's prompt constraints,
metrics, out-of-tolerance defects, selected iteration, and stop reason.

When a submission requires a repair, the shared repair prompt is based on the
`REVISION REQUEST` template and contains the failed validation, missing
requirements, previous source, and any required task-specific pattern. For the
baseline, the `PROMPTING CONDITION: NON-ADAPTIVE BASELINE` marker is preserved
on the repair prompt, so the Ollama wrapper does not append defect-generation
guidance. Guided conditions retain their assigned-style and category guidance
when repaired. The repair budget and attempt-selection rule are held constant
across conditions; the initial condition prompt remains the primary treatment
being compared.

### Configurable parameters

`ExperimentConfig` supports:

- task ID;
- target profile;
- batch size;
- tolerance;
- model and context length;
- generation temperature;
- repetitions;
- maximum iterative iterations;
- maximum repair attempts;
- selected conditions;
- target standard errors.

The command-line entry point additionally accepts the profile path, Ollama URL, experiment ID, log path, and condition list. `run_all_generation_experiments.ps1` runs T1, T2, and T3 sequentially.

### Metrics and storage

The experiment runner records:

- functional pass rate;
- task-independent coverage;
- task-dependent coverage;
- category requirement rate for guided conditions;
- mean absolute profile error;
- root mean square profile error;
- within-tolerance rate;
- valid and total submission counts;
- iteration-level profile comparisons;
- out-of-tolerance defects;
- zero-observed defects;
- selected iteration;
- stop reason;
- constraints used in each iteration.

It deliberately does not store source code or prompts in the compact experiment log. Source and prompt inspection remains available in the interactive Streamlit session and calibrated-artefact export.

### Existing experiment evidence

The repository contains 12 JSONL files and 13 experiment records under
`research-notes/synthetic-generation-experiments/`. The latest completed suite
contains three records, one for each prototype task. Each record uses
`qwen2.5-coder:1.5b`, temperature 0.2, batch size 20, three repetitions, and a
maximum of three iterative generations. The table reports the mean across the
three repetitions; therefore, values such as 19.67 valid submissions are
averages of whole-number repetition results, not fractional submissions.

| Task | Condition | MAE | Valid submissions | Functional pass | Within tolerance | Independent coverage | Dependent coverage | Selected iterations |
|---|---|---:|---:|---:|---:|---:|---:|---|
| T1 | Baseline | 0.0984 | 16.33 | 81.7% | 83.3% | 100.0% | 0.0% | 1, 1, 1 |
| T1 | Task-aware non-adaptive | 0.0870 | 19.67 | 98.3% | 83.3% | 100.0% | 11.8% | 1, 1, 1 |
| T1 | Task-aware iterative | 0.0866 | 20.00 | 100.0% | 83.3% | 100.0% | 11.7% | 1, 1, 1 |
| T2 | Baseline | 0.1578 | 20.00 | 100.0% | 45.8% | 3.3% | 0.0% | 1, 1, 1 |
| T2 | Task-aware non-adaptive | 0.1231 | 20.00 | 100.0% | 70.8% | 80.0% | 48.3% | 1, 1, 1 |
| T2 | Task-aware iterative | 0.1268 | 20.00 | 100.0% | 66.7% | 81.7% | 51.7% | 1, 1, 1 |
| T3 | Baseline | 0.2247 | 20.00 | 100.0% | 61.1% | 20.0% | 0.0% | 1, 1, 1 |
| T3 | Task-aware non-adaptive | 0.2455 | 20.00 | 100.0% | 44.4% | 96.7% | 40.0% | 1, 1, 1 |
| T3 | Task-aware iterative | 0.2178 | 20.00 | 100.0% | 50.0% | 96.7% | 41.7% | 3, 1, 2 |

The latest evidence shows three different outcomes. For T1, iterative
calibration slightly improves profile error and functional validity, but the
initial batch remains the best selected iteration in every repetition. For T2,
iterative calibration increases task-dependent coverage but does not improve
MAE or within-tolerance rate, so the initial batch is retained in every
repetition. For T3, iterative calibration improves MAE over both baseline and
non-adaptive task-aware prompting, and selected iterations vary across
repetitions. These results support the operation of the selection and
non-regression workflow, but they are preliminary evidence for RQ3 rather than
a general claim about all models or tasks.

## J. Evaluation gaps and priorities

### Priority 1: Complete detector validation and evidence-status reconciliation

The controlled fixture report passes 34/34 cases, and the gold-label readiness report contains 1,332 labels. Fifteen active detectors meet the pilot count and metric criteria. `empty_if` and `redundant_not` are still pilot-validated because they have fewer than 20 positive reviewed examples. Detector readiness should be reported separately from controlled-fixture correctness, and the target profile metadata should be updated to reflect the latest validation status.

### Priority 2: Extend the repeated experiment evidence

The latest T1-T3 suite now uses three repetitions per condition, so repeated
execution is demonstrated in the repository evidence. RQ3 still requires a
larger pre-specified study across models and, ideally, more independent batches
per condition before making a general claim. Confidence intervals or another
uncertainty treatment should be reported for the condition-level comparisons.

### Priority 3: Pre-specify the primary evaluation objective

The runner now evaluates all configured iterative generations unless a batch
reaches the tolerance objective. It then retains the best eligible batch using
profile error as the primary ranking criterion and within-tolerance and
coverage measures as tie-breakers, while using the initial batch as a
non-regression quality floor. This is an explicit operational policy, but the
research evaluation should still predefine whether the primary reported
outcome is mean absolute profile error, within-tolerance rate, category
coverage, or a multi-objective rule.

### Priority 4: Distinguish assignment compliance from authentic-style prevalence

The guided workflow deliberately assigns styles and requires at least one defect from each category. This is useful for testing controllability, but it introduces intervention. The baseline, task-aware non-adaptive, and iterative conditions must be interpreted as different prompting treatments rather than as equally natural samples.

### Priority 5: Measure defect interactions

The Analytics tab now reports valid-submission defect co-occurrence pairs through `detector_interaction_rows()`. This addresses descriptive interaction measurement. It does not establish causality or show whether intentionally assigning one style changes another style's detector result; that remains a future experiment.

### Priority 6: Strengthen reproducibility

The project records seeds, prompts, model name, context length, target profile, tolerance, experiment configuration, and persistent local iteration state. It does not yet record model digest, Ollama version, or a pinned Python/dependency lockfile. These should be captured for a final experiment package.

### Priority 7: Improve Streamlit experiment analysis

The Analytics tab now presents the retained calibrated artefact, its lineage, and a browser for available JSONL experiment records. A future complementary improvement is to compare repeated conditions with uncertainty plots and distinguish selected iterations from rejected candidates across runs.

## K. Section 3 evidence summary

| Evaluation Area | Evidence Present | Relevant File/Function | Main Finding | Limitation |
|---|---|---|---|---|
| Functionality | End-to-end generation, validation, detection, comparison, calibration, export, and experiment services | `services/generation/workflow.py`, `experiment.py`, `ui/generation.py` | The principal artefact workflow is implemented. | Streamlit and CLI expose different orchestration layers. |
| Usability | AppTest coverage and organised Streamlit pages/tabs | `app.py`, `app_pages/`, `ui/generation.py`, `tests/ui/test_app.py` | The user can configure, inspect, calibrate, export, and browse experiment records. | No multi-user store or repeated-run uncertainty dashboard. |
| Static Analysis | Layered modules, `IterationResult` traceability, clean Ruff verification | `models/types.py`, `services/`, `detectors/`, `ruff check .` | Separation of concerns and current code quality are acceptable for a prototype. | Dependencies are unpinned and legacy/compatibility modules remain. |
| Dynamic Analysis | Integration tests and workflow implementation | `run_iteration()`, `validate_source()`, `compare_profiles()` | Invalid code is bounded by repairs and excluded from the valid denominator; comparison is sampling-aware. | Detector exceptions and sandbox hardening need further work. |
| Optimisation | Repair limits, maximum iterations, early acceptance, non-regression guard, cached dashboard data | `workflow.py`, `experiment.py`, `ui/app_data.py` | Unbounded regeneration is prevented. | No parallel generation, cross-process cache, or experiment scheduler. |
| Black-box Testing | 150 passing tests including integration and AppTest tests | `tests/integration/`, `tests/ui/` | External workflow and page behaviour are exercised. | Full live Ollama failure presentation and cross-process persistence need additional tests. |
| White-box Testing | Detector, prompt, assignment, comparison, calibration, storage, interaction, export, and experiment unit tests | `tests/unit/` | Core internal rules and persistence invariants are directly tested. | No property-based suite, full sandbox, or causal interaction experiment. |
| Experimental Simulation | Three conditions, repetitions, bounded iterative calibration, metrics, JSONL logs | `services/generation/experiment.py`, `scripts/run_generation_experiment.py` | The repository can execute the intended prompting-condition comparison and has a latest three-repetition T1-T3 suite. | Evidence remains limited to one model and one recent batch size, so RQ3 is not yet answered conclusively. |

## Descriptive and literature-informed interpretation

The artefact is best described as a functioning design-science research prototype rather than a validated production benchmark. Its principal contribution is an operational chain connecting authentic defect evidence to task-aware synthetic generation and then back to measurable prevalence comparison. The reusable detector registry, functional gate, target-relative and sampling-aware comparison, calibration guard, and experiment runner make the chain executable and inspectable.

The evaluation should therefore make three distinctions explicit:

1. **Artefact correctness**: whether the implemented workflow executes as specified. Current tests and fixtures provide positive evidence for this.
2. **Detector validity**: whether the structural detectors correspond to the project's operational defect definitions. Current evidence is pilot-level, with two detectors needing more positive review examples.
3. **Synthetic benchmark validity**: whether generated code is sufficiently similar to authentic code for the intended research use. The current experiment logs are preliminary evidence only and do not establish this claim.

Suggested local literature placeholders to verify before final submission:

- `[A3-conceptualize-artefacts.pdf, page to verify]` for the definition and evaluation of design artefacts.
- `[A4-designing-system.pdf, page to verify]` for design-science evaluation strategy and artefact assessment.
- `[A2-literature-review.pdf, page to verify]` for the literature context on code quality, novice programming, or synthetic data generation.
- `[A1-introduction.pdf, page to verify]` for the research motivation and problem context.

These placeholders are intentionally not presented as complete bibliographic citations because the repository stores course reading PDFs rather than a resolved reference list. Page numbers and author-year details should be confirmed from the source PDFs before they are inserted into the academic draft.

## Relationship to the research questions

### RQ1: Classification of authentic defect types

The repository implements the operational basis for RQ1: defect definitions are catalogued in `config/defect_specifications.json` and YAML research notes; task applicability is encoded in the catalogue; authentic task reports are produced by `run_prevalence_reports()`; and grouped profiles use eligible task-level prevalence. The resulting target profile distinguishes task-independent defects from task-dependent defects and records non-applicable defects as omitted rather than zero.

The remaining RQ1 limitation is detector validity. The classification is operationally implemented, but the final empirical claim requires completing review evidence for the pilot-validated detectors and explaining the sampling and task-family mapping decisions.

### RQ2: Incorporating empirical profiles into task-aware prompting

The repository implements this mechanism through target profiles, assignment planning, per-submission briefs, task-specific patterns, observable defect signatures, and category requirements. Numeric prevalence is used to plan assignments and compare outputs, while the prompt describes the selected styles rather than exposing target percentages directly. This is an intentional prompt-design decision, but it means prevalence control is mediated by assignment and calibration rather than by the LLM interpreting percentages.

The remaining RQ2 limitation is empirical reliability across model sizes and tasks. The logs show meaningful task-aware category coverage, but task-dependent coverage remains uneven, especially for T1 and T3.

### RQ3: Effect of iterative task-aware refinement

The repository implements the comparison mechanism through three prompting conditions, configurable repetitions, bounded all-iteration calibration, best-iteration selection, a non-regression quality floor, metrics, and JSONL logs. The latest three-repetition T1-T3 suite shows that iterative calibration improves T1 profile error slightly, improves T3 profile error and dependent coverage, and increases T2 dependent coverage while worsening T2 profile error slightly. Therefore, the current artefact provides preliminary repeated evidence for RQ3, but the evidence is limited to one model, one recent batch size, and three repetitions per task.

## Overall evaluation conclusion

The prototype has reached a substantial and testable artefact state. The generation feature, reusable detector service, empirical target profiles, functional gate, repair-attempt selection, bounded iterative calibration, experiment runner, logging, export, and Streamlit analytics are present and connected at the core workflow level. The latest evaluation demonstrates repeated execution and task-specific differences, but it does not establish general superiority of iterative calibration. The next step is to complete any remaining detector review, expand the repeated experiment across models and batch sizes, record environment/model provenance, and interpret improvement against pre-specified metrics and uncertainty.
