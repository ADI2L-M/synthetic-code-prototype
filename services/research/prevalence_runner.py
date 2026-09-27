"""Execute all research detectors and write task/family prevalence reports."""

from __future__ import annotations

import ast
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from detectors.research.registry import RESEARCH_DETECTORS, detect_research_defects
from models.research import DetectionResult
from services.research.eligibility import eligibility_for
from services.research.prevalence import SubmissionObservation, task_prevalence
from services.research.target_profile import build_empirical_target_profile


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_catalog(grouping_path: Path) -> dict[str, dict[str, str]]:
    grouping = _load_json(grouping_path)
    catalog: dict[str, dict[str, str]] = {}
    for group_id, definition in grouping.items():
        task_id, task_family = group_id.split("_", maxsplit=1)
        for role in ("direct", "supporting"):
            for label in definition.get(role, []):
                catalog[label] = {
                    "task_id": task_id,
                    "task_family": task_family,
                    "mapping_role": role,
                }
    return catalog


def _task_sort_key(label: str) -> tuple[int, int]:
    parts = label.replace("Lab ", "").replace(" Q", " ").split()
    return int(parts[0]), int(parts[1])


def _parseable(source: str) -> bool:
    try:
        ast.parse(source)
    except (SyntaxError, ValueError, TypeError, UnicodeError):
        return False
    return True


def _result_summary(result: DetectionResult) -> dict[str, Any]:
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


def _task_report(
    label: str,
    metadata: dict[str, str],
    rows: list[dict[str, Any]],
    specification: dict[str, Any],
) -> dict[str, Any]:
    task_id = metadata["task_id"]
    defect_ids = list(RESEARCH_DETECTORS)
    eligibility = {
        defect: eligibility_for(task_id, defect, specification)
        for defect in defect_ids
    }
    parseable_rows = [row for row in rows if row["parse_success"]]
    defects: dict[str, dict[str, Any]] = {}
    for defect in defect_ids:
        status = eligibility[defect]
        raw_results = [row["detections"][defect] for row in rows]
        eligible_results = [row["detections"][defect] for row in parseable_rows]
        affected = sum(result.present for result in eligible_results)
        record: dict[str, Any] = {
            "eligibility": status.status,
            "opportunity_level": status.opportunity_level,
            "valid_eligible_submission_count": len(parseable_rows) if status.status == "eligible" else None,
            "eligible_denominator": len(parseable_rows) if status.status == "eligible" else None,
            "affected_submission_count": affected if status.status == "eligible" else None,
            "prevalence": affected / len(parseable_rows) if status.status == "eligible" and parseable_rows else None,
            "raw_detected_submission_count": sum(result.present for result in raw_results),
            "raw_instance_count": sum(result.count for result in raw_results),
            "example_detections": [],
        }
        for row in rows:
            result = row["detections"][defect]
            if result.present and len(record["example_detections"]) < 3:
                record["example_detections"].append(
                    {
                        "submission_id": row["submission_id"],
                        **_result_summary(result),
                    }
                )
        defects[defect] = record

    return {
        "report_type": "authentic_task_prevalence",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": {
            "authentic_task": label,
            "prototype_task": task_id,
            "task_family": metadata["task_family"],
            "mapping_role": metadata["mapping_role"],
        },
        "denominator_definition": "parseable submissions marked functionally correct by the functional-validation dataset",
        "submissions": {
            "functionally_correct_count": len(rows),
            "parseable_count": len(parseable_rows),
            "parse_failure_count": len(rows) - len(parseable_rows),
        },
        "defects": defects,
    }


def _family_summary(
    observations: list[SubmissionObservation],
    labels: dict[str, dict[str, str]],
) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for prototype_task in sorted({metadata["task_id"] for metadata in labels.values()}):
        task_observations = [
            observation
            for observation in observations
            if labels[observation.task_id]["task_id"] == prototype_task
        ]
        family = next(
            labels[observation.task_id]["task_family"] for observation in task_observations
        )
        defects: dict[str, Any] = {}
        for defect in RESEARCH_DETECTORS:
            rows = task_prevalence(task_observations, defect)
            eligible_rows = [row for row in rows if row["prevalence"] is not None]
            values = [row["prevalence"] for row in eligible_rows]
            valid_count = sum(row["valid_eligible_submission_count"] for row in eligible_rows)
            affected_count = sum(row["affected_submission_count"] for row in eligible_rows)
            defects[defect] = {
                "task_family": family,
                "defect": defect,
                "eligible_task_count": len(eligible_rows),
                "valid_submission_count": valid_count,
                "affected_submission_count": affected_count,
                "task_mean_prevalence": mean(values) if values else None,
                "pooled_prevalence": affected_count / valid_count if valid_count else None,
                "minimum_task_prevalence": min(values) if values else None,
                "maximum_task_prevalence": max(values) if values else None,
                "standard_deviation": pstdev(values) if len(values) > 1 else 0.0 if values else None,
                "task_prevalence": eligible_rows,
            }
        summary[prototype_task] = {
            "prototype_task": prototype_task,
            "task_family": family,
            "authentic_task_count": len({observation.task_id for observation in task_observations}),
            "defects": defects,
        }
    return summary


