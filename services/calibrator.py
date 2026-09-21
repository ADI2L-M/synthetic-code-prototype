def calibration_constraints(comparison: list[dict]) -> dict[str, str]:
    return {row["defect"]: {"Increase": "strengthen the generation constraint", "Reduce": "reduce the generation constraint", "Maintain": "maintain the generation constraint"}[row["action"]] for row in comparison}
