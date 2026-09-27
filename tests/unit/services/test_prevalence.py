from services.research.prevalence import (
    SubmissionObservation,
    family_prevalence,
    task_prevalence,
)


def _observations() -> list[SubmissionObservation]:
    return [
        SubmissionObservation("a", "q1", "family", True, {"d": True}, {"d": "eligible"}),
        SubmissionObservation("b", "q1", "family", True, {"d": False}, {"d": "eligible"}),
        SubmissionObservation("invalid", "q1", "family", False, {"d": True}, {"d": "eligible"}),
        SubmissionObservation("na", "q1", "family", True, {"d": True}, {"d": "not_applicable"}),
        SubmissionObservation("c", "q2", "family", True, {"d": False}, {"d": "eligible"}),
    ]


def test_task_prevalence_uses_valid_eligible_submissions_only():
    rows = task_prevalence(_observations(), "d")

    assert rows[0]["valid_eligible_submission_count"] == 2
    assert rows[0]["affected_submission_count"] == 1
    assert rows[0]["prevalence"] == 0.5


def test_family_prevalence_equal_weights_tasks_and_reports_pooled_value():
    result = family_prevalence(_observations(), "d")[0]

    assert result["eligible_task_count"] == 2
    assert result["task_mean_prevalence"] == 0.25
    assert result["pooled_prevalence"] == 1 / 3
    assert len(result["task_prevalence"]) == 2


def test_family_prevalence_does_not_create_zero_for_non_applicable_task():
    observations = [
        SubmissionObservation("a", "q1", "family", True, {"d": True}, {"d": "eligible"}),
        SubmissionObservation("b", "q2", "family", True, {"d": False}, {"d": "not_applicable"}),
    ]

    result = family_prevalence(observations, "d")[0]

    assert result["eligible_task_count"] == 1
    assert result["task_mean_prevalence"] == 1.0
