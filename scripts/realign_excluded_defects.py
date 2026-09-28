"""Remove excluded exploratory defects from generated empirical outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "research-notes" / "authentic-submission-outputs"
DEFAULT_SPECIFICATION = ROOT / "config" / "defect_specifications.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _remove_defect(payload: dict, defect: str) -> None:
    defects = payload.get("defects")
    if isinstance(defects, dict):
        defects.pop(defect, None)

    target_profile = payload.get("target_profile")
    if isinstance(target_profile, dict):
        target_profile.pop(defect, None)

    for category in ("task_independent", "task_dependent"):
        category_values = payload.get(category)
        if isinstance(category_values, dict):
            category_values.pop(defect, None)

    omitted = payload.get("omitted_not_applicable")
    if isinstance(omitted, list):
        payload["omitted_not_applicable"] = [item for item in omitted if item != defect]

    prototype_summary = payload.get("prototype_task_detection_summary")
    if isinstance(prototype_summary, dict):
        prototype_summary.pop(defect, None)


def realign_outputs(output_dir: Path, specification_path: Path, defect: str) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from services.research.target_profile import export_empirical_target_profile

    summary_path = output_dir / "prototype-task-detection-summary.json"
    summary = _read_json(summary_path)
    summary.get("source", {}).update({"detector_count": 17})
    for task_summary in summary.get("prototype_tasks", {}).values():
        _remove_defect(task_summary, defect)
    _write_json(summary_path, summary)

    for report_path in (output_dir / "task-reports").glob("*.json"):
        report = _read_json(report_path)
        _remove_defect(report, defect)
        _write_json(report_path, report)

    export_empirical_target_profile(
        summary_path,
        specification_path,
        output_dir / "empirical-target-profile.json",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--defect", default="redundant_for")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--specification", type=Path, default=DEFAULT_SPECIFICATION)
    args = parser.parse_args()
    realign_outputs(args.output_dir, args.specification, args.defect)
    print(f"Removed {args.defect} from active empirical outputs")


if __name__ == "__main__":
    main()
