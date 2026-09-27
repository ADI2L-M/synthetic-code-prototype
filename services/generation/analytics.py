"""Analytics helpers for synthetic defect generation batches."""

from __future__ import annotations

from collections import Counter
from statistics import mean

from models.types import IterationResult
from services.generation.prompt_builder import TASK_INDEPENDENT_DEFECTS


def _valid_submissions(iteration: IterationResult):
    return [
        submission
        for submission in iteration.submissions
        if submission.validation.status == "PASS"
    ]


def _category(defect: str) -> str:
    return (
        "Task-independent"
        if defect in TASK_INDEPENDENT_DEFECTS
        else "Task-dependent"
    )


def defect_analytics_rows(iteration: IterationResult) -> list[dict[str, object]]:
    """Return guided, detected, and target values for each target defect."""
    valid = _valid_submissions(iteration)
    guided = Counter(
        defect
        for submission in iteration.submissions
        for defect in submission.assigned_defects
    )
    comparison = {row.defect: row for row in iteration.comparison}
    rows: list[dict[str, object]] = []
    for defect, target in iteration.target_profile.items():
        detected = sum(
            submission.defects.get(defect, False) for submission in valid
        )
        observed = detected / len(valid) if valid else 0.0
        row = comparison[defect]
        rows.append(
            {
                "Defect": defect.replace("_", " ").title(),
                "Category": _category(defect),
                "Target": target,
                "Guided": guided.get(defect, 0),
                "Detected (valid)": detected,
                "Valid denominator": len(valid),
                "Observed": observed,
                "Target standard error": row.target_standard_error,
                "Observed 95% low": row.observed_interval_low,
                "Observed 95% high": row.observed_interval_high,
                "Decision margin": row.allowed_difference,
                "Difference": row.difference,
                "Status": row.status,
                "Action": row.action,
            }
        )
    return rows


def generation_quality(iteration: IterationResult) -> dict[str, float | int]:
    """Summarise functional and category-level generation quality."""
    valid = _valid_submissions(iteration)
    total = len(iteration.submissions)

    def coverage(category: str) -> int:
        return sum(
            any(
                submission.defects.get(defect, False)
                for defect in iteration.target_profile
                if _category(defect) == category
            )
            for submission in valid
        )

    return {
        "total_submissions": total,
        "valid_submissions": len(valid),
        "invalid_submissions": total - len(valid),
        "functional_pass_rate": len(valid) / total if total else 0.0,
        "independent_coverage": coverage("Task-independent") / len(valid)
        if valid
        else 0.0,
        "dependent_coverage": coverage("Task-dependent") / len(valid)
        if valid
        else 0.0,
        "category_requirement_rate": sum(
            submission.category_requirements_met for submission in iteration.submissions
        )
        / total
        if total
        else 0.0,
        "average_attempts": mean(
            submission.generation_attempts for submission in iteration.submissions
        )
        if total
        else 0.0,
    }


def iteration_history_rows(
    history: list[IterationResult],
) -> list[dict[str, object]]:
    """Build compact history rows for calibration review."""
    rows: list[dict[str, object]] = []
    for iteration in history:
        quality = generation_quality(iteration)
        rows.append(
            {
                "Iteration": iteration.iteration,
                "Model": iteration.model or "—",
                "Generated": quality["total_submissions"],
                "Functionally valid": quality["valid_submissions"],
                "Pass rate": quality["functional_pass_rate"],
                "Category coverage": quality["category_requirement_rate"],
                "Average attempts": quality["average_attempts"],
                "Profile status": "Accepted"
                if iteration.accepted
                else "Needs review",
                "Calibration applied": bool(iteration.constraints),
            }
        )
    return rows
