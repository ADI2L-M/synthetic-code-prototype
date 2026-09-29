import pytest

from detectors.core.registry import detect_defects
from models.types import IterationResult, SubmissionResult, ValidationResult
from services.data.loader import load_profiles, load_tasks
from services.data.profile_composer import compose_target_profile
from services.generation.analysis import (
    compare_profiles,
    observed_profile,
    wilson_interval,
)
from services.generation.calibrator import (
    calibration_constraints,
    calibration_is_non_regressive,
    calibration_regression_message,
)
from services.generation.validator import validate_source
from services.generation.workflow import run_iteration
import services.generation.workflow as generation_workflow
from services.providers.demo import DemoProvider


def test_task_profiles_are_context_aware():
    tasks = load_tasks()
    independent, dependent, target = compose_target_profile(tasks[0], load_profiles())
    assert independent and dependent
    assert set(target) == set(independent) | set(dependent)
    assert "redundant_boolean_comparison" in dependent


def test_demo_generation_validates_and_detects_defects():
    task = load_tasks()[0]
    source = DemoProvider().generate(task, 2)[1]
    result = validate_source(source, task)
    assert result.status == "PASS"
    assert detect_defects(source, ["redundant_boolean_comparison"])[
        "redundant_boolean_comparison"
    ]


def test_validator_rejects_unsafe_source_before_subprocess_execution():
    task = load_tasks()[0]
    source = (
        "import os\n"
        "def classify_score(score):\n"
        "    return os.getcwd()\n"
    )

    result = validate_source(source, task)

    assert result.status == "FAIL"
    assert "Unsafe source rejected" in result.failure_message


def test_validator_times_out_non_terminating_generated_code():
    task = load_tasks()[0]
    source = (
        "def classify_score(score):\n"
        "    while True:\n"
        "        pass\n"
    )

    result = validate_source(source, task, timeout_seconds=1)

    assert result.status == "FAIL"
    assert result.timed_out is True


def test_detector_exception_is_not_silently_converted_to_prevalence(monkeypatch):
    task = load_tasks()[0]

    def detector_failure(*args, **kwargs):
        raise RuntimeError("detector failure")

    monkeypatch.setattr(generation_workflow, "detect_research_defects", detector_failure)

    with pytest.raises(RuntimeError, match="detector failure"):
        run_iteration(
            task=task,
            target_profile={"magic_number": 0.1},
            batch_size=1,
            iteration_number=1,
            tolerance=0.1,
            provider=DemoProvider(),
        )


def test_failed_submissions_are_excluded_from_denominator():
    task = load_tasks()[0]
    passed = validate_source(DemoProvider().generate(task, 1)[0], task)
    failed = validate_source("def classify_score(score):\n    return 'wrong'", task)
    submissions = [
        SubmissionResult(1, "", passed, {"unused_variable": True}),
        SubmissionResult(2, "", failed, {}),
    ]
    assert observed_profile(submissions, ["unused_variable"])["unused_variable"] == 1.0


def test_comparison_and_tolerance_actions():
    rows = compare_profiles(
        {"a": 0.4, "b": 0.1, "c": 0.1}, {"a": 0.1, "b": 0.105, "c": 0.1}, 0.1
    )
    assert rows[0].status == "Underrepresented"
    assert rows[1].status == "Within tolerance"
    assert rows[2].action == "Maintain"


def test_comparison_uses_target_relative_tolerance_for_rare_defects():
    rows = compare_profiles({"rare": 0.01}, {"rare": 0.0}, 0.10)

    assert rows[0].status == "Underrepresented"
    assert rows[0].difference == 0.01


def test_sampling_aware_comparison_records_counts_and_wilson_interval():
    rows = compare_profiles(
        {"defect": 0.5},
        {"defect": 2 / 9},
        0.10,
        observed_denominator=9,
        target_standard_errors={"defect": 0.10},
        observed_counts_by_defect={"defect": 2},
    )

    row = rows[0]
    assert row.observed_count == 2
    assert row.observed_denominator == 9
    assert row.observed_interval_low == wilson_interval(2, 9)[0]
    assert row.observed_interval_high == wilson_interval(2, 9)[1]
    assert row.status == "Within tolerance"


