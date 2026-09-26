"""Generation-ready task contracts for the empirical prototype families."""

from __future__ import annotations

from functools import cache

from models.types import ProgrammingTask, TestCase


@cache
def load_prototype_tasks() -> dict[str, ProgrammingTask]:
    """Return the T1/T2/T3 contracts used by the synthetic generator."""
    return {
        "T1": ProgrammingTask(
            id="T1",
            name="T1 · Temperature Classification",
            description=(
                "Write classify_temperature(temp) to classify a Celsius "
                "temperature as cold, mild, or hot."
            ),
            function_name="classify_temperature",
            contexts=["T1", "conditional_logic", "branching"],
            functional_requirements=[
                "Accept one integer parameter named temp.",
                "Return 'cold' when temp is below 10.",
                "Return 'mild' when temp is from 10 through 24 inclusive.",
                "Return 'hot' when temp is 25 or above.",
                "Return the category as a string without printing it.",
            ],
            test_cases=[
                TestCase(args=[-1], expected="cold"),
                TestCase(args=[10], expected="mild"),
                TestCase(args=[24], expected="mild"),
                TestCase(args=[25], expected="hot"),
                TestCase(args=[100], expected="hot"),
            ],
        ),
        "T2": ProgrammingTask(
            id="T2",
            name="T2 · Total Scores",
            description=(
                "Write total_scores(scores) to calculate the total of all "
                "integer values in a list without using sum()."
            ),
            function_name="total_scores",
            contexts=["T2", "list_processing", "iteration", "collection"],
            functional_requirements=[
                "Accept a list of integers named scores.",
                "Return the total of every value in scores.",
                "Return 0 for an empty list.",
                "Do not use Python's built-in sum() function.",
                "Return the total as an integer without printing it.",
            ],
            test_cases=[
                TestCase(args=[[]], expected=0),
                TestCase(args=[[1, 2, 3]], expected=6),
                TestCase(args=[[-5, 4, 0]], expected=-1),
                TestCase(args=[[10, 10, 10, 10]], expected=40),
            ],
        ),
        "T3": ProgrammingTask(
            id="T3",
            name="T3 · Sum to N",
            description=(
                "Write sum_to_n(n) to calculate the sum of all integers "
                "from 1 through n using iteration."
            ),
            function_name="sum_to_n",
            contexts=["T3", "numeric_iteration", "iteration", "accumulation"],
            functional_requirements=[
                "Accept one positive integer parameter named n.",
                "Calculate the sum of all integers from 1 through n.",
                "Use iteration rather than a direct mathematical formula.",
                "Do not use Python's built-in sum() function.",
                "Return the total as an integer without printing it.",
            ],
            test_cases=[
                TestCase(args=[1], expected=1),
                TestCase(args=[5], expected=15),
                TestCase(args=[10], expected=55),
                TestCase(args=[25], expected=325),
            ],
        ),
    }


def load_prototype_task(task_id: str) -> ProgrammingTask:
    """Load one empirical prototype task by ID."""
    try:
        return load_prototype_tasks()[task_id]
    except KeyError as error:
        raise ValueError(f"Unknown prototype task: {task_id}") from error
