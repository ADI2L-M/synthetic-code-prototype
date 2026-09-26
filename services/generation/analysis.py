from models.types import ProfileComparison, SubmissionResult


def observed_profile(
    submissions: list[SubmissionResult], defect_ids: list[str]
) -> dict[str, float]:
    valid = [item for item in submissions if item.validation.status == "PASS"]
    return {
        defect_id: sum(item.defects.get(defect_id, False) for item in valid)
        / len(valid)
        if valid
        else 0.0
        for defect_id in defect_ids
    }


def compare_profiles(
    target: dict[str, float], observed: dict[str, float], tolerance: float
) -> list[ProfileComparison]:
    """Compare observed prevalence using a target-relative tolerance.

    ``tolerance`` is a fraction of each defect's target prevalence, not an
    absolute percentage-point difference. A zero target therefore has no
    tolerance: any observed occurrence is overrepresented.
    """
    rows: list[ProfileComparison] = []
    for defect_id, target_value in target.items():
        difference = target_value - observed.get(defect_id, 0.0)
        allowed_difference = abs(target_value) * tolerance
        if difference > allowed_difference:
            status, action = "Underrepresented", "Increase"
        elif difference < -allowed_difference:
            status, action = "Overrepresented", "Reduce"
        else:
            status, action = "Within tolerance", "Maintain"
        rows.append(
            ProfileComparison(
                defect=defect_id,
                target=target_value,
                observed=observed.get(defect_id, 0.0),
                difference=difference,
                status=status,
                action=action,
            )
        )
    return rows
