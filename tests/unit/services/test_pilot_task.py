from pathlib import Path

from services.authentic.ingestion import load_task_submissions
from services.authentic.pilot_task import lab_12_q2_task
from services.generation.validator import validate_source


WORKBOOK = Path("research-notes/data-identification/cs1_labs_responses.xlsx")
GROUPING = Path("research-notes/data-identification/cs1_regeneration_task_groups.json")


def test_lab_12_q2_contract_is_tuple_returning():
    task = lab_12_q2_task()

    assert task.function_name == "get_sum_evens_odds"
    assert len(task.test_cases) == 4
    assert all(case.expected_type == "tuple" for case in task.test_cases)


def test_lab_12_q2_reference_answer_passes_contract():
    submission = load_task_submissions(WORKBOOK, GROUPING, 12, 2)[0]

    result = validate_source(submission.reference_code or "", lab_12_q2_task())

    assert result.status == "PASS"
    assert result.tests_passed == 4


def test_lab_12_q2_rejects_list_instead_of_tuple():
    source = "def get_sum_evens_odds(numbers_list):\n    return [0, 0]\n"

    result = validate_source(source, lab_12_q2_task())

    assert result.status == "FAIL"
    assert result.tests_failed == 4
