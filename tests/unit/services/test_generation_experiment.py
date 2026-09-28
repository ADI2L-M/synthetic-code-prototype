import json
from datetime import datetime

import pytest

from services.generation.experiment import (
    BASELINE_CONDITION,
    ExperimentConfig,
    ITERATIVE_CONDITION,
    TASK_AWARE_CONDITION,
    experiment_log_path,
    run_experiment,
)
from services.generation.prototype_tasks import load_prototype_tasks
from services.generation.workflow import run_iteration


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
    path = experiment_log_path(datetime(2026, 9, 29, 12, 34, 56))

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
