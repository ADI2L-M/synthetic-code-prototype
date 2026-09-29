# Section 3: Design Artefact Evaluation

## Evaluation basis and scope

This report evaluates the repository as it exists on 29 September 2026. It uses the evaluation prompt supplied for Section 3 and distinguishes implemented behaviour from intended or proposed behaviour. The report does not treat a passing software test as proof that the research claims are externally valid.

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
| Automated repository tests | 139 passed | Current automated implementation behaviour is passing. |
| Ruff | `All checks passed!` | No current Ruff findings were reported by the verification command. |
| Controlled detector fixtures | 34/34 passed across 17 active detectors | The controlled positive/negative detector suite passes. |
| Manually reviewed detector labels | 1,332 | Evidence exists for detector-readiness assessment. |
| Detector readiness | 15 validated; 2 pilot-validated | The catalogue is not fully at the configured evidence threshold. |
| Experiment logs | 5 JSONL files | Baseline, task-aware, and iterative conditions have been executed for T1-T3, with one additional T1 log. |

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
8. Ollama produces one submission per request. The active provider uses a 16,384-token context, 1,200-token output limit, temperature 0, and a deterministic seed derived from task, iteration, submission, and condition information.
9. Each submission is functionally validated in a timed subprocess.
10. A failed or incomplete submission can receive up to two repairs, giving three total attempts.
11. Functionally valid submissions are analysed with the same research AST/token detectors used for authentic prevalence.
12. Observed prevalence uses only functionally valid submissions as its denominator.
13. `compare_profiles()` compares target and observed prevalence using target-relative tolerance plus a sampling-aware margin when counts are available.
14. The Streamlit user can manually apply calibration and regenerate.
15. The experiment runner can automatically compare baseline, task-aware non-adaptive, and task-aware iterative conditions, with repetitions and a maximum iteration limit.
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
| Automated iterative calibration | Implemented in service/CLI | `run_experiment()` with `task_aware_iterative` |
| Persistent compact experiment logging | Implemented for CLI experiments | Timestamped JSONL logs under `research-notes/synthetic-generation-experiments/` |
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

### Usability strengths

- Home, Generation, and Defect detection are separate navigable application pages.
- Generation controls are separated into the sidebar, leaving the main area for research evidence.
- The Programming task tab is first, followed by target profile, prompt, results, and analytics.
- Exact per-submission prompts are visible after generation.
- Generated code and functional-test failures are visible per submission.
- Analytics separates category coverage from defect-level profile alignment.
- Defect alignment can be filtered by category or defects outside tolerance.
- Detailed uncertainty and detector counts are available in an expander.
- The Analytics tab explicitly identifies the retained iteratively calibrated artefact.
- Calibrated outputs can be exported with their lineage rather than only as anonymous source files.

### Usability limitations

- The local Ollama service must be available at the configured endpoint.
- Generation is synchronous and can be slow for larger batches or repeated repairs.
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
- Current Ruff verification is clean.

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

The CLI experiment runner performs the same kind of iterative comparison automatically for `task_aware_iterative`, stopping when the candidate is accepted, when the non-regression guard is triggered, or when the maximum iteration count is reached.

## F. Optimisation and resource use

| Mechanism | Status and evidence |
|---|---|
| Configurable sample size | Implemented; Streamlit allows 1-50, CLI accepts `--batch-size`. |
| Repair limit | Implemented; default two repairs, three total attempts. |
| Iteration limit | Implemented in experiment runner; default maximum three iterative iterations. |
| Early acceptance | Implemented in experiment runner when all profile rows are within tolerance. |
| Non-regressive stop | Implemented in experiment runner and Streamlit calibration path. |
| Stable assignment and generation seeds | Implemented in `assignment.py` and `OllamaProvider`. |
| Cached dashboard loading | Implemented through `@st.cache_data`. |
| Subprocess timeout | Implemented for functional validation. |
| Provider batching | Not used as a multi-submission model request; submissions are requested individually. |
| Parallel generation | Not implemented. |
| Persistent result cache | Implemented for Streamlit run history through local SQLite; cross-process caching is not implemented. |
| Automatic UI convergence loop | Not implemented. |
| Experiment scheduling/background jobs | Not implemented. |

The main resource-saving mechanism is bounded repair and iteration control. The current architecture prioritises traceability and per-submission inspection over throughput.

## G. Black-box testing

Black-box evidence is strongest in integration tests and Streamlit `AppTest` tests because those tests exercise externally observable outcomes through public workflow or UI entry points.

| Test ID or group | Input/condition | Expected external behaviour | Repository evidence | Result |
|---|---|---|---|---|
| `test_demo_generation_validates_and_detects_defects` | Demo provider and a prototype task | Valid source passes and selected defects are detected | `tests/integration/test_workflow.py` | Passed in the 139-test run |
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

### Configurable parameters

