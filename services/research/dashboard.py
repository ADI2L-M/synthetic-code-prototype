"""Load and shape empirical research reports for the Streamlit dashboard."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "authentic-prevalence"
DEFAULT_PROFILE_PATH = DEFAULT_OUTPUT_DIR / "empirical-target-profile.json"
DEFAULT_SUMMARY_PATH = DEFAULT_OUTPUT_DIR / "prototype-task-detection-summary.json"
DEFAULT_SPECIFICATION_PATH = ROOT / "config" / "defect_specifications.json"

TASK_LABELS = {
    "T1": "T1 · Temperature Classification",
    "T2": "T2 · Total Scores",
    "T3": "T3 · Sum to N",
}

TASK_DEFINITION_FILES = {
    "T1": "research-notes/task-def-yaml/T1_conditional_logic.yaml",
    "T2": "research-notes/task-def-yaml/T2_list_processing.yaml",
    "T3": "research-notes/task-def-yaml/T3_numeric_iteration.yaml",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_sort_key(label: str) -> tuple[int, int]:
    match = re.search(r"Lab\s+(\d+)\s+Q(\d+)", label)
    return (int(match.group(1)), int(match.group(2))) if match else (999, 999)


def _display_name(defect: str) -> str:
    return defect.replace("_", " ").title()


def _catalog(specification: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["name"]: item
        for item in specification.get("defects", [])
        if "name" in item
    }


def _task_report_map(
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for index_item in summary.get("task_reports", []):
        report_path = output_dir / index_item["report"]
        report = _read_json(report_path)
        reports[report["task"]["authentic_task"]] = {
            **report,
            "report_path": str(report_path.relative_to(ROOT)),
            "prototype_task": index_item["prototype_task"],
        }
    return reports


def _target_rows(
    prototype_task: str,
    profile_task: dict[str, Any],
    summary_task: dict[str, Any],
    specification: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    opportunity_levels = (
        specification.get("eligibility_matrix", {})
        .get(prototype_task, {})
        .get("opportunity_level", {})
    )
    for defect, target in profile_task.get("target_profile", {}).items():
        result = summary_task["defects"][defect]
        defect_specification = catalog.get(defect, {})
        rows.append(
            {
                "defect": defect,
                "display_name": _display_name(defect),
                "category": defect_specification.get("category", "unknown"),
                "opportunity_level": opportunity_levels.get(
                    defect, result.get("opportunity_level", "normal")
                ),
                "target_prevalence": float(target),
                "pooled_prevalence": result["pooled_prevalence"],
                "eligible_tasks": result["eligible_task_count"],
                "valid_submissions": result["valid_submission_count"],
                "affected_submissions": result["affected_submission_count"],
                "minimum_prevalence": result["minimum_task_prevalence"],
                "maximum_prevalence": result["maximum_task_prevalence"],
                "standard_deviation": result["standard_deviation"],
                "task_prevalence": result["task_prevalence"],
            }
        )
    return rows


def _authentic_task_rows(
    prototype_task: str,
    task_reports: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "authentic_task": label,
            "mapping_role": report["task"]["mapping_role"],
            "functionally_correct": report["submissions"]["functionally_correct_count"],
            "parseable": report["submissions"]["parseable_count"],
            "parse_failures": report["submissions"]["parse_failure_count"],
            "report_path": report["report_path"],
            "defects": report["defects"],
        }
        for label, report in task_reports.items()
        if report["prototype_task"] == prototype_task
    ]
    return sorted(rows, key=lambda row: _task_sort_key(row["authentic_task"]))


def build_dashboard_data(
    profile: dict[str, Any],
    summary: dict[str, Any],
    specification: dict[str, Any],
    task_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a serialisable view model from the persisted research outputs."""
    catalog = _catalog(specification)
    prototype_tasks: dict[str, dict[str, Any]] = {}
    for prototype_task, profile_task in profile.get("prototype_tasks", {}).items():
        summary_task = summary["prototype_tasks"][prototype_task]
        authentic_tasks = _authentic_task_rows(prototype_task, task_reports)
        prototype_tasks[prototype_task] = {
            "id": prototype_task,
            "label": TASK_LABELS.get(prototype_task, prototype_task),
            "task_family": profile_task["task_family"],
            "definition_file": TASK_DEFINITION_FILES.get(prototype_task, ""),
            "authentic_task_count": len(authentic_tasks),
            "functionally_correct_count": sum(
                row["functionally_correct"] for row in authentic_tasks
            ),
            "parseable_count": sum(row["parseable"] for row in authentic_tasks),
            "target_rows": _target_rows(
                prototype_task, profile_task, summary_task, specification, catalog
            ),
            "omitted_not_applicable": profile_task.get(
                "omitted_not_applicable", []
            ),
            "authentic_tasks": authentic_tasks,
        }

    return {
        "report_type": profile.get("report_type"),
        "profile_source": profile.get("profile_source"),
        "generated_at_utc": profile.get("generated_at_utc"),
        "primary_estimator": profile.get("primary_estimator"),
        "secondary_estimator": profile.get("secondary_estimator"),
        "detector_validation_status": profile.get("detector_validation_status"),
        "detector_count": summary.get("source", {}).get("detector_count", 0),
        "denominator_definition": summary.get("source", {}).get(
            "denominator_definition", ""
        ),
        "prototype_tasks": prototype_tasks,
        "defect_catalog": {
            defect: {
                "display_name": _display_name(defect),
                "category": item.get("category", "unknown"),
                "definition": item.get("authoritative_definition", ""),
            }
            for defect, item in catalog.items()
        },
    }


def load_dashboard_data(
    profile_path: Path = DEFAULT_PROFILE_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    specification_path: Path = DEFAULT_SPECIFICATION_PATH,
) -> dict[str, Any]:
    """Load the empirical profile, summary, specification, and task reports."""
    output_dir = summary_path.parent
    summary = _read_json(summary_path)
    return build_dashboard_data(
        _read_json(profile_path),
        summary,
        _read_json(specification_path),
        _task_report_map(summary, output_dir),
    )
