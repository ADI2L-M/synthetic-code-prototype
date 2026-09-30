from services.research.detector_validation import (
    create_assisted_validation,
    load_validation_labels,
    merge_assisted_labels,
    run_controlled_fixtures,
)
from services.research.validation_metrics import (
    ValidationLabel,
    detector_readiness_report,
)


def test_controlled_fixtures_cover_every_detector_and_pass():
    report = run_controlled_fixtures()

    assert report["detector_count"] == 17
    assert report["case_count"] == 34
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


def test_assisted_validation_separates_contextual_cases(tmp_path):
    source = tmp_path / "review.jsonl"
    output = tmp_path / "assisted.jsonl"
    uncertain = tmp_path / "uncertain.jsonl"
    source.write_text(
        '{"submission_id":"s1","task_id":"T1","defect":"magic_number","detector_label":1}\n'
        '{"submission_id":"s2","task_id":"T1","defect":"else_if","detector_label":1}\n',
        encoding="utf-8",
    )

    counts = create_assisted_validation(source, output, uncertain)

    assert counts["total"] == 2
    assert counts["provisional"] == 1
    assert counts["uncertain"] == 1
    assert '"manual_label": 1' in output.read_text(encoding="utf-8")
    assert '"manual_label": "uncertain"' in uncertain.read_text(encoding="utf-8")


def test_merge_assisted_labels_updates_only_reviewed_cases(tmp_path):
    assisted = tmp_path / "assisted.jsonl"
    reviewed = tmp_path / "reviewed.jsonl"
    output = tmp_path / "gold.jsonl"
    assisted.write_text(
        '{"submission_id":"s1","task_id":"T1","defect":"magic_number","manual_label":"uncertain"}\n'
        '{"submission_id":"s2","task_id":"T1","defect":"else_if","manual_label":1}\n',
        encoding="utf-8",
    )
    reviewed.write_text(
        '{"submission_id":"s1","task_id":"T1","defect":"magic_number","manual_label":0,"notes":"threshold is task-required"}\n',
        encoding="utf-8",
    )

    counts = merge_assisted_labels(assisted, reviewed, output)
    text = output.read_text(encoding="utf-8")

    assert counts == {"total": 2, "merged": 1}
    assert '"manual_label": 0' in text
    assert '"notes": "threshold is task-required"' in text
