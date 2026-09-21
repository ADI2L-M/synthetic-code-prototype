import json
from pathlib import Path
from typing import Any

from models.types import ProgrammingTask, TestCase

ROOT = Path(__file__).resolve().parents[1]


def _read_json(name: str) -> Any:
    with (ROOT / "data" / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_tasks() -> list[ProgrammingTask]:
    return [
        ProgrammingTask(
            id=item["id"], name=item["name"], description=item["description"],
            function_name=item["function_name"], contexts=item["contexts"],
            functional_requirements=item["functional_requirements"],
            test_cases=[TestCase(**case) for case in item["test_cases"]],
        )
        for item in _read_json("tasks.json")
    ]


def load_profiles() -> dict[str, Any]:
    return _read_json("demonstration_profiles.json")
