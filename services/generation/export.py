"""Export generated submissions from a single generation iteration."""

from __future__ import annotations

from io import BytesIO
from json import dumps
from zipfile import ZIP_DEFLATED, ZipFile

from models.types import IterationResult


def iteration_export_archive(iteration: IterationResult) -> bytes:
    """Return a ZIP archive containing an iteration's code and manifest."""
    manifest = {
        "iteration": iteration.iteration,
        "task_id": iteration.task_id,
        "task_name": iteration.task_name,
        "model": iteration.model,
        "context_length": iteration.context_length,
        "tolerance": iteration.tolerance,
        "accepted": iteration.accepted,
        "target_standard_errors": iteration.target_standard_errors,
        "submissions": [],
    }
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
        for submission in iteration.submissions:
            filename = f"submissions/submission_{submission.submission_id:03d}.py"
            output.writestr(filename, submission.source_code)
            manifest["submissions"].append(
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
        output.writestr("manifest.json", dumps(manifest, indent=2))
    return archive.getvalue()
