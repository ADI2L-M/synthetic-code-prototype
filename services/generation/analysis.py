from math import sqrt

from models.types import ProfileComparison, SubmissionResult

CONFIDENCE_Z = 1.96


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


def observed_counts(
    submissions: list[SubmissionResult], defect_ids: list[str]
) -> tuple[dict[str, int], int]:
    """Return defect counts and the valid-submission denominator."""
    valid = [item for item in submissions if item.validation.status == "PASS"]
    return (
        {
            defect_id: sum(item.defects.get(defect_id, False) for item in valid)
            for defect_id in defect_ids
        },
        len(valid),
    )


def wilson_interval(
    successes: int, trials: int, z: float = CONFIDENCE_Z
) -> tuple[float, float]:
    """Return a Wilson confidence interval for a binomial proportion."""
    if trials <= 0:
        return (0.0, 1.0)
    proportion = successes / trials
    denominator = 1 + z**2 / trials
    centre = (proportion + z**2 / (2 * trials)) / denominator
    margin = (
        z
        * sqrt(
            proportion * (1 - proportion) / trials
            + z**2 / (4 * trials**2)
        )
        / denominator
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def compare_profiles(
    target: dict[str, float],
    observed: dict[str, float],
    tolerance: float,
    observed_denominator: int | None = None,
    target_standard_errors: dict[str, float] | None = None,
    observed_counts_by_defect: dict[str, int] | None = None,
) -> list[ProfileComparison]:
    """Compare profiles with sampling uncertainty when counts are available.

    The generation workflow supplies the valid-submission denominator and the
    authentic task-level standard error. In that mode, the allowed difference
    is the larger of the configured tolerance floor and the combined 95%
    sampling margin. Calls without a denominator retain the historical
    target-relative behaviour for compatibility with older callers.
    """
    rows: list[ProfileComparison] = []
    sampling_aware = observed_denominator is not None
    target_standard_errors = target_standard_errors or {}
    observed_counts_by_defect = observed_counts_by_defect or {}
    for defect_id, target_value in target.items():
        observed_value = observed.get(defect_id, 0.0)
        difference = target_value - observed_value
        observed_count = observed_counts_by_defect.get(
            defect_id,
            round(observed_value * observed_denominator)
            if observed_denominator is not None
            else 0,
        )
        denominator = observed_denominator or 0
        target_standard_error = target_standard_errors.get(defect_id, 0.0)
        observed_interval_low, observed_interval_high = wilson_interval(
            observed_count, denominator
        )
        if sampling_aware and denominator > 0:
            observed_standard_error = (
                observed_interval_high - observed_interval_low
            ) / (2 * CONFIDENCE_Z)
            combined_standard_error = sqrt(
                target_standard_error**2 + observed_standard_error**2
            )
            sampling_margin = CONFIDENCE_Z * combined_standard_error
            allowed_difference = max(
                abs(target_value) * tolerance,
                sampling_margin,
            )
        else:
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
                observed_count=observed_count,
                observed_denominator=denominator,
                target_standard_error=target_standard_error,
                observed_interval_low=observed_interval_low,
                observed_interval_high=observed_interval_high,
                allowed_difference=allowed_difference,
            )
        )
    return rows
