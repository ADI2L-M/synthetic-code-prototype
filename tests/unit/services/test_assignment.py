import pytest

from services.generation.assignment import plan_defect_assignments


def test_assignment_plan_is_reproducible_and_balanced():
    first = plan_defect_assignments(
        "T1",
        {"formatting": 0.55, "magic_number": 0.54},
        batch_size=10,
        iteration_number=1,
    )
    second = plan_defect_assignments(
        "T1",
        {"formatting": 0.55, "magic_number": 0.54},
        batch_size=10,
        iteration_number=1,
    )

    assert first == second
    assert sum(len(defects) for defects in first.by_submission.values()) == sum(
        first.planned_counts.values()
    )
    assert max(len(defects) for defects in first.by_submission.values()) <= 3


def test_rare_defect_keeps_fractional_expected_quota():
    plans = [
        plan_defect_assignments(
            "T1",
            {"rare": 0.0017},
            batch_size=10,
            iteration_number=iteration,
        )
        for iteration in range(1, 11)
    ]

    assert plans[0].expected_counts["rare"] == pytest.approx(0.017)
    assert sum(plan.planned_counts["rare"] for plan in plans) < 10
