from services.generation.configuration import (
    defect_names_by_category,
    generation_policy,
    load_generation_configuration,
)
from services.generation.prompt_builder import (
    DEFECT_REQUIRED_SIGNATURES,
    GENERATION_AVOIDANCE_HINTS,
    GENERATION_EXAMPLES,
    GENERATION_HINTS,
    TASK_INDEPENDENT_DEFECTS,
    TASK_SPECIFIC_PATTERNS,
)
from services.generation.prototype_tasks import load_prototype_tasks
from services.generation.workflow import (
    RELIABLE_DEFECT_ORDER,
    TASK_RELIABLE_DEFECT_ORDER,
)


def test_runtime_tasks_are_loaded_from_the_canonical_configuration():
    configured = load_generation_configuration()["prototype_tasks"]
    tasks = load_prototype_tasks()

    assert set(tasks) == set(configured) == {"T1", "T2", "T3"}
    for task_id, task in tasks.items():
        assert task.name == configured[task_id]["name"]
        assert task.function_name == configured[task_id]["function_name"]
        assert len(task.test_cases) == len(configured[task_id]["test_cases"])


def test_runtime_generation_policy_is_not_duplicated_in_python_constants():
    policy = generation_policy

    assert TASK_INDEPENDENT_DEFECTS == defect_names_by_category("task_independent")
    assert GENERATION_HINTS == policy("hints")
    assert GENERATION_AVOIDANCE_HINTS == policy("avoidance_hints")
    assert DEFECT_REQUIRED_SIGNATURES == policy("required_signatures")
    assert GENERATION_EXAMPLES == policy("examples")
    assert TASK_SPECIFIC_PATTERNS == {
        (task_id, defect): pattern
        for task_id, patterns in policy("task_specific_patterns").items()
        for defect, pattern in patterns.items()
    }
    assert RELIABLE_DEFECT_ORDER == policy("reliable_defect_order")
    assert TASK_RELIABLE_DEFECT_ORDER == policy("task_reliable_defect_order")
