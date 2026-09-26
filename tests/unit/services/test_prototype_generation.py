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
