"""Run reference-derived functional tests over the authentic workbook."""

from __future__ import annotations

import csv
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.authentic.functional_validation import (
    AuthenticTestPlan,
    load_test_plans,
    validate_authentic_source,
)
from services.authentic.ingestion import AuthenticSubmission, load_task_submissions


def _task_catalog(grouping_path: Path) -> dict[str, tuple[str, str]]:
    grouping = json.loads(grouping_path.read_text(encoding="utf-8"))
    catalog: dict[str, tuple[str, str]] = {}
    for group_id, definition in grouping.items():
        task_id, task_family = group_id.split("_", maxsplit=1)
        for group in ("direct", "supporting"):
            for label in definition[group]:
                catalog[label] = (task_id, task_family)
    return catalog


def _validate_one(
    submission: AuthenticSubmission,
    plan: AuthenticTestPlan,
) -> dict[str, Any]:
    result = validate_authentic_source(
        submission.source_code,
        submission.reference_code or "",
        plan,
    )
    return {
        "submission_id": submission.submission_id,
        "lab": submission.lab,
        "question": submission.question,
        "source_row": submission.source_row,
        "status": result.status,
        "tests_passed": result.tests_passed,
        "tests_failed": result.tests_failed,
        "failure_message": result.failure_message,
        "timed_out": result.timed_out,
        "error": result.error,
        "source_code": submission.source_code,
    }


def run_authentic_filter(
    workbook_path: Path,
    grouping_path: Path,
    plan_path: Path,
    output_dir: Path,
    workers: int = 8,
    progress=None,
) -> dict[str, Any]:
    """Run all mapped task contracts and write complete/filtered CSV outputs."""
    plans = load_test_plans(plan_path)
    catalog = _task_catalog(grouping_path)
    results: list[dict[str, Any]] = []

    for task_number, (label, (task_id, task_family)) in enumerate(
        sorted(catalog.items()), start=1
    ):
        lab, question = label.split(" Q")
        submissions = load_task_submissions(
            workbook_path,
            grouping_path,
            int(lab.split()[1]),
            int(question),
        )
        plan = plans[label]
        task_results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_validate_one, submission, plan): submission
                for submission in submissions
            }
            for future in as_completed(futures):
                task_results.append(future.result())
        task_results.sort(key=lambda row: row["source_row"])
        for row in task_results:
            row.update(
                {
                    "task_id": task_id,
                    "task_family": task_family,
                    "authentic_task": label,
                    "test_mode": plan.mode,
                    "functionally_correct": row["status"] == "PASS",
                }
            )
        results.extend(task_results)
        if progress is not None:
            progress(task_number, len(catalog), label, len(task_results))

    output_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "submission_id",
        "authentic_task",
        "task_id",
        "task_family",
        "lab",
        "question",
        "source_row",
        "test_mode",
        "status",
        "functionally_correct",
        "tests_passed",
        "tests_failed",
        "timed_out",
        "failure_message",
        "error",
        "source_code",
    ]
    all_path = output_dir / "authentic_functional_validation.csv"
    filtered_path = output_dir / "functionally_correct_submissions.csv"
    for path, rows in (
        (all_path, results),
        (filtered_path, [row for row in results if row["functionally_correct"]]),
    ):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    by_task: dict[str, dict[str, Any]] = {}
    for label in sorted(catalog):
        task_rows = [row for row in results if row["authentic_task"] == label]
        by_task[label] = {
            "task_id": task_rows[0]["task_id"],
            "task_family": task_rows[0]["task_family"],
            "test_mode": task_rows[0]["test_mode"],
            "submission_count": len(task_rows),
            "functionally_correct_count": sum(
                row["functionally_correct"] for row in task_rows
            ),
            "functionally_incorrect_count": sum(
                not row["functionally_correct"] for row in task_rows
            ),
            "failure_messages": dict(
                Counter(
                    row["failure_message"] or row["error"] or "unknown"
                    for row in task_rows
                    if not row["functionally_correct"]
                ).most_common(10)
            ),
        }
    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "workbook": str(workbook_path),
        "test_plan": str(plan_path),
        "task_count": len(catalog),
        "submission_count": len(results),
        "functionally_correct_count": sum(
            row["functionally_correct"] for row in results
        ),
        "functionally_incorrect_count": sum(
            not row["functionally_correct"] for row in results
        ),
        "tasks": by_task,
        "outputs": {
            "all_validation": str(all_path),
            "functionally_correct": str(filtered_path),
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary
