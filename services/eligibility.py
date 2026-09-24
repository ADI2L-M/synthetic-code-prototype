import json
from pathlib import Path
from typing import Any

from models.research import Eligibility

_DEFAULT_SPECIFICATION = (
    Path(__file__).resolve().parents[1] / "config" / "defect_specifications.json"
)


def load_defect_specification(path: Path = _DEFAULT_SPECIFICATION) -> dict[str, Any]:
    with path.open(encoding="utf-8") as specification_file:
        return json.load(specification_file)


def eligibility_for(
    task_id: str,
    defect: str,
    specification: dict[str, Any] | None = None,
) -> Eligibility:
    specification = specification or load_defect_specification()
    matrix = specification.get("eligibility_matrix", {})
    task_matrix = matrix.get(task_id)
    if task_matrix is None:
        raise ValueError(f"Unknown research task: {task_id}")

    opportunity_level = task_matrix.get("opportunity_level", {}).get(defect, "normal")
    if defect in task_matrix.get("eligible", []):
        return Eligibility("eligible", opportunity_level)
    if defect in task_matrix.get("not_applicable", []):
        return Eligibility("not_applicable", opportunity_level)
    if defect in task_matrix.get("instruction_confounded", []):
        return Eligibility("instruction_confounded", opportunity_level)
    raise ValueError(f"Defect is not classified for task {task_id}: {defect}")


def eligible_defects(
    task_id: str,
    defects: list[str],
    specification: dict[str, Any] | None = None,
) -> dict[str, Eligibility]:
    return {
        defect: eligibility_for(task_id, defect, specification)
        for defect in defects
    }