def test_sampling_aware_comparison_can_still_identify_large_gap():
    rows = compare_profiles(
        {"defect": 0.5},
        {"defect": 0.0},
        0.10,
        observed_denominator=100,
        target_standard_errors={"defect": 0.0},
        observed_counts_by_defect={"defect": 0},
    )

    assert rows[0].status == "Underrepresented"


def test_sampling_aware_comparison_does_not_treat_zero_count_as_certain():
    rows = compare_profiles(
        {"defect": 0.01},
        {"defect": 0.0},
        0.10,
        observed_denominator=10,
        target_standard_errors={"defect": 0.0},
        observed_counts_by_defect={"defect": 0},
    )

    assert rows[0].status == "Within tolerance"


def test_iteration_snapshots_task_target_tolerance_and_constraints():
    task = load_tasks()[0]
    _, _, target = compose_target_profile(task, load_profiles())
    constraints = {"unused_variable": "strengthen the generation constraint"}

    iteration = run_iteration(
        task=task,
        target_profile=target,
        batch_size=3,
        iteration_number=2,
        tolerance=0.15,
        constraints=constraints,
    )

    assert iteration.task_id == task.id
    assert iteration.task_name == task.name
    assert iteration.target_profile == target
    assert iteration.target_profile is not target
    assert iteration.tolerance == 0.15
    assert iteration.constraints == constraints
    assert iteration.iteration == 2
    assert len(iteration.submissions) == 3


def test_calibration_changes_constraints_not_target_profile():
    task = load_tasks()[0]
    _, _, target = compose_target_profile(task, load_profiles())
    original_target = dict(target)
    iteration = run_iteration(task, target, 2, 1, 0.10)

    constraints = calibration_constraints(iteration.comparison)

    assert target == original_target
    assert set(constraints) == set(target)


def _quality_iteration(
    *,
    pass_count: int,
    independent_count: int,
    dependent_count: int,
) -> IterationResult:
    submissions = []
    for submission_id in range(1, 3):
        valid = submission_id <= pass_count
        submissions.append(
            SubmissionResult(
                submission_id=submission_id,
                source_code="",
                validation=ValidationResult(
                    status="PASS" if valid else "FAIL",
                    tests_passed=1 if valid else 0,
                    tests_failed=0 if valid else 1,
                ),
                defects={
                    "unused_variable": submission_id <= independent_count,
                    "augmentable_assignment": submission_id <= dependent_count,
                },
                category_requirements_met=(
                    valid
                    and submission_id <= independent_count
                    and submission_id <= dependent_count
                ),
            )
        )
    return IterationResult(
        iteration=1,
        task_id="T1",
        task_name="Test task",
        target_profile={
            "unused_variable": 0.5,
            "augmentable_assignment": 0.5,
        },
        tolerance=0.1,
        constraints={},
        specification="",
        submissions=submissions,
        observed_profile={},
        comparison=[],
    )


def test_calibration_rejects_regression_in_mandatory_category_coverage():
    previous = _quality_iteration(
        pass_count=2,
        independent_count=2,
        dependent_count=2,
    )
    candidate = _quality_iteration(
        pass_count=2,
        independent_count=2,
        dependent_count=1,
    )

    assert calibration_is_non_regressive(previous, candidate) is False
    assert "task-dependent coverage" in calibration_regression_message(
        previous, candidate
    )


def test_calibration_allows_equal_or_better_quality():
    previous = _quality_iteration(
        pass_count=1,
        independent_count=1,
        dependent_count=1,
    )
    candidate = _quality_iteration(
        pass_count=2,
        independent_count=2,
        dependent_count=2,
    )

    assert calibration_is_non_regressive(previous, candidate) is True
