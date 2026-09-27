from models.types import IterationResult, ProfileComparison
from services.generation.analytics import generation_quality

ACTION_CONSTRAINTS = {
    "Increase": "strengthen the generation constraint",
    "Reduce": "reduce the generation constraint",
    "Maintain": "maintain the generation constraint",
}


def calibration_constraints(comparison: list[ProfileComparison]) -> dict[str, str]:
    return {row.defect: ACTION_CONSTRAINTS[row.action] for row in comparison}


CALIBRATION_QUALITY_KEYS = (
    "functional_pass_rate",
    "independent_coverage",
    "dependent_coverage",
    "category_requirement_rate",
)


def calibration_is_non_regressive(
    previous: IterationResult, candidate: IterationResult
) -> bool:
    """Return whether a calibrated batch preserves every quality dimension.

    Calibration may improve the defect profile, but it must not trade away
    functional validity or either mandatory defect category. The comparison is
    intentionally component-wise rather than using one aggregate score.
    """
    previous_quality = generation_quality(previous)
    candidate_quality = generation_quality(candidate)
    return all(
        candidate_quality[key] >= previous_quality[key]
        for key in CALIBRATION_QUALITY_KEYS
    )


def calibration_regression_message(
    previous: IterationResult, candidate: IterationResult
) -> str:
    """Explain why a calibrated batch was not committed."""
    previous_quality = generation_quality(previous)
    candidate_quality = generation_quality(candidate)
    labels = {
        "functional_pass_rate": "functional pass rate",
        "independent_coverage": "task-independent coverage",
        "dependent_coverage": "task-dependent coverage",
        "category_requirement_rate": "overall category requirement",
    }
    regressions = [
        (
            labels[key],
            previous_quality[key],
            candidate_quality[key],
        )
        for key in CALIBRATION_QUALITY_KEYS
        if candidate_quality[key] < previous_quality[key]
    ]
    detail = "; ".join(
        f"{label}: {before:.0%} → {after:.0%}"
        for label, before, after in regressions
    )
    return (
        "Calibration was not applied because the regenerated batch would "
        f"reduce required quality coverage ({detail}). The previous batch "
        "was retained."
    )
