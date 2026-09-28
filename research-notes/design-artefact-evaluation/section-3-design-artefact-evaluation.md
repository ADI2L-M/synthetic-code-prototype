# Section 3: Design Artefact Evaluation

## Evaluation verdict

The prototype is a working research prototype for generating functionally correct synthetic Python submissions and comparing their detected defect profiles against authentic CS1 submissions.

The core workflow is implemented:

> authentic defect profile → task-aware prompt → Ollama generation → functional validation → AST defect detection → synthetic profile → comparison → calibration → regeneration

The prototype is not yet a complete experimental evaluation framework. The main missing capabilities are:

- automated comparison between baseline, non-adaptive, and adaptive prompting;
- persistent experiment/run storage;
- automatic stopping or convergence criteria;
- stronger detector validation for rare or absent defects;
- formal measurement of defect interaction;
- resolution of current Ruff/static-analysis issues.

Current repository evidence:

- Full test suite: **116 passed**.
- Active controlled detector fixtures: **34/34 passed**.
- Manual detector labels: **1,332**.
- Active detector-catalogue validation status: **pilot validated**.
- Ruff: **31 reported errors**, primarily wildcard compatibility imports and import-order errors.

The test results demonstrate implementation behaviour, but they do not by themselves establish the scientific validity of the synthetic benchmark or prove that the LLM reproduces authentic defect distributions.

## A. Prototype overview

### Intended purpose

The prototype generates synthetic novice Python code for three prototype tasks:

- **T1: Conditional logic** — `classify_temperature`;
- **T2: List processing** — `total_scores`;
- **T3: Numeric iteration** — `sum_to_n`.

Generated submissions are required to remain functionally correct while exhibiting selected task-independent and task-dependent defect styles.

The prototype evaluates:

- functional correctness;
- detected defect categories;
- target-versus-observed prevalence;
- defect-category coverage;
- calibration performance across iterations.

### Current end-to-end workflow

1. Authentic submissions are filtered for functional correctness.
2. Authentic submissions are grouped into task families.
3. Research AST/token detectors analyse valid submissions.
4. Task-level defect prevalence is calculated.
5. Prototype-task target profiles are produced using arithmetic means across related authentic tasks.
6. The user selects a prototype task, model, batch size, tolerance, and Ollama URL.
7. The system constructs a task-aware prompt.
8. Ollama generates one submission at a time.
9. Each submission is functionally tested.
10. Valid submissions are analysed by the shared research detectors.
11. The synthetic defect profile is calculated from valid submissions only.
12. The synthetic profile is compared with the empirical target.
13. Calibration constraints can be applied manually.
14. A new iteration can be generated.
15. Generated code and metadata can be exported as a ZIP archive.

Primary evidence:

- `services/generation/workflow.py`
- `services/generation/prototype_runner.py`
- `services/research/prevalence_runner.py`
- `services/research/target_profile.py`
- `README.md`

### Technologies and models

The repository uses:

- Python;
- Streamlit;
- pandas;
- Altair and Matplotlib;
- Ollama through HTTP requests;
- Python `ast` and `tokenize`;
- pytest;
- Ruff;
- JSON, CSV, XLSX, and ZIP-based export files.

The configured Ollama models are:

- `qwen2.5-coder:1.5b`;
- `deepseek-coder:1.3b`;
- `granite-code:3b`.

The provider uses a 16,384-token context length, a 1,200-token output limit, and temperature 0.3. Although `google-genai` is listed in `requirements.txt`, no current generation path uses it.

### Main components

| Component | Main location |
|---|---|
| Streamlit entry point | `app.py` |
| Home page | `app_pages/home.py` |
| Generation page | `app_pages/generation.py` |
| Generation interface | `ui/generation.py` |
| Session-state iteration storage | `ui/state.py` |
| Prototype tasks | `services/generation/prototype_tasks.py` |
| Prompt construction | `services/generation/prompt_builder.py` |
| Ollama interaction | `services/providers/ollama.py` |
| Generation workflow | `services/generation/workflow.py` |
| Functional validation | `services/generation/validator.py` |
| Research detectors | `detectors/research/` |
| Profile comparison | `services/generation/analysis.py` |
| Calibration | `services/generation/calibrator.py` |
| Export | `services/generation/export.py` |

### Implemented versus not implemented

