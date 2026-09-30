from io import BytesIO
from json import loads
from zipfile import ZipFile

from models.types import IterationResult, SubmissionResult, ValidationResult
from services.generation.export import (
    calibrated_artifact_export_archive,
    iteration_export_archive,
    load_iteration_export_archive,
)


def test_iteration_export_contains_source_files_and_manifest():
    iteration = IterationResult(
        iteration=2,
        task_id="T1",
        task_name="Conditional logic",
        target_profile={},
        tolerance=0.1,
        constraints={},
        specification="",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="def classify_temperature(temp):\n    return 'cold'\n",
                validation=ValidationResult("PASS", 1, 0),
                assigned_defects=("magic_number",),
                defects={"magic_number": True},
            )
        ],
        observed_profile={},
        comparison=[],
        model="qwen2.5-coder:1.5b",
    )

    with ZipFile(BytesIO(iteration_export_archive(iteration))) as archive:
        assert archive.namelist() == [
            "submissions/submission_001.py",
            "iteration.json",
            "manifest.json",
        ]
        assert "return 'cold'" in archive.read(
            "submissions/submission_001.py"
        ).decode()
        manifest = loads(archive.read("manifest.json"))

    assert manifest["iteration"] == 2
    assert manifest["submissions"][0]["detected_defects"] == ["magic_number"]

    restored = load_iteration_export_archive(iteration_export_archive(iteration))
    assert restored.task_id == iteration.task_id
    assert restored.submissions[0].source_code == iteration.submissions[0].source_code


def test_calibrated_artifact_export_contains_selected_batch_and_lineage():
    iteration = IterationResult(
        iteration=2,
        task_id="T1",
        task_name="Conditional logic",
        target_profile={"magic_number": 0.5},
        tolerance=0.1,
        constraints={"magic_number": "strengthen the generation constraint"},
        specification="",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="def classify_temperature(temp):\n    return 'cold'\n",
                validation=ValidationResult("PASS", 1, 0),
                assigned_defects=("magic_number",),
                defects={"magic_number": True},
            )
        ],
        observed_profile={"magic_number": 1.0},
        comparison=[],
        model="qwen2.5-coder:1.5b",
    )

    with ZipFile(
        BytesIO(calibrated_artifact_export_archive(iteration, [iteration]))
    ) as archive:
        assert archive.namelist() == [
            "submissions/submission_001.py",
            "iteration.json",
            "calibrated-artifact.json",
        ]
        manifest = loads(archive.read("calibrated-artifact.json"))

    assert manifest["artifact"] == "iteratively_calibrated_synthetic_batch"
    assert manifest["selected_iteration"] == 2
    assert manifest["calibration_lineage"][0]["constraints_applied"] == {
        "magic_number": "strengthen the generation constraint"
    }
