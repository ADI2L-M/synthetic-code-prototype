import json
from datetime import datetime, timezone

import pytest

import services.generation.experiment as experiment_module
from models.types import (
    IterationResult,
    ProfileComparison,
    SubmissionResult,
    ValidationResult,
)
from services.generation.experiment import (
    BASELINE_CONDITION,
    ITERATIVE_CONDITION,
    TASK_AWARE_CONDITION,
    ExperimentConfig,
    experiment_log_path,
    load_experiment_logs,
    run_experiment,
)
from services.generation.prototype_tasks import load_prototype_tasks
from services.generation.workflow import run_iteration


def _synthetic_iteration(iteration_number: int, error: float) -> IterationResult:
    return IterationResult(
        iteration=iteration_number,
        task_id="T1",
        task_name="Temperature Classification",
        target_profile={
            "magic_number": 0.5,
            "redundant_comparison": 0.5,
        },
        tolerance=0.1,
        constraints={},
        specification="",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="def classify_temperature(temp): return 'cold'",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": True, "redundant_comparison": True},
                category_requirements_met=True,
            )
        ],
        observed_profile={"magic_number": 0.5, "redundant_comparison": 0.5},
        comparison=[
            ProfileComparison(
                defect="magic_number",
                target=0.5,
                observed=0.5 + error,
                difference=error,
                status="Within tolerance" if abs(error) <= 0.1 else "Underrepresented",
                action="Maintain" if abs(error) <= 0.1 else "Increase",
            )
        ],
        condition=ITERATIVE_CONDITION,
    )


class ConventionalProvider:
    def generate(self, task, batch_size, iteration=1, specification=None):
        source = {
            "T1": (
                "def classify_temperature(temp):\n"
                "    if temp < 10:\n"
                "        return 'cold'\n"
                "    if temp < 25:\n"
                "        return 'mild'\n"
                "    return 'hot'\n"
            ),
            "T2": (
                "def total_scores(scores):\n"
                "    total = 0\n"
                "    for score in scores:\n"
                "        total += score\n"
                "    return total\n"
            ),
            "T3": (
                "def sum_to_n(n):\n"
                "    total = 0\n"
                "    for value in range(1, n + 1):\n"
                "        total += value\n"
                "    return total\n"
            ),
        }[task.id]
        return [source] * batch_size


def test_experiment_log_path_uses_requested_timestamp_format():
    path = experiment_log_path(datetime(2026, 9, 29, 12, 34, 56, tzinfo=timezone.utc))

    assert path.name == "experiment-log-290926123456.jsonl"


def test_baseline_condition_uses_task_only_prompt_and_no_assignments():
    result = run_iteration(
        task=load_prototype_tasks()["T1"],
        target_profile={"built_in_name": 0.1},
        batch_size=1,
        iteration_number=1,
        tolerance=0.10,
        provider=ConventionalProvider(),
        condition=BASELINE_CONDITION,
    )

    submission = result.submissions[0]
    assert result.condition == BASELINE_CONDITION
    assert submission.assigned_defects == ()
    assert "PROMPTING CONDITION: NON-ADAPTIVE BASELINE" in submission.prompt
    assert "MANDATORY CATEGORY REQUIREMENT" not in submission.prompt
    assert submission.category_requirements_met is True


def test_experiment_compares_conditions_and_appends_compact_jsonl(tmp_path):
    log_path = tmp_path / "experiment-log.jsonl"
    config = ExperimentConfig(
        experiment_id="test-experiment",
        task_id="T1",
        target_profile={"built_in_name": 0.1},
        batch_size=1,
        temperature=0.35,
        conditions=(
            BASELINE_CONDITION,
            TASK_AWARE_CONDITION,
            ITERATIVE_CONDITION,
        ),
    )

    result = run_experiment(
        config,
        provider_factory=ConventionalProvider,
        log_path=log_path,
    )

    assert set(result.condition_summary) == {
        BASELINE_CONDITION,
        TASK_AWARE_CONDITION,
        ITERATIVE_CONDITION,
    }
    assert len(result.runs) == 3
    assert all(run.final_iteration.submissions for run in result.runs)
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 1

    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["record_type"] == "synthetic_generation_experiment"
    assert record["schema_version"] == 2
    assert record["config"]["temperature"] == 0.35
    assert record["config"]["max_repair_attempts"] == 2
    assert record["condition_summary"][BASELINE_CONDITION][
        "functional_pass_rate"
    ] == 1.0
    selected_run = next(
        run
        for run in record["runs"]
        if run["condition"] == BASELINE_CONDITION
    )
    assert selected_run["selected_out_of_tolerance"] == []
    assert selected_run["selected_zero_observed"] == [
        "built_in_name",
    ]
    comparison = selected_run["iterations"][0]["profile_comparison"]
    assert comparison[0]["defect"] == "built_in_name"
    assert comparison[0]["observed_count"] == 0
    assert comparison[0]["status"] == "Within tolerance"
    assert "source_code" not in log_path.read_text(encoding="utf-8")
    assert "prompt" not in log_path.read_text(encoding="utf-8")


