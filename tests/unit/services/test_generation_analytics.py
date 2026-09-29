from models.types import (
    IterationResult,
    ProfileComparison,
    SubmissionResult,
    ValidationResult,
)
from services.generation.analytics import (
    category_summary_rows,
    detector_interaction_rows,
    generation_quality,
)


def test_category_summary_reports_submission_coverage_and_profile_rows():
    iteration = IterationResult(
        iteration=1,
        task_id="T1",
        task_name="Temperature classification",
        target_profile={
            "magic_number": 0.5,
            "redundant_comparison": 0.5,
        },
        tolerance=0.1,
        constraints={},
        specification="",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="pass",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": True, "redundant_comparison": False},
            ),
            SubmissionResult(
                submission_id=2,
                source_code="pass",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": False, "redundant_comparison": True},
            ),
        ],
        observed_profile={"magic_number": 0.5, "redundant_comparison": 0.5},
        comparison=[
            ProfileComparison(
                defect="magic_number",
                target=0.5,
                observed=0.5,
                difference=0.0,
                status="Within tolerance",
                action="Maintain",
            ),
            ProfileComparison(
                defect="redundant_comparison",
                target=0.5,
                observed=0.5,
                difference=0.0,
                status="Within tolerance",
                action="Maintain",
            ),
        ],
    )

    rows = category_summary_rows(iteration)

    assert rows[0]["Category"] == "Task-independent"
    assert rows[0]["Submission coverage"] == 0.5
    assert rows[0]["Profile rows in tolerance"] == "1/1"
    assert rows[1]["Category"] == "Task-dependent"
    assert rows[1]["Submission coverage"] == 0.5
    assert rows[1]["Profile rows in tolerance"] == "1/1"
    assert generation_quality(iteration)["valid_submissions"] == 2


def test_detector_interactions_count_only_valid_co_occurrences():
    iteration = IterationResult(
        iteration=1,
        task_id="T1",
        task_name="Temperature classification",
        target_profile={"magic_number": 0.5, "redundant_comparison": 0.5},
        tolerance=0.1,
        constraints={},
        specification="",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="pass",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": True, "redundant_comparison": True},
            ),
            SubmissionResult(
                submission_id=2,
                source_code="pass",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": True, "redundant_comparison": False},
            ),
            SubmissionResult(
                submission_id=3,
                source_code="fail",
                validation=ValidationResult("FAIL", 0, 1),
                defects={"magic_number": True, "redundant_comparison": True},
            ),
        ],
        observed_profile={"magic_number": 1.0, "redundant_comparison": 1.0},
        comparison=[],
    )

    rows = detector_interaction_rows(iteration)

    assert rows[0]["Co-occurrence count"] == 1
    assert rows[0]["Valid denominator"] == 2
    assert rows[0]["Co-occurrence rate"] == 0.5
