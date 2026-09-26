from services.generation.prompt_builder import build_generation_specification
from services.generation.prototype_tasks import load_prototype_tasks
from services.generation.workflow import run_iteration


class FakeProvider:
    def generate(self, task, batch_size, iteration=1, specification=None):
        source = {
            "T1": "def classify_temperature(temp):\n    if temp < 10:\n        return 'cold'\n    if temp < 25:\n        return 'mild'\n    return 'hot'\n",
            "T2": "def total_scores(scores):\n    total = 0\n    for score in scores:\n        total += score\n    return total\n",
            "T3": "def sum_to_n(n):\n    total = 0\n    for value in range(1, n + 1):\n        total += value\n    return total\n",
        }[task.id]
        return [source] * batch_size


class RecordingProvider(FakeProvider):
    def __init__(self):
        self.calls = []

    def generate(self, task, batch_size, iteration=1, specification=None):
        self.calls.append((task.id, batch_size, iteration, specification))
        return super().generate(task, batch_size, iteration, specification)


def test_prototype_tasks_cover_all_empirical_generation_families():
    tasks = load_prototype_tasks()

    assert set(tasks) == {"T1", "T2", "T3"}
    assert tasks["T1"].function_name == "classify_temperature"
    assert tasks["T2"].function_name == "total_scores"
    assert tasks["T3"].function_name == "sum_to_n"


def test_generation_workflow_uses_research_detectors_for_empirical_targets():
    target = {"augmentable_assignment": 0.0, "one_letter_name": 0.0}
    result = run_iteration(
        task=load_prototype_tasks()["T3"],
        target_profile=target,
        batch_size=2,
        iteration_number=1,
        tolerance=0.1,
        provider=FakeProvider(),
    )

    assert len(result.submissions) == 2
    assert all(
        submission.validation.status == "PASS" for submission in result.submissions
    )
    assert set(result.observed_profile) == set(target)


def test_generation_uses_one_reproducible_guidance_brief_per_submission():
    provider = RecordingProvider()
    result = run_iteration(
        task=load_prototype_tasks()["T3"],
        target_profile={"one_letter_name": 0.5},
        batch_size=4,
        iteration_number=1,
        tolerance=0.1,
        provider=provider,
    )

    assert len(provider.calls) == 4
    assert all(call[1] == 1 for call in provider.calls)
    assert all("ASSIGNED DEFECT STYLE BRIEFS" in call[3] for call in provider.calls)
    assert any("Defective pattern example:" in call[3] for call in provider.calls)
    assert any("Corrected contrast:" in call[3] for call in provider.calls)
    assert all(item.prompt for item in result.submissions)
    assert all(item.generation_seed is not None for item in result.submissions)
    assert result.planned_assignment_counts["one_letter_name"] in {2, 3}


def test_submission_prompt_contains_only_assigned_defect_guidance():
    provider = RecordingProvider()
    run_iteration(
        task=load_prototype_tasks()["T1"],
        target_profile={
            "redundant_not": 1.0,
            "built_in_name": 0.0,
        },
        batch_size=1,
        iteration_number=1,
        tolerance=0.1,
        provider=provider,
    )

    prompt = provider.calls[0][3]
    assert "DEFECT: redundant not" in prompt
    assert "TASK-DEPENDENT DEFECT FOCUS" in prompt
    assert "Defective pattern example:" in prompt
    assert "built in name" not in prompt
    assert "100% target" not in prompt


def test_programming_task_brief_redacts_prevalence_and_lists_task_dependent_defects():
    brief = build_generation_specification(
        load_prototype_tasks()["T1"],
        {"magic_number": 0.54, "redundant_not": 0.01},
    )

    assert "POTENTIAL TASK-DEPENDENT DEFECTS" in brief
    assert "redundant not" in brief
    assert "magic number" not in brief
    assert "%" not in brief
