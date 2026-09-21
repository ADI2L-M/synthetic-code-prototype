from models.types import SubmissionResult


def observed_profile(submissions: list[SubmissionResult], defect_ids: list[str]) -> dict[str, float]:
    valid = [item for item in submissions if item.validation.status == "PASS"]
    return {defect_id: sum(item.defects.get(defect_id, False) for item in valid) / len(valid) if valid else 0.0 for defect_id in defect_ids}


def compare_profiles(target: dict[str, float], observed: dict[str, float], tolerance: float) -> list[dict]:
    rows = []
    for defect_id, target_value in target.items():
        difference = target_value - observed.get(defect_id, 0.0)
        if difference > tolerance:
            status, action = "Underrepresented", "Increase"
        elif difference < -tolerance:
            status, action = "Overrepresented", "Reduce"
        else:
            status, action = "Within tolerance", "Maintain"
        rows.append({"defect": defect_id, "target": target_value, "observed": observed.get(defect_id, 0.0), "difference": difference, "status": status, "action": action})
    return rows
