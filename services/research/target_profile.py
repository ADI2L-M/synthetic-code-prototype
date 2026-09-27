"""Build empirical prevalence profiles for prototype-task generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_empirical_target_profile(
    summary: dict[str, Any],
    specification: dict[str, Any],
) -> dict[str, Any]:
    """Convert prevalence summaries into generation-ready target profiles."""
    catalog = {
        defect["name"]: defect
        for defect in specification.get("defects", [])
    }
    prototype_tasks: dict[str, Any] = {}
    for prototype_task, task_summary in summary["prototype_tasks"].items():
        task_independent: dict[str, Any] = {}
        task_dependent: dict[str, Any] = {}
        omitted_not_applicable: list[str] = []
        target_profile: dict[str, float] = {}
        for defect, result in task_summary["defects"].items():
            if result["task_mean_prevalence"] is None:
                omitted_not_applicable.append(defect)
                continue
            target_value = result["task_mean_prevalence"]
            target_profile[defect] = target_value
            estimate = {
                "prevalence": target_value,
                "eligible_tasks": result["eligible_task_count"],
                "valid_submissions": result["valid_submission_count"],
                "affected_submissions": result["affected_submission_count"],
                "pooled_prevalence": result["pooled_prevalence"],
                "minimum_task_prevalence": result["minimum_task_prevalence"],
                "maximum_task_prevalence": result["maximum_task_prevalence"],
                "standard_deviation": result["standard_deviation"],
                "estimator": "equal_task_weighted_mean",
            }
            category = catalog.get(defect, {}).get("category")
            if category == "task_independent":
                task_independent[defect] = estimate
            else:
                task_dependent[defect] = estimate
        prototype_tasks[prototype_task] = {
            "task_family": task_summary["task_family"],
            "target_profile": target_profile,
            "task_independent": task_independent,
            "task_dependent": task_dependent,
            "omitted_not_applicable": sorted(omitted_not_applicable),
        }
    return {
        "report_type": "empirical_target_profile",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_source": "authentic_cs1_submissions",
        "primary_estimator": "arithmetic mean of eligible authentic-task prevalence",
        "secondary_estimator": "pooled affected submissions divided by pooled valid submissions",
        "detector_validation_status": "preliminary_raw_detector_estimates",
        "prototype_tasks": prototype_tasks,
    }


def export_empirical_target_profile(
    summary_path: Path,
    specification_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Read prevalence output and write the generation target profile."""
    profile = build_empirical_target_profile(
        _read_json(summary_path),
        _read_json(specification_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return profile


def load_empirical_target_values(
    profile_path: Path,
    prototype_task: str,
) -> dict[str, float]:
    """Load flat target values for an explicitly selected prototype task."""
    profile = _read_json(profile_path)
    try:
        values = profile["prototype_tasks"][prototype_task]["target_profile"]
    except KeyError as error:
        raise ValueError(f"No empirical target profile for {prototype_task}") from error
    return {str(defect): float(value) for defect, value in values.items()}
