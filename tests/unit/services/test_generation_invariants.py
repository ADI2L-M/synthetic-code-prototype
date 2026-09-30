from services.generation.analysis import compare_profiles, wilson_interval
from services.generation.assignment import plan_defect_assignments


def test_wilson_interval_stays_bounded_for_all_small_samples():
    for trials in range(1, 31):
        for successes in range(trials + 1):
            low, high = wilson_interval(successes, trials)
            assert 0.0 <= low <= high <= 1.0


def test_profile_comparison_actions_are_consistent_with_signed_difference():
    for target in (0.01, 0.1, 0.5, 1.0):
        for observed in (0.0, target / 2, target, min(1.0, target * 2)):
            row = compare_profiles({"defect": target}, {"defect": observed}, 0.1)[0]
            if row.status == "Within tolerance":
                assert row.action == "Maintain"
            elif row.difference > 0:
                assert row.status == "Underrepresented"
                assert row.action == "Increase"
            else:
                assert row.status == "Overrepresented"
                assert row.action == "Reduce"


def test_assignment_plan_never_exceeds_batch_or_defect_cap():
    for batch_size in range(1, 16):
        plan = plan_defect_assignments(
            "T2",
            {"rare": 0.17, "common": 0.8},
            batch_size,
            iteration_number=1,
            max_defects_per_submission=2,
        )
        assert len(plan.by_submission) == batch_size
        assert all(len(defects) <= 2 for defects in plan.by_submission.values())
        for defect, count in plan.planned_counts.items():
            assert count == sum(defect in values for values in plan.by_submission.values())