| Framework element | Status |
|---|---|
| Context-aware target profile | Implemented |
| Task-specific prompt construction | Implemented |
| Local LLM generation | Implemented |
| Functional validation | Implemented |
| AST-based defect detection | Implemented |
| Synthetic profile construction | Implemented |
| Target comparison | Implemented |
| Manual iterative calibration | Implemented |
| Non-regression protection during calibration | Implemented |
| Automatic convergence loop | Not implemented |
| Persistent experiment database/log | Not implemented |
| Automated baseline comparison | Not implemented |
| Multi-run statistical experiment orchestration | Not implemented |
| Fully validated detector catalogue | Not yet complete |

## B. Functionality

| Functionality | Status | Evidence and behaviour |
|---|---|---|
| Load target profile | Implemented | `load_empirical_target_values()` loads empirical target values. |
| Construct empirical profile | Implemented | `build_empirical_target_profile()` uses the arithmetic mean of task-level prevalence values. |
| Select prototype task | Implemented | `load_prototype_tasks()` and the generation sidebar provide T1–T3 selection. |
| Configure generation | Implemented | `render_generation_sidebar()` provides model, batch size, tolerance, and Ollama URL controls. |
| Construct prompts | Implemented | `build_generation_specification()` and `build_submission_specification()` construct task-aware prompts. |
| Use target prevalence | Partially implemented | Prevalence affects assignment planning and comparison, but numerical prevalence is deliberately omitted from the LLM prompt. |
| Generate code | Implemented | `OllamaProvider.generate()` sends requests to the local Ollama API. |
| Repair failed output | Implemented | `run_iteration()` allows up to three total generation attempts per submission. |
| Functional testing | Implemented | `validate_source()` executes generated code against task test cases in a subprocess. |
| Defect detection | Implemented | `detect_research_defects()` dispatches to the 17 active research detectors. |
| Synthetic profile | Implemented | `observed_profile()` calculates defect prevalence using valid submissions only. |
| Profile comparison | Implemented | `compare_profiles()` records target, observed value, difference, confidence interval, status, and action. |
| Calibration | Implemented | `calibration_constraints()` creates adjustment instructions from profile discrepancies. |
| Calibration protection | Implemented | `calibration_is_non_regressive()` rejects candidates that reduce functional or category coverage. |
| Repeated generation | Partially implemented | The interface supports manual iterations stored in Streamlit session state. |
| Baseline comparison | Not implemented | No dedicated automated baseline/non-adaptive/adaptive experiment runner was found. |
| Export | Implemented | `iteration_export_archive()` exports generated source files and a manifest. |
| Visualisation | Implemented | The generation and research dashboards show results, comparisons, iteration history, and task reports. |

Generated submissions that remain invalid after three attempts are retained in the iteration result but excluded from the observed defect-profile denominator.

## C. Usability

### User workflow

The user operates the prototype through Streamlit:

1. Open the Home page.
2. Navigate to Generation.
3. Select a prototype task.
4. Select an Ollama model.
5. Set batch size and tolerance.
6. Generate a batch.
7. Inspect the programming task, prompt, results, and analytics tabs.
8. Apply calibration and generate another iteration if required.
9. Open individual submissions in an overlay card.
10. Export an iteration as a ZIP file.

### Usability strengths

The interface provides:

- separate Home, Generation, and Defect Detection pages;
- clear generation controls in the sidebar;
- programming task, target profile, prompt, results, and analytics tabs;
- source-code visibility;
- functional validation results;
- detected and assigned defect visibility;
- category coverage metrics;
- iteration history;
- calibration status;
- code export.

### Usability limitations

- Generation depends on a locally running Ollama service.
- Generation is synchronous; there is no dedicated background job queue.
- Iterations are stored only in Streamlit session state.
- Closing or restarting the application does not provide persistent iteration history.
- There is no integrated experiment comparison screen.
- The user must manually initiate calibration and regeneration.
- The interface does not automatically determine when profile alignment has converged.
- Older `ui/sections/` modules duplicate parts of the current generation UI and may increase maintenance confusion.

## D. Static analysis

### Modularity

The project has a layered structure containing UI, generation services, research services, detector registries, domain models, providers, and tests. This separation is visible in `models/`, `services/`, and `detectors/`.

### Separation of concerns

Prompt construction, generation, validation, detection, profile aggregation, calibration, and UI rendering are separated into different modules. This is a strength of the current design.

### Configuration

The main research configuration is stored in:

- `config/defect_specifications.json`;
- `research-notes/defect_definitions_yaml/`.

A maintainability issue remains: `prompt_builder.py` includes additional prompt-only task-independent defect names such as `non_descriptive_naming` and `unused_variable`, while the active research detector catalogue is based on 17 configured defects. These sources should be reconciled.

### Duplication

Static duplication exists in:

