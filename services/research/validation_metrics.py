from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationLabel:
    submission_id: str
    task_id: str
    defect: str
    manual_label: int
    detector_label: int


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
                "validation_n": len(defect_labels),
            }
        )
    return report
