from pathlib import Path

from services.authentic.ingestion import load_task_submissions, task_id_for


WORKBOOK = Path("research-notes/data-identification/cs1_labs_responses.xlsx")
GROUPING = Path("research-notes/data-identification/cs1_regeneration_task_groups.json")


def test_lab_question_maps_to_target_task():
    assert task_id_for(12, 2, GROUPING) == "T2"


def test_lab_12_question_2_loads_authentic_responses():
    submissions = load_task_submissions(WORKBOOK, GROUPING, 12, 2)

    assert len(submissions) == 626
    assert submissions[0].submission_id == "Lab_12_Q2_R2"
    assert submissions[0].reference_code
    assert all(submission.task_id == "T2" for submission in submissions)
