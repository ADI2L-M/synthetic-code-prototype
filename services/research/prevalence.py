from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any


@dataclass(frozen=True)
class SubmissionObservation:
    submission_id: str
    task_id: str
    task_family: str
    valid: bool
    defects: dict[str, bool]
    eligibility: dict[str, str]


def task_prevalence(
    observations: list[SubmissionObservation],
    defect: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[SubmissionObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.task_id, []).append(observation)

    rows: list[dict[str, Any]] = []
    for task_id, task_observations in sorted(grouped.items()):
        eligible = [
            observation
            for observation in task_observations
            if observation.valid
            and observation.eligibility.get(defect) == "eligible"
        ]
        prevalence = (
            sum(observation.defects.get(defect, False) for observation in eligible)
            / len(eligible)
            if eligible
            else None
        )
        family = task_observations[0].task_family
        rows.append(
            {
                "task_id": task_id,
                "task_family": family,
                "defect": defect,
                "valid_eligible_submission_count": len(eligible),
                "affected_submission_count": sum(
                    observation.defects.get(defect, False) for observation in eligible
                ),
                "prevalence": prevalence,
            }
        )
    return rows


def family_prevalence(
    observations: list[SubmissionObservation],
    defect: str,
) -> list[dict[str, Any]]:
    task_rows = task_prevalence(observations, defect)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in task_rows:
        if row["prevalence"] is not None:
            grouped.setdefault(row["task_family"], []).append(row)

    results: list[dict[str, Any]] = []
    for family, rows in sorted(grouped.items()):
        values = [row["prevalence"] for row in rows]
        valid_count = sum(row["valid_eligible_submission_count"] for row in rows)
        affected_count = sum(row["affected_submission_count"] for row in rows)
        results.append(
            {
                "task_family": family,
                "defect": defect,
                "eligible_task_count": len(rows),
                "valid_submission_count": valid_count,
                "task_mean_prevalence": mean(values),
                "pooled_prevalence": affected_count / valid_count,
                "minimum_task_prevalence": min(values),
                "maximum_task_prevalence": max(values),
                "standard_deviation": pstdev(values) if len(values) > 1 else 0.0,
                "task_prevalence": rows,
            }
        )
    return results