def test_experiment_rejects_negative_repair_budget(tmp_path):
    config = ExperimentConfig(
        experiment_id="invalid",
        task_id="T1",
        target_profile={},
        max_repair_attempts=-1,
    )

    with pytest.raises(ValueError, match="max_repair_attempts"):
        run_experiment(config, ConventionalProvider, log_path=tmp_path / "log.jsonl")


def test_experiment_supports_repeated_runs_for_comparison(tmp_path):
    config = ExperimentConfig(
        experiment_id="repeated-experiment",
        task_id="T1",
        target_profile={"built_in_name": 0.1},
        batch_size=1,
        repetitions=2,
        conditions=(TASK_AWARE_CONDITION,),
    )

    result = run_experiment(
        config,
        provider_factory=ConventionalProvider,
        log_path=tmp_path / "log.jsonl",
    )

    assert len(result.runs) == 2
    assert {run.repetition for run in result.runs} == {1, 2}


def test_iterative_experiment_selects_best_eligible_iteration(monkeypatch, tmp_path):
    errors = iter((0.20, 0.15, 0.12))

    def fake_run_iteration(**kwargs):
        return _synthetic_iteration(kwargs["iteration_number"], next(errors))

    monkeypatch.setattr(experiment_module, "run_iteration", fake_run_iteration)
    config = ExperimentConfig(
        experiment_id="best-iteration",
        task_id="T1",
        target_profile={"magic_number": 0.5},
        max_iterations=3,
        conditions=(ITERATIVE_CONDITION,),
    )

    result = run_experiment(
        config,
        provider_factory=ConventionalProvider,
        log_path=tmp_path / "log.jsonl",
    )

    run = result.runs[0]
    assert len(run.iterations) == 3
    assert run.final_iteration.iteration == 3
    assert run.stop_reason == "maximum_iterations"


def test_task_aware_initial_iterations_use_matched_seed_namespace(monkeypatch, tmp_path):
    calls = []

    def fake_run_iteration(**kwargs):
        calls.append((kwargs["condition"], kwargs["iteration_number"], kwargs["seed_namespace"]))
        return _synthetic_iteration(kwargs["iteration_number"], 0.05)

    monkeypatch.setattr(experiment_module, "run_iteration", fake_run_iteration)
    config = ExperimentConfig(
        experiment_id="matched-seeds",
        task_id="T1",
        target_profile={"magic_number": 0.5},
        max_iterations=2,
        conditions=(TASK_AWARE_CONDITION, ITERATIVE_CONDITION),
    )

    run_experiment(config, provider_factory=ConventionalProvider, log_path=tmp_path / "log.jsonl")

    assert calls[0][:2] == (TASK_AWARE_CONDITION, 1)
    assert calls[1][:2] == (ITERATIVE_CONDITION, 1)
    assert calls[0][2] == calls[1][2]


def test_experiment_log_browser_skips_malformed_lines(tmp_path):
    path = tmp_path / "experiment-log-1.jsonl"
    path.write_text(
        "not-json\n"
        '{"record_type":"other"}\n'
        '{"record_type":"synthetic_generation_experiment",'
        '"experiment_id":"one","config":{"task_id":"T1"}}\n',
        encoding="utf-8",
    )

    records = load_experiment_logs(tmp_path)

    assert len(records) == 1
    assert records[0]["experiment_id"] == "one"
    assert records[0]["_log_file"] == path.name
