# Audit of authentic student defect profiles

**Scope and evidence date:** repository snapshot inspected 24 October 2026. This is a read-only reconstruction from committed configurations, code, reports, and experiment logs. No authentic submission was executed. “Observed” below means a value recorded in a stored project output; it does not mean the source workbook or functional-filter output was independently rechecked.

## 1. Dataset and provenance

The ingestion code expects `research-notes/data-identification/cs1_labs_responses.xlsx`, with `Lab N` worksheets, `Response Q` submission columns, and optional `Right answer Q` reference columns. It skips blank responses and assigns a row-based internal identifier (`services/authentic/ingestion.py`, `load_task_submissions`). The workbook and `cs1_regeneration_task_groups.json` mapping are absent from this checkout; the entire `research-notes/data-identification/` directory is Git-ignored. The functional-filter CSVs and summary expected under `outputs/authentic-functional-filter/` are also absent; `outputs/` is Git-ignored (`.gitignore`). **Not verified:** institution, course cohort, collection dates, number of unique students, original row totals, authorisation/consent/ethics approval, or whether source answers were altered.

The retained task-report index maps **46 lab questions** to prototype families: 20 T1, 19 T2, and 7 T3 (`research-notes/authentic-submission-outputs/task-report-index.json`). A read-only comparison found exactly one test plan for every indexed lab question, with no missing or extra plan. Its `direct` and `supporting` roles are stored labels, not evidence that any lab question asked for the exact prototype function. The authentic test plans call **none** of `classify_temperature`, `total_scores`, or `sum_to_n` (`research-notes/functional-tests/authentic_test_cases.json`). The prototype contracts use those three functions (`config/generation_configuration.json`; `research-notes/task-def-yaml/`). An older narrative calls T1 a score-classification task (`research-notes/programming-task-definitions.md`), while the current prototype config calls it temperature classification. Thus the authentic questions are **comparable task themes**, not verified exact task matches. **Not verified:** the rationale and full question text behind each direct/supporting decision, because the mapping file is absent.

| Prototype theme and contract | Mapped lab questions | Direct / supporting | Functionally correct and parseable in stored reports | Test-plan modes |
|---|---:|---:|---:|---|
| T1 conditional logic, `classify_temperature(temp)` | 20 | 10 / 10 | 10,778 | 15 script, 4 function, 1 structured |
| T2 list processing, `total_scores(scores)` | 19 | 8 / 11 | 10,756 | 3 script, 16 function |
| T3 numeric iteration, `sum_to_n(n)` | 7 | 5 / 2 | 3,859 | 4 script, 3 function |
| **Total** | **46** | **23 / 23** | **25,393** | **22 script, 23 function, 1 structured** |

The 25,393 count is the sum of `submissions.parseable_count` in the 46 retained `task-reports/*.json`; each also reports `parse_failure_count: 0` among rows supplied to prevalence analysis. The reports label the same rows `functionally_correct_count`. The task-family counts are **post-filter denominators**, not available or selected pre-filter counts. A separate detector-review metadata file reports 28,960 nonblank mapped submissions and 986 parse failures (`research-notes/detector-validation/authentic-detector-review.meta.json`), but that is a different review workflow, includes an 18-detector catalogue, and is not a retained functional-validation outcome. Do not divide 25,393 by 28,960 as a verified functional pass rate.

## 2. Selection and functional validation

The configured selection process enumerates every label in the missing grouping JSON and loads nonblank `Response Q` cells for each mapped lab question (`services/authentic/filter.py`, `_task_catalog`, `run_authentic_filter`; `services/authentic/ingestion.py`, `load_task_submissions`). There is no visible sampling step or duplicate check in this path. **Not verified:** how the 46 questions were originally chosen, whether duplicate source responses or repeated student attempts occur, or how many blank/unmapped submissions were left out.

The actual validator has three modes (`services/authentic/functional_validation.py`, `validate_authentic_source`; `services/authentic/validation_runner.py`, `execute`): script output comparison with a right-answer program; function return value **and captured stdout** comparison with the right-answer function; and structured-answer parsing/comparison. The 46 reference-derived plans contain 78 script cases, 63 function cases, and one structured task without executable cases (`research-notes/functional-tests/authentic_test_cases.json`). All configured cases must pass for status `PASS`; `run_authentic_filter` writes only PASS rows to `functionally_correct_submissions.csv`. A top-level exception fails the remaining cases; no result/invalid JSON fails; parent subprocess timeout is five seconds and fails. The structured mode compares parsed values directly without executing student code. This is a local subprocess in a temporary working directory, **not a demonstrated security sandbox**: the runner uses Python `exec`, and the source code does not show resource or permission isolation beyond timeout and temporary directory. The absent input files and the untrusted-code risk are why this audit did not rerun it.