- compatibility facades under `detectors/`;
- compatibility service modules under `services/`;
- older UI sections under `ui/sections/`;
- demo data and current empirical data paths.

### Error handling and execution safety

Error handling exists for Ollama HTTP errors, connection failures, empty model responses, subprocess timeouts, malformed validation output, and invalid generated code.

Generated code is executed using Python `exec()` inside a subprocess. The timeout limits execution duration, but this is not a complete security sandbox.

### Dependency management

`requirements.txt` lists the main dependencies, but versions are not pinned. This limits reproducibility across machines and environments.

### Reproducibility

Positive features include:

- stable SHA-256-based seed generation;
- recorded generation seed;
- recorded model;
- recorded prompt;
- recorded generation attempts;
- recorded target profile and tolerance;
- exported manifest metadata.

Limitations include:

- no persistent run database;
- no environment lockfile;
- no model-version capture;
- no automatic storage of complete experiment configurations;
- Streamlit session state is temporary.

### Traceability

Traceability is reasonably strong within one iteration:

`target profile → assignment plan → prompt → source code → functional validation → detections → comparison → calibration constraints`

The `IterationResult` model preserves most of this information. The main weakness is that experimental runs are not persistently stored outside the current Streamlit session.

## E. Dynamic analysis

### One generation run

`run_iteration()`:

1. creates defect assignments;
2. builds a task-specific prompt;
3. calls the LLM;
4. validates the returned source code;
5. requests a repair generation when necessary;
6. detects defects after functional success;
7. records source, validation, defects, prompt, seed, attempts, and category status.

### Failed functional validation

If a generated submission fails:

- the failure is recorded;
- a repair prompt may be issued;
- up to three total generation attempts are allowed;
- if all attempts fail, the submission remains recorded as invalid;
- invalid submissions are excluded from the observed defect-profile denominator.

### Defect detection

Defect detection uses the shared research detector registry. Detection is based on parsed AST/token structures rather than LLM self-reporting.

A parse failure is recorded by the detector pipeline and does not produce a valid defect observation.

### Profile comparison

The comparison process records target prevalence, observed prevalence, difference, observed count, valid denominator, Wilson interval, target standard error, allowed difference, status, and recommended action.

The tolerance is not simply a fixed percentage-point difference. The implementation uses a target-relative tolerance combined with a sampling-aware margin.

### Calibration

Calibration translates discrepancy actions into `Increase`, `Reduce`, and `Maintain` constraints. The next iteration uses these constraints. A candidate iteration is rejected if it causes regression in functional pass rate, independent-defect coverage, dependent-defect coverage, or category-requirement rate.

### Multiple iterations

Manual repeated iterations are supported and displayed in the Analytics tab. Automatic repeated execution until convergence is not implemented.

## F. Optimisation

| Optimisation area | Status |
|---|---|
| Maximum repair attempts | Implemented; maximum three total attempts per submission |
| Configurable batch size | Implemented; UI allows 1–50 |
| Defect assignment planning | Implemented; uses fractional stochastic allocation |
| Avoiding excessive defect assignments | Implemented; assignment cap exists |
| Cached data loading | Implemented through cached loaders |
| Subprocess timeout | Implemented |
| Provider batching | Not used in the active workflow; submissions are generated individually |
| Early stopping | Not implemented |
| Automatic convergence detection | Not implemented |
| Persistent result caching | Not implemented |
| Parallel generation | Not implemented |
| Automatic experiment scheduling | Not implemented |

The system reduces unnecessary calls by repairing each submission only until it becomes functionally correct and category-compliant, or until the retry limit is reached.

## G. Black-box testing

The latest full test execution produced:

```text
116 passed in 31.00s
```

### Existing black-box tests

