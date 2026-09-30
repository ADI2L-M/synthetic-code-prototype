"""Export generated submissions from a single generation iteration."""

from __future__ import annotations

from io import BytesIO
from json import dumps, loads
from zipfile import ZIP_DEFLATED, ZipFile

from models.types import IterationResult
from services.generation.storage import iteration_from_dict, iteration_to_dict


def _write_iteration_files(output: ZipFile, iteration: IterationResult) -> list[dict[str, object]]:
    """Write code files and return their manifest entries."""
    submissions: list[dict[str, object]] = []
    for submission in iteration.submissions:
        filename = f"submissions/submission_{submission.submission_id:03d}.py"
        output.writestr(filename, submission.source_code)
        submissions.append(
            {
                "submission_id": submission.submission_id,
                "filename": filename,
                "validation": submission.validation.status,
                "assigned_defects": list(submission.assigned_defects),
                "detected_defects": [
                    defect
                    for defect, present in submission.defects.items()
                    if present
                ],
                "generation_attempts": submission.generation_attempts,
                "category_requirements_met": submission.category_requirements_met,
            }
        )
    return submissions


def iteration_export_archive(iteration: IterationResult) -> bytes:
    """Return a ZIP archive containing an iteration's code and manifest."""
    manifest = {
        "iteration": iteration.iteration,
        "task_id": iteration.task_id,
        "task_name": iteration.task_name,
        "model": iteration.model,
        "context_length": iteration.context_length,
        "temperature": iteration.temperature,
        "tolerance": iteration.tolerance,
        "accepted": iteration.accepted,
        "condition": iteration.condition,
        "target_standard_errors": iteration.target_standard_errors,
        "payload_file": "iteration.json",
        "submissions": [],
    }
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
        manifest["submissions"] = _write_iteration_files(output, iteration)
        output.writestr(
            "iteration.json",
            dumps(iteration_to_dict(iteration), indent=2, ensure_ascii=False),
        )
        output.writestr("manifest.json", dumps(manifest, indent=2))
    return archive.getvalue()


def calibrated_artifact_export_archive(
    iteration: IterationResult,
    history: list[IterationResult],
) -> bytes:
    """Export the retained calibrated batch together with its lineage.

    The latest retained iteration is the artefact selected by the UI.  The
    lineage records every retained calibration step so the exported batch is
    auditable without depending on Streamlit session state.
    """
    manifest = {
        "artifact": "iteratively_calibrated_synthetic_batch",
        "selected_iteration": iteration.iteration,
        "task_id": iteration.task_id,
        "task_name": iteration.task_name,
        "model": iteration.model,
        "context_length": iteration.context_length,
        "temperature": iteration.temperature,
        "tolerance": iteration.tolerance,
        "accepted": iteration.accepted,
        "condition": iteration.condition,
        "target_standard_errors": iteration.target_standard_errors,
        "payload_file": "iteration.json",
        "calibration_lineage": [
            {
                "iteration": item.iteration,
                "accepted": item.accepted,
                "constraints_applied": dict(item.constraints),
                "observed_profile": item.observed_profile,
            }
            for item in history
        ],
        "submissions": [],
    }
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
        manifest["submissions"] = _write_iteration_files(output, iteration)
        output.writestr(
            "iteration.json",
            dumps(iteration_to_dict(iteration), indent=2, ensure_ascii=False),
        )
        output.writestr("calibrated-artifact.json", dumps(manifest, indent=2))
    return archive.getvalue()


def load_iteration_export_archive(archive_data: bytes) -> IterationResult:
    """Rehydrate an iteration exported by either archive function."""
    with ZipFile(BytesIO(archive_data)) as archive:
        try:
            payload = loads(archive.read("iteration.json"))
        except KeyError as error:
            raise ValueError("The archive does not contain iteration.json") from error
    return iteration_from_dict(payload)