| Theme | Available nonblank submissions | Selected for functional testing | Tested | PASS | FAIL | Functional pass rate | AST analysed after PASS | Excluded after PASS |
|---|---|---|---|---|---|---|---:|---:|
| T1 | Not verified | Not verified | Not verified | 10,778 reported | Not verified | Not verified | 10,778 reported | 0 parse failures reported |
| T2 | Not verified | Not verified | Not verified | 10,756 reported | Not verified | Not verified | 10,756 reported | 0 parse failures reported |
| T3 | Not verified | Not verified | Not verified | 3,859 reported | Not verified | Not verified | 3,859 reported | 0 parse failures reported |

Functional failures, their reasons, and per-theme pass rates cannot be reconstructed from the retained outputs. The code's summary would contain those fields, but code capability does not prove their realised values.

## 3. Detector method and classification

The 17 active research detectors are registered in `detectors/research/registry.py` and specified in `config/defect_specifications.json`. The latter supplies explicit category and eligibility assignments; a detector's ability to execute on source from another theme does **not** change its assigned category. `services/research/eligibility.py` applies the matrix. The prevalence runner executes raw detectors on every parseable PASS row, then counts only task-eligible results (`services/research/prevalence_runner.py`, `_task_report`, `run_prevalence_reports`). Formatting is token/source based; the catalogue is therefore AST **and token** detection rather than purely AST detection. Rules and exclusions are operational proxies for code-quality characteristics, not evidence of student intent.

| ID | Detector and category | Eligible theme(s) | Operational positive rule (condensed) |
|---|---|---|---|
| T1_D1 | `redundant_if_else`, dependent | T1 | `if/else` directly returns opposite Boolean constants. |
| T1_D2 | `redundant_comparison`, dependent | T1 | Proven Boolean expression compared with `True`/`False`. |
| T1_D3 | `redundant_not`, dependent | T1 | `not` directly wraps one safely invertible comparison. |
| T1_D4 | `duplicate_if`, dependent | T1 | Adjacent `if/elif` bodies are structurally equivalent and combinable. |
| T1_D5 | `else_if`, dependent | T1 | `else` contains only a nested `if` with no meaningful wrapper. |
| T1_D6 | `nested_if`, dependent | T1 | Nested conditions can safely be joined without changed behavior. |
| T1_D7 | `redundant_elif`, dependent | T1 | Preceding branches prove the `elif` condition when reached. |
| T1_D8 | `empty_if`, dependent | T1 | One branch contains only `pass`; alternative has meaningful behavior. |
| T2_D1 | `redundant_indexing`, dependent | T2 | Loop index serves only to read the matching sequence item. |
| T2_D2 | `misleading_iterator_name`, dependent | T2 | An index-style name such as `i` directly binds collection elements. |
| T2_D3 | `duplicate_expression`, dependent | T2 | Pure equivalent expression repeats nearby above the configured complexity threshold. |
| T3_D1 | `while_as_for`, dependent | T3 | Counter-controlled `while` has safe constant progression on every path. |
| TD_ASSIGN_01 | `augmentable_assignment`, dependent | T2, T3 | `x = x op value` can safely use the equivalent augmented assignment. |
| TI_FORMAT_01 | `inappropriate_formatting`, independent | T1–T3 | Valid Python violates a listed whitespace/token rule. |
| TI_LITERAL_01 | `magic_number`, independent | T1–T3 | Nonexempt, meaningful numeric literal appears in decision/domain logic. |
| TI_NAME_01 | `one_letter_name`, independent | T1–T3 | Short binding is neither task imposed nor allowed by its role. |
| TI_NAME_02 | `built_in_name`, independent | T1–T3 | A binding shadows a configured Python built-in. |

These descriptions condense `config/defect_specifications.json`; that file also documents exclusions, false-positive risks, source/AST requirements, and opportunity levels. `redundant_for` is experimental: it remains in `detectors/research/iteration.py` but is absent from the active registry and profile, with no positive authentic examples reported (`detectors/research/README.md`; `research-notes/detector-validation/README.md`). `scripts/realign_excluded_defects.py` can remove this detector from stored outputs and re-export the target. This explains a possible route from the review metadata's 18 detectors to the active profile's 17, but **whether and when that script ran is not verified**. Legacy detector files under `detectors/legacy/` and categories in `data/demonstration_profiles.json` are not part of these empirical estimates.

### Validation status and limits