| Test ID | Behaviour tested | Evidence | Result |
|---|---|---|---|
| `test_demo_generation_validates_and_detects_defects` | A generated/demo submission is functionally validated and analysed | `tests/integration/test_workflow.py` | Passed |
| `test_failed_submissions_are_excluded_from_denominator` | Invalid submissions do not contribute to prevalence | `tests/integration/test_workflow.py` | Passed |
| `test_comparison_and_tolerance_actions` | Profile discrepancies produce actions | `tests/integration/test_workflow.py` | Passed |
| `test_sampling_aware_comparison_records_counts_and_wilson_interval` | Comparison records sampling-aware statistics | `tests/integration/test_workflow.py` | Passed |
| `test_calibration_changes_constraints_not_target_profile` | Calibration modifies constraints rather than the target profile | `tests/integration/test_workflow.py` | Passed |
| `test_calibration_rejects_regression_in_mandatory_category_coverage` | Worse calibration candidates are rejected | `tests/integration/test_workflow.py` | Passed |
| `test_home_is_default_page` | Home is the initial application page | `tests/ui/test_app.py` | Passed |
| `test_generation_view_exposes_main_controls` | Generation controls are visible | `tests/ui/test_app.py` | Passed |
| `test_generation_view_has_task_prompt_results_and_analytics_tabs` | Main generation tabs are available | `tests/ui/test_app.py` | Passed |
| `test_detector_dashboard_is_separate_from_generation` | Defect detection is a separate application view | `tests/ui/test_app.py` | Passed |
| `test_controlled_fixtures_cover_every_detector_and_pass` | Controlled detector cases are executed | `tests/unit/services/test_detector_validation.py` | Passed |
| `test_iteration_export_contains_source_files_and_manifest` | Generated output can be exported | `tests/unit/services/test_generation_export.py` | Passed |

### Black-box tests not currently demonstrated

No dedicated black-box tests were found for:

- a missing empirical target profile;
- an invalid target-profile schema;
- an unavailable Ollama model;
- a live Ollama connection failure;
- automated baseline-versus-adaptive comparison;
- automatic convergence;
- comparison of repeated independent experiment runs.

## H. White-box testing

| Component | Internal behaviour to test | Existing evidence |
|---|---|---|
| `build_generation_specification()` | Correct task contract, defect categories, examples, and calibration constraints | `test_programming_task_brief_redacts_prevalence_and_lists_task_dependent_defects()` |
| `build_submission_specification()` | Only assigned defect guidance is included | `test_submission_prompt_contains_only_assigned_defect_guidance()` |
| Ollama prompt construction | Assigned defects are presented as hard requirements | `test_ollama_prompt_marks_assigned_defects_as_hard_requirements()` |
| `validate_source()` | Correct execution, failure, timeout, and malformed-output handling | Validator and prototype-generation tests |
| `detect_research_defects()` | Correct detector registration and dispatch | `test_research_registry_covers_all_catalog_defects()` |
| Individual AST detectors | Positive and negative structural cases | `tests/unit/detectors/test_research_detectors.py` |
| `redundant_comparison` detector | Boolean comparison definition and false-positive rejection | `tests/unit/detectors/test_research_redundant_comparison.py` |
| `task_prevalence()` | Only valid and eligible submissions are included | `tests/unit/services/test_prevalence.py` |
| `family_prevalence()` | Equal task weighting and non-applicable handling | `tests/unit/services/test_prevalence.py` |
| `build_empirical_target_profile()` | Target construction and omission of non-applicable defects | `tests/unit/services/test_target_profile.py` |
| Assignment planner | Reproducibility and rare-defect fractional allocation | `tests/unit/services/test_assignment.py` |
| Calibration guard | Non-regressive candidate acceptance | `tests/integration/test_workflow.py` |
| Export | Source and manifest completeness | `tests/unit/services/test_generation_export.py` |

### Detector-validation limitation

The detector validation artifact reports:

- 15 active detectors as validated;
- `empty_if` and `redundant_not` as pilot validated;
- overall active-catalogue status as pilot validated;
- `redundant_for` excluded from the active catalogue because there are no positive reviewed authentic examples.

The active detector implementation therefore has strong controlled-fixture evidence, but two active detectors still need more authentic positive examples. `redundant_for` is retained only as an exploratory detector and is not used for the primary prevalence benchmark.

## I. Experimental simulation capability

### Implemented conditions

The repository currently supports:

1. task-aware generation using empirical task profiles;
2. manual iterative calibration;
3. repeated generation using the selected model and batch size.

### Not implemented

There is no dedicated implementation for:

- a non-adaptive baseline condition;
- an automatically controlled task-aware non-iterative condition;
- a fully automated iterative condition;
- randomised repeated experimental runs;
- statistical comparison between conditions;
- persistent experiment-level result aggregation.

The prototype supports the mechanics needed for the experiment but not the complete experimental orchestration required to answer RQ3 directly.

### Configurable parameters

The interface supports:

- prototype task;
- Ollama model;
- batch size;
- relative tolerance;
- Ollama URL.

The provider additionally fixes context length, temperature, and output-token limits.

### Generations and metrics

The system can generate a configurable batch of 1–50 submissions. Each submission can require up to three generation attempts, including repair attempts.

Available metrics include:

