from services.research.detector_validation import (
    load_validation_labels,
    run_controlled_fixtures,
)
from services.research.validation_metrics import (
    ValidationLabel,
    detector_readiness_report,
)


def test_controlled_fixtures_cover_every_detector_and_pass():
    report = run_controlled_fixtures()

    assert report["detector_count"] == 18
    assert report["case_count"] == 36
    assert report["all_passed"] is True
    assert report["failed_count"] == 0


def test_detector_readiness_reports_pending_detectors_without_manual_labels():
    report = detector_readiness_report(
        [],
        detector_ids=["magic_number", "duplicate_expression"],
    )

    assert report["overall_status"] == "preliminary"
    assert [row["status"] for row in report["detectors"]] == ["pending", "pending"]


def test_detector_readiness_distinguishes_pilot_and_validated_status():
    labels = []
    for index in range(20):
        labels.append(ValidationLabel(str(index), "T1", "magic_number", 1, 1))
        labels.append(ValidationLabel(str(index + 20), "T1", "magic_number", 0, 0))

    report = detector_readiness_report(labels, detector_ids=["magic_number"])

    assert report["overall_status"] == "validated"
    assert report["detectors"][0]["status"] == "validated"


def test_load_validation_labels_skips_pending_and_uncertain_rows(tmp_path):
    path = tmp_path / "labels.jsonl"
    path.write_text(
        '{"submission_id":"pending","task_id":"T1","defect":"magic_number","manual_label":null,"detector_label":1}\n'
        '{"submission_id":"uncertain","task_id":"T1","defect":"magic_number","manual_label":"uncertain","detector_label":1}\n'
        '{"submission_id":"complete","task_id":"T1","defect":"magic_number","manual_label":1,"detector_label":1}\n',
        encoding="utf-8",
    )

    labels = load_validation_labels(path)

    assert len(labels) == 1
    assert labels[0].submission_id == "complete"