The stored controlled-fixture report records 34/34 passing positive/negative cases for 17 detectors (`research-notes/detector-validation/controlled-fixture-report.json`). The stored manual-validation report labels 15 detectors `validated` and two (`empty_if`, `redundant_not`) `pilot_validated`, with zero recorded FP/FN (`research-notes/detector-validation/manual-validation-report.json`). The 1,332 stored gold-label rows retain 16 human reviewer tags, 947 “Codex AI first pass” tags, and 369 “Codex first-pass review” tags; every final label equals its detector label. **Researcher clarification (24 October 2026):** the reviewer tags were not consistently updated, and the researcher personally reviewed only a subset, estimated as “a couple of ten” cases (approximately 20), not all 1,332. The exact count and selection method are **Not verified**. Whether those decisions were made independently of detector predictions, and whether disagreements were adjudicated, is also **Not verified**. The stored perfect metrics are therefore agreement with the recorded labels, largely AI first-pass labels; they should not be cited as independently human-validated precision or recall. The 17 named rules also omit other possible novice defects by design.

**Read-only rerun on 24 October 2026:** the gold-label JSONL contains source text for 1,308 distinct submissions across 1,332 detector-case rows, but no reference solutions. Running the current static research detector for each case reproduced all **1,292/1,292** stored detector labels for registered defects. The other 40 rows concern `redundant_for`, which is no longer in the active registry, so they were excluded from this comparison. This checks detector-label reproducibility on the selected cases; it does not validate the labels against independent human judgement, rerun functional tests, or reproduce the 25,393-submission prevalence analysis. No student source was executed.

## 4. Profile construction and results

For each authentic lab question and eligible detector, stored prevalence is `affected_submission_count / eligible_denominator`, with one Boolean presence per parseable PASS submission. `raw_instance_count` is a separate occurrence metric and is **not** the numerator (`services/research/prevalence_runner.py`, `_task_report`; `services/research/prevalence.py`, `task_prevalence`). The cross-question **experimental target** is then the arithmetic mean of each eligible lab question's prevalence, assigning each lab question equal weight (`services/research/target_profile.py`, `build_empirical_target_profile`). The pooled submission prevalence, `sum(affected) / sum(eligible)`, is retained as a secondary estimator. These estimators differ because task counts differ.

The table compares the pooled **authentic observed** prevalence specified in the attachment with the **configured experimental target**. The complete 51 task-detector combinations, including structural N/A entries, are in `authentic_student_profile_summary.csv`. “Empirically derived but transformed” describes the target's equal-question averaging of detector estimates; it does not imply manual editing. Values were recalculated from `prototype-task-detection-summary.json` and matched against `empirical-target-profile.json` for all 26 eligible task-detector pairs. Percentages are rounded here to two decimals; the CSV retains six.

| Task | Detector | Eligible | Detected | Pooled observed % | Experimental target % |
|---|---|---:|---:|---:|---:|
| T1 | redundant_if_else | 10,778 | 104 | 0.96 | 1.13 |
| T1 | redundant_comparison | 10,778 | 48 | 0.45 | 0.47 |
| T1 | redundant_not | 10,778 | 11 | 0.10 | 0.10 |
| T1 | duplicate_if | 10,778 | 94 | 0.87 | 0.94 |
| T1 | else_if | 10,778 | 157 | 1.46 | 1.44 |
| T1 | nested_if | 10,778 | 18 | 0.17 | 0.17 |
| T1 | redundant_elif | 10,778 | 101 | 0.94 | 0.86 |
| T1 | empty_if | 10,778 | 14 | 0.13 | 0.14 |
| T1 | inappropriate_formatting | 10,778 | 5,715 | 53.02 | 55.01 |
| T1 | magic_number | 10,778 | 5,930 | 55.02 | 54.07 |
| T1 | one_letter_name | 10,778 | 1,136 | 10.54 | 10.75 |
| T1 | built_in_name | 10,778 | 129 | 1.20 | 1.15 |
| T2 | redundant_indexing | 10,756 | 332 | 3.09 | 3.04 |
| T2 | misleading_iterator_name | 10,756 | 1,149 | 10.68 | 10.64 |
| T2 | duplicate_expression | 10,756 | 1,593 | 14.81 | 14.63 |
| T2 | augmentable_assignment | 10,756 | 99 | 0.92 | 0.92 |
| T2 | inappropriate_formatting | 10,756 | 5,678 | 52.79 | 53.07 |
| T2 | magic_number | 10,756 | 3,006 | 27.95 | 27.74 |
| T2 | one_letter_name | 10,756 | 1,739 | 16.17 | 16.16 |
| T2 | built_in_name | 10,756 | 359 | 3.34 | 3.33 |
| T3 | while_as_for | 3,859 | 195 | 5.05 | 4.73 |
| T3 | augmentable_assignment | 3,859 | 78 | 2.02 | 2.05 |
| T3 | inappropriate_formatting | 3,859 | 2,251 | 58.33 | 59.46 |
| T3 | magic_number | 3,859 | 1,630 | 42.24 | 40.93 |
| T3 | one_letter_name | 3,859 | 1,027 | 26.61 | 29.40 |
| T3 | built_in_name | 3,859 | 760 | 19.69 | 18.24 |

