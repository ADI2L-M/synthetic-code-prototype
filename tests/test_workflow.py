from detectors.all import detect_defects
from models.types import SubmissionResult
from services.analysis import compare_profiles, observed_profile
from services.data_loader import load_profiles, load_tasks
from services.demo_provider import DemoProvider
from services.profile_composer import compose_target_profile
from services.validator import validate_source


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
    assert detect_defects(source, ["redundant_boolean_comparison"])["redundant_boolean_comparison"]


def test_failed_submissions_are_excluded_from_denominator():
    task = load_tasks()[0]
    passed = validate_source(DemoProvider().generate(task, 1)[0], task)
    failed = validate_source("def classify_score(score):\n    return 'wrong'", task)
    submissions = [SubmissionResult(1, "", passed, {"unused_variable": True}), SubmissionResult(2, "", failed, {})]
    assert observed_profile(submissions, ["unused_variable"])["unused_variable"] == 1.0


def test_comparison_and_tolerance_actions():
    rows = compare_profiles({"a": 0.4, "b": 0.1, "c": 0.1}, {"a": 0.1, "b": 0.2, "c": 0.1}, 0.1)
    assert rows[0]["status"] == "Underrepresented"
    assert rows[1]["status"] == "Within tolerance"
    assert rows[2]["action"] == "Maintain"
