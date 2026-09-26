from detectors.research.redundant_comparison import detect_redundant_comparison_result
from services.authentic.ingestion import AuthenticSubmission
from services.research.pipeline import analyze_submission


def _submission(source_code: str, task_id: str = "T1") -> AuthenticSubmission:
    return AuthenticSubmission("S1", 1, 1, task_id, source_code, None, 2)


def test_pipeline_preserves_raw_detection_and_task_eligibility():
    record = analyze_submission(
        _submission(
            "def classify_temperature(temp):\n"
            "    return (temp < 10) == True\n"
        ),
        {"redundant_comparison": detect_redundant_comparison_result},
        functional_correct=True,
        constraint_compliant=True,
    )

    assert record.parse_success
    assert record.valid_for_prevalence
    assert record.defects["redundant_comparison"].present
    assert record.eligibility["redundant_comparison"].status == "eligible"


def test_pipeline_does_not_treat_unknown_correctness_as_valid():
    record = analyze_submission(_submission("pass"))

    assert record.parse_success
    assert record.functional_correct is None
    assert record.constraint_compliant is None
    assert not record.valid_for_prevalence


def test_pipeline_retains_parse_failure_and_skips_raw_detection():
    record = analyze_submission(_submission("def broken(:"))

    assert not record.parse_success
    assert record.exclusion_reason == "parse_error"
    assert record.defects["redundant_comparison"].count == 0
    assert "parsing failed" in (record.defects["redundant_comparison"].notes or "")


def test_pipeline_records_functional_exclusion():
    record = analyze_submission(
        _submission("pass"),
        functional_correct=False,
        constraint_compliant=True,
    )

    assert record.exclusion_reason == "functional_incorrect"
    assert not record.valid_for_prevalence
