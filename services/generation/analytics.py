"""Analytics helpers for synthetic defect generation batches."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
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


def category_summary_rows(iteration: IterationResult) -> list[dict[str, object]]:
    """Summarise alignment and coverage for the two defect categories.

    The category coverage values are submission-level measures: a valid
    submission is covered when it contains at least one detected defect from
    the category.  Profile alignment remains defect-level and is reported as
    the number of category rows within the calibrated decision margin.
    """
    quality = generation_quality(iteration)
    rows = defect_analytics_rows(iteration)
    valid = int(quality["valid_submissions"])
    for category, coverage_key in (
        ("Task-independent", "independent_coverage"),
        ("Task-dependent", "dependent_coverage"),
    ):
        category_rows = [row for row in rows if row["Category"] == category]
        in_tolerance = sum(
            row["Status"] == "Within tolerance" for row in category_rows
        )
        rows_count = len(category_rows)
        target_mean = (
            sum(float(row["Target"]) for row in category_rows) / rows_count
            if rows_count
            else 0.0
        )
        observed_mean = (
            sum(float(row["Observed"]) for row in category_rows) / rows_count
            if rows_count
            else 0.0
        )
        rows.append(
            {
                "Category": category,
                "Valid submissions": valid,
                "Submission coverage": float(quality[coverage_key]),
                "Target mean": target_mean,
                "Observed mean": observed_mean,
                "Profile rows in tolerance": f"{in_tolerance}/{rows_count}",
            }
        )
    return rows[-2:]


def detector_interaction_rows(iteration: IterationResult) -> list[dict[str, object]]:
    """Return valid-submission defect co-occurrence counts and rates."""
    valid = _valid_submissions(iteration)
    defects = tuple(iteration.target_profile)
    rows: list[dict[str, object]] = []
    for first, second in combinations(defects, 2):
        count = sum(
            submission.defects.get(first, False)
            and submission.defects.get(second, False)
            for submission in valid
        )
        rows.append(
            {
                "Defect A": first.replace("_", " ").title(),
                "Defect B": second.replace("_", " ").title(),
                "Co-occurrence count": count,
                "Valid denominator": len(valid),
                "Co-occurrence rate": count / len(valid) if valid else 0.0,
            }
        )
    return sorted(
        rows,
        key=lambda row: (-int(row["Co-occurrence count"]), row["Defect A"], row["Defect B"]),
    )


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
