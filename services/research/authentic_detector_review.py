"""Create human-review cases from authentic student submissions."""

from __future__ import annotations

import ast
import json
import warnings
from collections.abc import Iterable
from pathlib import Path
from random import Random
from typing import Any

from detectors.research.registry import RESEARCH_DETECTORS, detect_research_defects
from models.research import DetectionResult
from services.authentic.ingestion import AuthenticSubmission, load_task_submissions
from services.research.eligibility import eligibility_for

TASK_FAMILIES = {
    "T1": "conditional_logic",
    "T2": "list_processing",
    "T3": "numeric_iteration",
}


def _task_catalog(grouping_path: Path) -> dict[str, tuple[str, str]]:
    grouping = json.loads(grouping_path.read_text(encoding="utf-8"))
    catalog: dict[str, tuple[str, str]] = {}
    for group_id, definition in grouping.items():
        task_id, task_family = group_id.split("_", maxsplit=1)
        for role in ("direct", "supporting"):
            for label in definition.get(role, []):
                catalog[label] = (task_id, task_family)
    return catalog


def _task_sort_key(label: str) -> tuple[int, int]:
    parts = label.replace("Lab ", "").replace(" Q", " ").split()
    return int(parts[0]), int(parts[1])


def _parseable(source: str) -> bool:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            ast.parse(source)
    except (SyntaxError, TypeError, UnicodeError, ValueError):
        return False
    return True


def _detection_summary(result: DetectionResult) -> dict[str, Any]:
    return {
        "present": result.present,
        "count": result.count,
        "locations": [
            {"line": location.line, "column": location.column}
            for location in result.locations
        ],
        "evidence": result.evidence,
        "notes": result.notes,
    }


def _detect(source: str, defect_ids: list[str]) -> dict[str, DetectionResult]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return detect_research_defects(source, defect_ids=defect_ids)


def _select_class(
    rows: list[dict[str, Any]],
    per_class: int,
    randomiser: Random,
) -> list[dict[str, Any]]:
    if per_class == 0 or len(rows) <= per_class:
        return rows
    return randomiser.sample(rows, per_class)


def build_authentic_review_records(
    submissions: Iterable[AuthenticSubmission],
    *,
    per_class: int = 40,
    seed: int = 20260927,
    eligible_only: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run detectors and select a review sample for each defect/class pair.

    ``per_class`` limits the number of detector-positive and detector-negative
    cases retained for each defect. A value of zero retains every eligible
    parseable case. The source code is included once per selected review row so
    that the JSONL file can be reviewed without reopening the workbook.
    """
    if per_class < 0:
        raise ValueError("per_class must be zero or a positive integer")

    candidates: dict[str, dict[bool, list[dict[str, Any]]]] = {
        defect: {True: [], False: []} for defect in RESEARCH_DETECTORS
    }
    summary: dict[str, Any] = {
        "submission_count": 0,
        "parseable_submission_count": 0,
        "parse_failure_count": 0,
        "excluded_noneligible_case_count": 0,
        "candidate_counts": {
            defect: {"detector_positive": 0, "detector_negative": 0}
            for defect in RESEARCH_DETECTORS
        },
        "selected_counts": {
            defect: {"detector_positive": 0, "detector_negative": 0}
            for defect in RESEARCH_DETECTORS
        },
    }

    for submission in submissions:
        summary["submission_count"] += 1
        task_family = TASK_FAMILIES.get(submission.task_id)
        if task_family is None:
            raise ValueError(f"Unknown research task: {submission.task_id}")
        if not _parseable(submission.source_code):
            summary["parse_failure_count"] += 1
            continue

        summary["parseable_submission_count"] += 1
        task_label = f"Lab {submission.lab} Q{submission.question}"
        eligibilities = {
            defect: eligibility_for(submission.task_id, defect)
            for defect in RESEARCH_DETECTORS
        }
        if eligible_only:
            defect_ids = [
                defect
                for defect, eligibility in eligibilities.items()
                if eligibility.status == "eligible"
            ]
            summary["excluded_noneligible_case_count"] += len(
                RESEARCH_DETECTORS
            ) - len(defect_ids)
        else:
            defect_ids = list(RESEARCH_DETECTORS)
        detections = _detect(submission.source_code, defect_ids)
        for defect, detection in detections.items():
            eligibility = eligibilities[defect]
            row = {
                "submission_id": submission.submission_id,
                "authentic_task": task_label,
                "task_id": submission.task_id,
                "task_family": task_family,
                "lab": submission.lab,
                "question": submission.question,
                "source_row": submission.source_row,
                "defect": defect,
                "eligibility": eligibility.status,
                "opportunity_level": eligibility.opportunity_level,
                "detector_label": int(detection.present),
                "detector_count": detection.count,
                "detector_evidence": _detection_summary(detection),
                "manual_label": None,
                "reviewer": "",
                "evidence_reference": "",
                "notes": "",
                "source_code": submission.source_code,
            }
            detector_class = detection.present
            candidates[defect][detector_class].append(row)
            summary["candidate_counts"][defect][
                "detector_positive" if detector_class else "detector_negative"
            ] += 1

    randomiser = Random(seed)
    selected: list[dict[str, Any]] = []
    for defect in RESEARCH_DETECTORS:
        for detector_class, class_name in (
            (True, "detector_positive"),
            (False, "detector_negative"),
        ):
            class_rows = sorted(
                candidates[defect][detector_class],
                key=lambda row: (row["authentic_task"], row["source_row"]),
            )
            chosen = _select_class(class_rows, per_class, randomiser)
            for row in chosen:
                row["review_sample_class"] = class_name
            selected.extend(chosen)
            summary["selected_counts"][defect][class_name] = len(chosen)

    selected.sort(
        key=lambda row: (
            row["defect"],
            row["review_sample_class"],
            row["authentic_task"],
            row["source_row"],
        )
    )
    summary["selected_case_count"] = len(selected)
    summary["detector_count"] = len(RESEARCH_DETECTORS)
    summary["per_class_limit"] = per_class
    summary["seed"] = seed
    summary["eligible_only"] = eligible_only
    return selected, summary


def load_authentic_submissions(
    workbook_path: Path,
    grouping_path: Path,
) -> list[AuthenticSubmission]:
    """Load all mapped authentic submissions from the research workbook."""
    catalog = _task_catalog(grouping_path)
    submissions: list[AuthenticSubmission] = []
    for label in sorted(catalog, key=_task_sort_key):
        lab, question = label.split(" Q")
        submissions.extend(
            load_task_submissions(
                workbook_path,
                grouping_path,
                int(lab.split()[1]),
                int(question),
            )
        )
    return submissions


def write_authentic_review(
    workbook_path: Path,
    grouping_path: Path,
    output_path: Path,
    *,
    per_class: int = 40,
    seed: int = 20260927,
    eligible_only: bool = True,
) -> dict[str, Any]:
    """Generate the JSONL review file and its metadata report."""
    submissions = load_authentic_submissions(workbook_path, grouping_path)
    records, summary = build_authentic_review_records(
        submissions,
        per_class=per_class,
        seed=seed,
        eligible_only=eligible_only,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary.update(
        {
            "report_type": "authentic_detector_review_sample",
            "workbook": str(workbook_path),
            "grouping": str(grouping_path),
            "review_file": str(output_path),
        }
    )
    metadata_path = output_path.with_suffix(".meta.json")
    metadata_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary["metadata_file"] = str(metadata_path)
    return summary
