"""Reproducible per-submission defect guidance assignments."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from math import floor


MAX_ASSIGNED_DEFECTS = 3


@dataclass(frozen=True)
class AssignmentPlan:
    """The defect guidance assigned to each submission in one iteration."""

    seed: int
    expected_counts: dict[str, float]
    planned_counts: dict[str, int]
    by_submission: dict[int, tuple[str, ...]]


def stable_seed(*parts: object) -> int:
    """Return a stable integer seed independent of Python hash randomisation."""
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % 2_147_483_647


def _stochastic_count(prevalence: float, batch_size: int, seed: int) -> int:
    expected = prevalence * batch_size
    whole = floor(expected)
    fractional = expected - whole
    return whole + int(random.Random(seed).random() < fractional)


def plan_defect_assignments(
    task_id: str,
    target_profile: dict[str, float],
    batch_size: int,
    iteration_number: int,
    max_defects_per_submission: int = MAX_ASSIGNED_DEFECTS,
) -> AssignmentPlan:
    """Create assignments without rounding rare defects upward."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if max_defects_per_submission < 1:
        raise ValueError("max_defects_per_submission must be at least 1")
    if any(not 0 <= prevalence <= 1 for prevalence in target_profile.values()):
        raise ValueError("target prevalence values must be between 0 and 1")

    seed = stable_seed(task_id, iteration_number, "defect-assignment")
    expected_counts = {
        defect: prevalence * batch_size
        for defect, prevalence in target_profile.items()
    }
    planned_counts = {
        defect: _stochastic_count(
            prevalence,
            batch_size,
            stable_seed(seed, defect),
        )
        for defect, prevalence in target_profile.items()
    }
    assignments: dict[int, set[str]] = {
        submission_id: set() for submission_id in range(1, batch_size + 1)
    }

    # Place high-prevalence defects first, then spread them across the least
    # loaded submissions so compatible styles can co-occur without filling one
    # prompt with the whole catalog.
    defect_order = sorted(
        target_profile,
        key=lambda defect: (-target_profile[defect], defect),
    )
    for defect in defect_order:
        defect_seed = stable_seed(seed, defect, "placement")
        placement_rng = random.Random(defect_seed)
        tie_breakers = {
            submission_id: placement_rng.random()
            for submission_id in assignments
        }
        candidates = list(assignments)
        candidates.sort(
            key=lambda submission_id: (
                len(assignments[submission_id]),
                tie_breakers[submission_id],
            )
        )
        available = [
            submission_id
            for submission_id in candidates
            if len(assignments[submission_id]) < max_defects_per_submission
        ]
        requested = planned_counts[defect]
        if requested > len(available):
            raise ValueError(
                "The requested defect profile cannot be assigned with at most "
                f"{max_defects_per_submission} defects per submission."
            )
        for submission_id in available[:requested]:
            assignments[submission_id].add(defect)

    ordered_defects = list(target_profile)
    return AssignmentPlan(
        seed=seed,
        expected_counts=expected_counts,
        planned_counts=planned_counts,
        by_submission={
            submission_id: tuple(
                defect for defect in ordered_defects if defect in assigned
            )
            for submission_id, assigned in assignments.items()
        },
    )
