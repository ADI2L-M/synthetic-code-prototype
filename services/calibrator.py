from models.types import ProfileComparison

ACTION_CONSTRAINTS = {
    "Increase": "strengthen the generation constraint",
    "Reduce": "reduce the generation constraint",
    "Maintain": "maintain the generation constraint",
}


def calibration_constraints(comparison: list[ProfileComparison]) -> dict[str, str]:
    return {row.defect: ACTION_CONSTRAINTS[row.action] for row in comparison}
