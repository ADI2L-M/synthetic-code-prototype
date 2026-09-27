from dataclasses import dataclass
from typing import Any

DEFAULT_PRECISION_TARGET = 0.90
DEFAULT_RECALL_TARGET = 0.85
DEFAULT_F1_TARGET = 0.87
DEFAULT_MIN_POSITIVE_LABELS = 20
DEFAULT_MIN_NEGATIVE_LABELS = 20


@dataclass(frozen=True)
class ValidationLabel:
    submission_id: str
    task_id: str
    defect: str
    manual_label: int
    detector_label: int
    task_family: str = ""
    eligibility: str = "eligible"
    reviewer: str = ""
    notes: str = ""


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def validation_report(labels: list[ValidationLabel]) -> list[dict[str, Any]]:
    grouped: dict[str, list[ValidationLabel]] = {}
    for label in labels:
        if label.manual_label not in (0, 1) or label.detector_label not in (0, 1):
            raise ValueError("Validation labels must be 0 or 1")
        grouped.setdefault(label.defect, []).append(label)

    report: list[dict[str, Any]] = []
    for defect, defect_labels in sorted(grouped.items()):
        true_positive = sum(
            label.manual_label == 1 and label.detector_label == 1
            for label in defect_labels
        )
        false_positive = sum(
            label.manual_label == 0 and label.detector_label == 1
            for label in defect_labels
        )
        true_negative = sum(
            label.manual_label == 0 and label.detector_label == 0
            for label in defect_labels
        )
        false_negative = sum(
            label.manual_label == 1 and label.detector_label == 0
            for label in defect_labels
        )
        precision = _ratio(true_positive, true_positive + false_positive)
        recall = _ratio(true_positive, true_positive + false_negative)
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision is not None
            and recall is not None
            and precision + recall
            else None
        )
        report.append(
            {
                "defect": defect,
                "TP": true_positive,
                "FP": false_positive,
                "TN": true_negative,
                "FN": false_negative,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "positive_labels": true_positive + false_negative,
                "negative_labels": true_negative + false_positive,
                "validation_n": len(defect_labels),
            }
        )
    return report


def detector_readiness_report(
    labels: list[ValidationLabel],
    detector_ids: list[str] | None = None,
    *,
    precision_target: float = DEFAULT_PRECISION_TARGET,
    recall_target: float = DEFAULT_RECALL_TARGET,
    f1_target: float = DEFAULT_F1_TARGET,
    min_positive_labels: int = DEFAULT_MIN_POSITIVE_LABELS,
    min_negative_labels: int = DEFAULT_MIN_NEGATIVE_LABELS,
) -> dict[str, Any]:
    """Classify detector validity using pilot review metrics and evidence counts."""
    report_by_defect = {
        row["defect"]: row for row in validation_report(labels)
    }
    detector_ids = detector_ids or sorted(report_by_defect)
    detectors: list[dict[str, Any]] = []
    for defect in detector_ids:
        row = report_by_defect.get(defect)
        if row is None:
            detectors.append(
                {
                    "defect": defect,
                    "status": "pending",
                    "reason": "No manual validation labels have been recorded.",
                }
            )
            continue

        enough_examples = (
            row["positive_labels"] >= min_positive_labels
            and row["negative_labels"] >= min_negative_labels
        )
        meets_metrics = (
            row["precision"] is not None
            and row["recall"] is not None
            and row["f1"] is not None
            and row["precision"] >= precision_target
            and row["recall"] >= recall_target
            and row["f1"] >= f1_target
        )
        if enough_examples and meets_metrics:
            status = "validated"
            reason = "Metrics and minimum reviewed-example counts meet the pilot criteria."
        elif meets_metrics:
            status = "pilot_validated"
            reason = "Metrics meet the targets, but more reviewed examples are needed."
        else:
            status = "preliminary"
            reason = "One or more metric targets are not met."
        detectors.append({**row, "status": status, "reason": reason})

    statuses = {row["status"] for row in detectors}
    if statuses and statuses == {"validated"}:
        overall_status = "validated"
    elif statuses and statuses.isdisjoint({"preliminary", "pending"}):
        overall_status = "pilot_validated"
    else:
        overall_status = "preliminary"
    return {
        "overall_status": overall_status,
        "criteria": {
            "precision_target": precision_target,
            "recall_target": recall_target,
            "f1_target": f1_target,
            "minimum_positive_labels": min_positive_labels,
            "minimum_negative_labels": min_negative_labels,
        },
        "detectors": detectors,
    }
