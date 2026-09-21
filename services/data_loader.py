import json
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

from models.types import DefectDefinition, ProgrammingTask, TestCase

ROOT = Path(__file__).resolve().parents[1]


@cache
def _read_json(name: str) -> Any:
    with (ROOT / "data" / name).open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_tasks() -> tuple[ProgrammingTask, ...]:
    return tuple(
        ProgrammingTask(
            id=item["id"],
            name=item["name"],
            description=item["description"],
            function_name=item["function_name"],
            contexts=item["contexts"],
            functional_requirements=item["functional_requirements"],
            test_cases=[TestCase(**case) for case in item["test_cases"]],
        )
        for item in _read_json("tasks.json")
    )


@lru_cache(maxsize=1)
def load_profiles() -> dict[str, Any]:
    return _read_json("demonstration_profiles.json")


@lru_cache(maxsize=1)
def load_defect_definitions() -> tuple[DefectDefinition, ...]:
    return tuple(
        DefectDefinition(
            id=item["id"],
            display_name=item["display_name"],
            classification=item["classification"],
            detector=item["detector"],
            description=item["description"],
            applicable_contexts=tuple(item.get("applicable_contexts", [])),
        )
        for item in _read_json("defect_repository.json")
    )


@lru_cache(maxsize=1)
def load_demo_submissions() -> dict[str, list[str]]:
    return _read_json("demo_submissions.json")
