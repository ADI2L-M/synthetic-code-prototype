"""Create authentic review cases, run controlled checks, or score labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make the repository root importable when this file is executed directly as a
# script (``python scripts/validate_detectors.py``).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_VALIDATION_DIR = ROOT / "research-notes" / "detector-validation"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("assisted", "authentic", "controlled", "manual", "merge"),
        required=True,
        help=(
            "Create an AI-assisted first-pass label file, create an authentic "
            "review sample, run controlled fixtures, or score manual labels."
        ),
    )
    parser.add_argument(
        "--labels",
        type=Path,
        help="Completed manual-label JSONL file used with --mode manual.",
    )
    parser.add_argument(
        "--review-input",
        type=Path,
        default=ROOT
        / "research-notes"
        / "detector-validation"
        / "authentic-detector-review.jsonl",
        help="Authentic review JSONL used with --mode assisted.",
    )
    parser.add_argument(
        "--uncertain-output",
        type=Path,
        default=ROOT
        / "research-notes"
        / "detector-validation"
        / "authentic-detector-uncertain-cases.jsonl",
        help="Uncertainty queue written with --mode assisted.",
    )
    parser.add_argument(
        "--assisted-input",
        type=Path,
        default=ROOT
        / "research-notes"
        / "detector-validation"
        / "authentic-detector-assisted-labels.jsonl",
        help="Complete assisted label file used with --mode merge.",
    )
    parser.add_argument(
        "--reviewed-uncertain",
        type=Path,
        default=ROOT
        / "research-notes"
        / "detector-validation"
        / "authentic-detector-uncertain-cases.jsonl",
        help="Edited uncertainty queue used with --mode merge.",
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=ROOT / "research-notes" / "data-identification" / "cs1_labs_responses.xlsx",
        help="Authentic XLSX workbook used with --mode authentic.",
    )
    parser.add_argument(
        "--grouping",
        type=Path,
        default=ROOT
        / "research-notes"
        / "data-identification"
        / "cs1_regeneration_task_groups.json",
        help="Authentic-task to prototype-task mapping JSON.",
    )
    parser.add_argument(
        "--per-class",
        type=int,
        default=40,
        help=(
            "Maximum detector-positive and detector-negative cases per defect "
            "for authentic review; use 0 for all cases."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260927,
        help="Random seed used for reproducible authentic-case sampling.",
    )
    parser.add_argument(
        "--include-noneligible",
        action="store_true",
        help="Include defects marked not applicable or instruction-confounded.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path. Defaults under research-notes/detector-validation.",
    )
    args = parser.parse_args()

    from detectors.research.registry import RESEARCH_DETECTORS
    from services.research.authentic_detector_review import write_authentic_review
    from services.research.detector_validation import (
        create_assisted_validation,
        load_validation_labels,
        merge_assisted_labels,
        run_controlled_fixtures,
    )
    from services.research.validation_metrics import detector_readiness_report

    if args.mode == "assisted":
        output = args.output or DEFAULT_VALIDATION_DIR / "authentic-detector-assisted-labels.jsonl"
        counts = create_assisted_validation(
            args.review_input,
            output,
            args.uncertain_output,
        )
        print(
            f"Assisted labels written to {output}\n"
            f"Provisional: {counts['provisional']} | "
            f"Uncertain: {counts['uncertain']}"
        )
        return

    if args.mode == "merge":
        output = args.output or DEFAULT_VALIDATION_DIR / "authentic-detector-gold-labels.jsonl"
        counts = merge_assisted_labels(
            args.assisted_input,
            args.reviewed_uncertain,
            output,
        )
        print(
            f"Merged labels written to {output}\n"
            f"Merged human decisions: {counts['merged']}"
        )
        return

    if args.mode == "authentic":
        output = args.output or DEFAULT_VALIDATION_DIR / "authentic-detector-review.jsonl"
        summary = write_authentic_review(
            args.workbook,
            args.grouping,
            output,
            per_class=args.per_class,
            seed=args.seed,
            eligible_only=not args.include_noneligible,
        )
        print(
            f"Authentic review written to {output}\n"
            f"Selected cases: {summary['selected_case_count']}"
        )
        return

    if args.mode == "controlled":
        output = args.output or DEFAULT_VALIDATION_DIR / "controlled-fixture-report.json"
        _write_json(output, run_controlled_fixtures())
        print(f"Controlled validation written to {output}")
        return

    if args.labels is None:
        parser.error("--labels is required when --mode manual is selected")
    output = args.output or DEFAULT_VALIDATION_DIR / "manual-validation-report.json"
    labels = load_validation_labels(args.labels)
    report = detector_readiness_report(
        labels,
        detector_ids=sorted(RESEARCH_DETECTORS),
    )
    report["label_source"] = str(args.labels)
    report["label_count"] = len(labels)
    _write_json(output, report)
    print(f"Manual validation written to {output}")


if __name__ == "__main__":
    main()