def _write_prototype_task_reports(
    output_dir: Path,
    catalog: dict[str, dict[str, str]],
    summary: dict[str, Any],
) -> list[dict[str, str]]:
    """Collect each prototype task's mapped authentic Lab/Question reports."""
    grouped_dir = output_dir / "prototype-task-reports"
    grouped_dir.mkdir(parents=True, exist_ok=True)
    definition_files = {
        "T1": "research-notes/task-def-yaml/T1_conditional_logic.yaml",
        "T2": "research-notes/task-def-yaml/T2_list_processing.yaml",
        "T3": "research-notes/task-def-yaml/T3_numeric_iteration.yaml",
    }
    index: list[dict[str, str]] = []
    for prototype_task in sorted(summary["prototype_tasks"]):
        metadata = summary["prototype_tasks"][prototype_task]
        authentic_tasks: list[dict[str, Any]] = []
        labels = sorted(
            [label for label, item in catalog.items() if item["task_id"] == prototype_task],
            key=_task_sort_key,
        )
        for label in labels:
            filename = label.replace(" ", "_") + ".json"
            report = json.loads((output_dir / "task-reports" / filename).read_text(encoding="utf-8"))
            authentic_tasks.append(
                {
                    "authentic_task": label,
                    "mapping_role": catalog[label]["mapping_role"],
                    "task_report": f"../task-reports/{filename}",
                    "submissions": report["submissions"],
                    "defects": report["defects"],
                }
            )
        filename = f"{prototype_task}_{metadata['task_family']}.json"
        grouped_report = {
            "report_type": "prototype_task_prevalence",
            "generated_at_utc": summary["generated_at_utc"],
            "prototype_task": {
                "task_id": prototype_task,
                "task_family": metadata["task_family"],
                "target_definition_file": definition_files[prototype_task],
                "mapping_source": "research-notes/data-identification/cs1_regeneration_task_groups.json",
            },
            "authentic_task_count": len(authentic_tasks),
            "authentic_tasks": authentic_tasks,
            "prototype_task_detection_summary": metadata["defects"],
        }
        (grouped_dir / filename).write_text(
            json.dumps(grouped_report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        index.append(
            {
                "prototype_task": prototype_task,
                "task_family": metadata["task_family"],
                "authentic_task_count": str(len(authentic_tasks)),
                "report": f"prototype-task-reports/{filename}",
            }
        )
    (output_dir / "prototype-task-report-index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return index


def regenerate_prototype_task_reports(
    output_dir: Path,
    grouping_path: Path,
) -> list[dict[str, str]]:
    """Regenerate grouped prototype reports from existing task reports."""
    summary_path = output_dir / "prototype-task-detection-summary.json"
    summary = _load_json(summary_path)
    catalog = _task_catalog(grouping_path)
    index = _write_prototype_task_reports(output_dir, catalog, summary)
    summary["prototype_task_reports"] = index
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return index


def run_prevalence_reports(
    filtered_csv: Path,
    grouping_path: Path,
    specification_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run the complete detector set and write one JSON report per task."""
    catalog = _task_catalog(grouping_path)
    specification = _load_json(specification_path)
    task_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    observations: list[SubmissionObservation] = []

    with filtered_csv.open(encoding="utf-8", newline="") as input_file:
        for row in csv.DictReader(input_file):
            label = row["authentic_task"]
            if label not in catalog:
                raise ValueError(f"Task is not present in grouping catalog: {label}")
            source = row.get("source_code", "")
            parse_success = _parseable(source)
            detections = detect_research_defects(source) if parse_success else {
                defect: DetectionResult(
                    defect=defect,
                    notes="Raw detection skipped because parsing failed.",
                )
                for defect in RESEARCH_DETECTORS
            }
            analysis_row = {
                "submission_id": row["submission_id"],
                "parse_success": parse_success,
                "detections": detections,
            }
            task_rows[label].append(analysis_row)
            eligibility = {
                defect: eligibility_for(catalog[label]["task_id"], defect, specification).status
                for defect in RESEARCH_DETECTORS
            }
            observations.append(
                SubmissionObservation(
                    submission_id=row["submission_id"],
                    task_id=label,
                    task_family=catalog[label]["task_family"],
                    valid=parse_success,
                    defects={defect: detections[defect].present for defect in RESEARCH_DETECTORS},
                    eligibility=eligibility,
                )
            )

    task_output_dir = output_dir / "task-reports"
    task_output_dir.mkdir(parents=True, exist_ok=True)
    report_index: list[dict[str, Any]] = []
    for label in sorted(task_rows, key=_task_sort_key):
        report = _task_report(label, catalog[label], task_rows[label], specification)
        filename = label.replace(" ", "_") + ".json"
        (task_output_dir / filename).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        report_index.append(
            {
                "authentic_task": label,
                "prototype_task": catalog[label]["task_id"],
                "task_family": catalog[label]["task_family"],
                "mapping_role": catalog[label]["mapping_role"],
                "report": f"task-reports/{filename}",
            }
        )

    summary = {
        "report_type": "prototype_task_detection_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "filtered_dataset": str(filtered_csv),
            "grouping": str(grouping_path),
            "defect_specification": str(specification_path),
            "detector_count": len(RESEARCH_DETECTORS),
            "denominator_definition": "parseable submissions marked functionally correct by the functional-validation dataset",
            "family_estimator": "arithmetic mean of authentic-task prevalence",
            "secondary_estimator": "pooled affected submissions divided by pooled valid submissions",
        },
        "task_reports": report_index,
        "prototype_tasks": _family_summary(observations, catalog),
    }
    summary["prototype_task_reports"] = _write_prototype_task_reports(
        output_dir, catalog, summary
    )
    (output_dir / "prototype-task-detection-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "empirical-target-profile.json").write_text(
        json.dumps(
            build_empirical_target_profile(summary, specification),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "task-report-index.json").write_text(
        json.dumps(report_index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary
