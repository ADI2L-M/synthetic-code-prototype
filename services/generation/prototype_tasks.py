"""Generation-ready task contracts for the empirical prototype families."""

from __future__ import annotations

from functools import cache

from models.types import ProgrammingTask, TestCase
from services.generation.configuration import load_generation_configuration


@cache
def load_prototype_tasks() -> dict[str, ProgrammingTask]:
    """Return the T1/T2/T3 contracts used by the synthetic generator."""
    configured_tasks = load_generation_configuration()["prototype_tasks"]
    return {
        task_id: ProgrammingTask(
            id=task_id,
            name=task["name"],
            description=task["description"],
            function_name=task["function_name"],
            contexts=list(task["contexts"]),
            functional_requirements=list(task["functional_requirements"]),
            test_cases=[TestCase(**case) for case in task["test_cases"]],
        )
        for task_id, task in configured_tasks.items()
    }


def load_prototype_task(task_id: str) -> ProgrammingTask:
    """Load one empirical prototype task by ID."""
    try:
        return load_prototype_tasks()[task_id]
    except KeyError as error:
        raise ValueError(f"Unknown prototype task: {task_id}") from error