The largest displayed estimator difference is T3 `one_letter_name` (26.61% pooled versus 29.40% target). This is a weighting difference, not evidence of undocumented manual adjustment. `config/defect_specifications.json` marks structurally inapplicable defects `not_applicable`; they are omitted from target profiles and represented as **N/A**, distinct from an eligible detector with zero observed cases. The task-independent/dependent split is an explicit catalogue classification based on structural opportunity and researcher-defined task context. **Not verified:** a quantitative cross-task recurrence test or prespecified statistical rule used to assign that classification from these submissions.

## 5. Link to experiments

`scripts/run_generation_experiment.py` defaults to the retained `empirical-target-profile.json` and passes its task-specific target values to `ExperimentConfig`. `services/generation/experiment.py`, `run_experiment`, uses that same `config.target_profile` for baseline, task-aware non-adaptive, and task-aware iterative runs; iteration changes constraints, not the target. In `services/generation/workflow.py`, `run_iteration`, the baseline receives a baseline prompt without target guidance but is evaluated against the same target; the two task-aware conditions use the target in generation guidance. I read all 13 retained experiment records in 12 JSONL files under `research-notes/synthetic-generation-experiments/`: 7 T1, 3 T2, 3 T3. All list the three conditions, and all recorded configuration targets match the retained empirical profile exactly, with no missing or additional defect keys. All 770 available per-iteration comparison targets also match; five older iterations lack per-iteration comparison entries. The logs demonstrate actual use of those values in recorded runs; they do not prove the missing raw-data pipeline was reproducible. The profile file labels itself `preliminary_raw_detector_estimates`.

`data/demonstration_profiles.json` contains illustrative values for an older two-task demo (`conditional_validation`, `list_processing`); `requirement.md` explicitly allows labelled demonstration values. Those values do **not** correspond to the logged T1/T2/T3 empirical targets and must not be reported as empirical findings.

## 6. Reliability and validity assessment

**Confirmed limitations:** original workbook, mapping JSON, and functional-filter results are missing; per-theme available/tested/fail counts and pass rates cannot be audited; detector frequencies are restricted to parseable PASS submissions; stored targets use equal-question means rather than pooled submission prevalence; direct/supporting tasks are not the exact prototype functions; T3 has fewer questions and fewer PASS rows than T1/T2; two detectors are below the pilot's minimum positive-review count; the researcher reports human review of only roughly 20 of 1,332 stored label cases; the report files themselves include row-derived IDs and detector evidence and should remain access controlled. The report generated here contains only aggregates.

**Potential threats requiring further evidence:** nonrandom question selection, repeated or copied submissions, domain/task mismatch within the broad families, reference-solution errors or inadequate functional cases, hidden exceptions/timeouts among failed submissions, false positives/negatives in detectors, nonrepresentative prevalence outside this cohort, and whether label review was independent of detector predictions. These are not asserted as observed problems. Missing provenance and authorisation prevent a full academic data-governance statement; missing source and filter files prevent an end-to-end rerun from this checkout. The missing-information checklist gives specific recovery steps.

## 7. Evidence map

| Stage | Project evidence | What it establishes |
|---|---|---|
| Workbook ingestion | `services/authentic/ingestion.py` | Expected workbook schema, blank-response skipping, row-to-submission handling. |
| Mapping | `research-notes/authentic-submission-outputs/task-report-index.json` | Retained 46 labels, family and direct/supporting roles; original mapping JSON absent. |
| Functional test plans | `research-notes/functional-tests/authentic_test_cases.json` | 46 reference-derived test modes and cases. |
| Functional execution | `services/authentic/functional_validation.py`; `services/authentic/validation_runner.py`; `services/authentic/filter.py` | PASS semantics, timeout/failure handling, intended all/PASS CSV writes. |
| Defect rules | `config/defect_specifications.json`; `detectors/research/registry.py`; `detectors/research/*.py` | 17 active names, operational rules, eligibility and implemented detection. |
| Detector review | `research-notes/detector-validation/{controlled-fixture-report.json,manual-validation-report.json,authentic-detector-review.meta.json,authentic-detector-gold-labels.jsonl}` | Fixture results and reported scoring; researcher estimates human review of about 20 cases; source material in the JSONL is confidential. |
| Prevalence | `services/research/prevalence_runner.py`; `research-notes/authentic-submission-outputs/{task-reports/,prototype-task-detection-summary.json}` | Actual stored counts and two estimators. |
| Target export | `services/research/target_profile.py`; `research-notes/authentic-submission-outputs/empirical-target-profile.json` | Equal-question target transformation and retained values. |
| Experimental use | `scripts/run_generation_experiment.py`; `services/generation/experiment.py`; `research-notes/synthetic-generation-experiments/experiment-log*.jsonl` | Target loading, shared-condition use, recorded target matches. |
