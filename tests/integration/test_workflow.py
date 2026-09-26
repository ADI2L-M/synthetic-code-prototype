from detectors.core.registry import detect_defects
from models.types import SubmissionResult
from services.generation.analysis import compare_profiles, observed_profile
from services.generation.calibrator import calibration_constraints
from services.data.loader import load_profiles, load_tasks
from services.providers.demo import DemoProvider
from services.data.profile_composer import compose_target_profile
from services.generation.validator import validate_source
from services.generation.workflow import run_iteration


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