`ExperimentConfig` supports:

- task ID;
- target profile;
- batch size;
- tolerance;
- model and context length;
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

Five JSONL experiment logs are present under `research-notes/synthetic-generation-experiments/`. The following summary is descriptive, not a statistical conclusion, because the recorded runs use one repetition per condition.

| Log | Task | Model | Batch | Condition pattern | Key observed result |
|---|---|---|---:|---|---|
| `experiment-log.jsonl` | T1 | qwen2.5-coder:1.5b | 10 | baseline, task-aware, iterative | Iterative functional pass rate 1.00; dependent coverage 0.30; within-tolerance rate 0.92. |
| `experiment-log-290926124333.jsonl` | T1 | qwen2.5-coder:1.5b | 10 | baseline, task-aware, iterative | Iterative dependent coverage 0.22 and functional pass rate 0.90. |
| `experiment-log-290926131306.jsonl` | T1 | qwen2.5-coder:1.5b | 50 | baseline, task-aware, iterative | Iterative dependent coverage 0.06; functional pass rate 1.00. |
| `experiment-log-290926135158.jsonl` | T2 | qwen2.5-coder:1.5b | 50 | baseline, task-aware, iterative | Task-aware non-adaptive dependent coverage 0.42; iterative dependent coverage 0.42. |
| `experiment-log-290926144358.jsonl` | T3 | qwen2.5-coder:1.5b | 50 | baseline, task-aware, iterative | Task-aware iterative dependent coverage 0.10; functional pass rate 1.00. |

These logs demonstrate that the experimental mechanism is executable and that task-aware prompting changes category coverage relative to the baseline. They also demonstrate that one run is insufficient to claim stable improvement: iterative calibration does not improve every metric in every recorded task and batch-size configuration.

## J. Evaluation gaps and priorities

### Priority 1: Complete detector validation and evidence-status reconciliation

The controlled fixture report passes 34/34 cases, and the gold-label readiness report contains 1,332 labels. Fifteen active detectors meet the pilot count and metric criteria. `empty_if` and `redundant_not` are still pilot-validated because they have fewer than 20 positive reviewed examples. Detector readiness should be reported separately from controlled-fixture correctness, and the target profile metadata should be updated to reflect the latest validation status.

### Priority 2: Evaluate the full experiment with repeated runs

The current JSONL examples use one repetition per condition. RQ3 requires repeated runs, confidence intervals or another uncertainty treatment for condition-level comparisons, and a pre-specified primary metric. The current runner supports repetitions, but a repeated study has not yet been demonstrated in the repository evidence.

### Priority 3: Define convergence and selection criteria before final experiments

The runner stops at acceptance, non-regressive guard, or maximum iterations. This is a practical stopping mechanism, but it is not a full convergence analysis. The research evaluation should predefine whether the primary objective is within-tolerance rate, mean absolute profile error, category coverage, or a multi-objective rule.

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
| Optimisation | Repair limits, maximum iterations, early acceptance, non-regression guard, cached dashboard data | `workflow.py`, `experiment.py`, `ui/app_data.py` | Unbounded regeneration is prevented. | No parallel generation, persistent cache, or background execution. |
| Black-box Testing | 139 passing tests including integration and AppTest tests | `tests/integration/`, `tests/ui/` | External workflow and page behaviour are exercised. | Full live Ollama failure presentation and cross-process persistence need additional tests. |
| White-box Testing | Detector, prompt, assignment, comparison, calibration, storage, interaction, export, and experiment unit tests | `tests/unit/` | Core internal rules and persistence invariants are directly tested. | No property-based suite, full sandbox, or causal interaction experiment. |
| Experimental Simulation | Three conditions, repetitions, bounded iterative calibration, metrics, JSONL logs | `services/generation/experiment.py`, `scripts/run_generation_experiment.py` | The repository can execute the intended prompting-condition comparison. | Existing evidence is mainly one repetition per condition, so RQ3 is not yet answered conclusively. |

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

The repository implements the comparison mechanism through three prompting conditions, configurable repetitions, bounded iterative calibration, non-regressive selection, metrics, and JSONL logs. Existing logs show that iterative calibration sometimes improves functional validity, dependent coverage, or within-tolerance rate, but not consistently across the small set of one-repetition runs. Therefore, the current artefact supports an RQ3 experiment but does not yet provide sufficient repeated evidence to answer RQ3 conclusively.

## Overall evaluation conclusion

The prototype has reached a substantial and testable artefact state. The generation feature, reusable detector service, empirical target profiles, functional gate, calibration logic, experiment runner, logging, export, and Streamlit analytics are present and connected at the core workflow level. The most important next step is not adding another generation feature; it is strengthening the evaluation evidence: complete detector review where required, run repeated controlled experiments, record environment/model provenance, and interpret iterative improvement against pre-specified metrics and uncertainty.