- functional pass rate;
- valid and invalid submissions;
- average attempts;
- independent-defect coverage;
- dependent-defect coverage;
- category-requirement rate;
- guided and detected defect counts;
- target and observed prevalence;
- profile difference;
- Wilson confidence intervals;
- target standard error;
- tolerance status;
- recommended action;
- iteration history.

The repository contains empirical authentic profiles and generated iteration structures, but no persistent controlled experiment dataset comparing baseline, task-aware non-adaptive, and iteratively calibrated prompting.

## J. Evaluation gaps

### Priority 1: experimental comparison

Implement an experiment runner that executes and stores:

1. non-adaptive baseline;
2. task-aware prompting without calibration;
3. task-aware prompting with iterative calibration.

Each condition should use identical tasks, batch sizes, models, controlled seeds, and repeated independent runs.

### Priority 2: persistent experiment logging

Store, for every run:

- experiment ID;
- condition;
- task;
- model and model version;
- prompt version;
- seed;
- batch size;
- temperature;
- target-profile version;
- detector version;
- validation results;
- defect results;
- calibration history.

The current Streamlit session state is insufficient for research-grade reproducibility.

### Priority 3: convergence and stopping criteria

Define an explicit stopping rule, such as:

- all measurable defect categories within tolerance;
- no improvement after a fixed number of iterations;
- maximum iteration limit;
- no regression in functional correctness or category coverage.

### Priority 4: detector validity

Complete authentic manual validation for `empty_if`, `redundant_not`, and any active detector with few authentic positive examples. `redundant_for` should remain excluded unless positive authentic evidence is later identified.

### Priority 5: defect interaction

Measure defect co-occurrence and interaction between task-independent and task-dependent defects. The current analysis treats defects primarily as independent binary categories.

### Priority 6: prompt and configuration consistency

Reconcile the 17-defect active research catalogue, exploratory detector definitions, prompt-only defect names, legacy repositories, legacy UI modules, YAML definitions, and JSON specifications.

### Priority 7: secure execution

Generated code is executed with `exec()` in a subprocess. A stronger sandbox would be required before running untrusted code outside a controlled local research environment.

### Priority 8: static quality

Resolve the 31 Ruff errors, especially wildcard imports in compatibility facades and module-level imports after path manipulation in `scripts/validate_detectors.py`.

## K. Section 3 evidence summary

| Evaluation Area | Evidence Present | Relevant File/Function | Main Finding | Limitation |
|---|---|---|---|---|
| Functionality | Full generation, validation, detection, comparison, calibration, and export workflow | `run_iteration()`, `validate_source()`, `compare_profiles()` | Core prototype workflow is implemented | No complete automated experiment runner |
| Usability | Streamlit pages, sidebar controls, tabs, source display, analytics, export | `ui/generation.py`, `ui/home.py` | Usable interactive research prototype | Session-only storage and manual calibration |
| Static Analysis | Layered modules, domain models, detector registry, provider abstraction | `models/`, `services/`, `detectors/` | Reasonable modular design | 31 Ruff errors, legacy duplication, unpinned dependencies |
| Dynamic Analysis | Functional retries, detector execution, profile comparison, calibration guard | `services/generation/workflow.py` | Runtime behaviour is explicitly represented | No automated convergence or persistent runs |
| Optimisation | Retry limit, caching, fractional assignment, timeout, configurable batch size | `assignment.py`, `validator.py`, `ui/generation.py` | Basic resource controls exist | No parallelism, early stopping, or persistent caching |
| Black-box Testing | 116 passing tests including workflow and UI tests | `tests/integration/`, `tests/ui/` | Main observable behaviours are tested | No live Ollama or baseline experiment tests |
| White-box Testing | Unit tests for prompt builder, detectors, prevalence, assignment, calibration, and export | `tests/unit/` | Internal logic has substantial coverage | Some detector validity remains preliminary |
| Experimental Simulation | Configurable tasks, models, batches, iterations, metrics, and export | `prototype_runner.py`, `analytics.py`, `export.py` | Prototype supports manual simulation iterations | No baseline/adaptive comparison or persistent experiment dataset |

## Overall conclusion

The artefact is sufficiently implemented to evaluate the feasibility of task-aware synthetic-code generation and iterative defect-profile calibration.

It currently demonstrates:

- functional synthetic code generation;
- empirical target-profile construction;
- shared AST-based defect detection;
- sampling-aware profile comparison;
- manual iterative calibration;
- interactive inspection and export.

For the design-science evaluation, it should be described as a **functional research prototype**, not yet as a fully validated experimental framework. The next major development should be a persistent experiment runner that compares baseline, task-aware, and iteratively calibrated prompting under controlled repeated runs.
