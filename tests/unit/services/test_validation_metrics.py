import pytest

from services.research.validation_metrics import ValidationLabel, validation_report


def test_validation_report_calculates_confusion_metrics():
    labels = [
        ValidationLabel("1", "T1", "d", 1, 1),
        ValidationLabel("2", "T1", "d", 0, 1),
        ValidationLabel("3", "T1", "d", 0, 0),
        ValidationLabel("4", "T1", "d", 1, 0),
    ]

    row = validation_report(labels)[0]

    assert row["TP"] == 1
    assert row["FP"] == 1
    assert row["TN"] == 1
    assert row["FN"] == 1
    assert row["precision"] == 0.5
    assert row["recall"] == 0.5
    assert row["f1"] == 0.5
    assert row["validation_n"] == 4


def test_validation_report_handles_zero_denominators():
    row = validation_report([ValidationLabel("1", "T1", "d", 0, 0)])[0]

    assert row["precision"] is None
    assert row["recall"] is None
    assert row["f1"] is None


def test_validation_report_rejects_non_binary_labels():
    with pytest.raises(ValueError, match="must be 0 or 1"):
        validation_report([ValidationLabel("1", "T1", "d", 2, 0)])
