"""SQLite persistence for interactive synthetic-generation iterations."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from models.types import (
    IterationResult,
    ProfileComparison,
    SubmissionResult,
    ValidationResult,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT / "outputs" / "synthetic-generation" / "generation.sqlite3"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path | None = None) -> sqlite3.Connection:
    path = database_path or DEFAULT_DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialise_database(database_path: Path | None = None) -> None:
    """Create the local persistence schema if it does not already exist."""
    with _connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS generation_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS iterations (
                iteration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES generation_runs(run_id),
                task_id TEXT NOT NULL,
                iteration_number INTEGER NOT NULL,
                accepted INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(run_id, task_id, iteration_number)
            );

            CREATE INDEX IF NOT EXISTS idx_iterations_run_task
                ON iterations(run_id, task_id, iteration_number);

            CREATE TABLE IF NOT EXISTS submissions (
                iteration_id INTEGER NOT NULL REFERENCES iterations(iteration_id)
                    ON DELETE CASCADE,
                submission_id INTEGER NOT NULL,
                source_code TEXT NOT NULL,
                prompt TEXT NOT NULL,
                validation_json TEXT NOT NULL,
                defects_json TEXT NOT NULL,
                assigned_defects_json TEXT NOT NULL,
                generation_attempts INTEGER NOT NULL,
                category_requirements_met INTEGER NOT NULL,
                PRIMARY KEY(iteration_id, submission_id)
            );
            """
        )


def create_run(
    database_path: Path | None = None,
    run_id: str | None = None,
) -> str:
    """Create and persist a generation run identifier."""
    initialise_database(database_path)
    identifier = run_id or uuid4().hex
    now = _utc_now()
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT INTO generation_runs(run_id, created_at, last_used_at) "
            "VALUES (?, ?, ?)",
            (identifier, now, now),
        )
    return identifier


def latest_run_id(database_path: Path | None = None) -> str | None:
    """Return the most recently used run, if persistent data exists."""
    initialise_database(database_path)
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT run_id FROM generation_runs ORDER BY last_used_at DESC LIMIT 1"
        ).fetchone()
    return str(row["run_id"]) if row else None


def iteration_to_dict(iteration: IterationResult) -> dict[str, object]:
    """Convert an iteration into a JSON-serialisable lossless payload."""
    return asdict(iteration)


def iteration_from_dict(payload: dict[str, object]) -> IterationResult:
    """Rehydrate an iteration payload stored by SQLite or an export archive."""
    submissions = [
        SubmissionResult(
            submission_id=int(item["submission_id"]),
            source_code=str(item.get("source_code", "")),
            validation=ValidationResult(**item["validation"]),
            defects=dict(item.get("defects", {})),
            assigned_defects=tuple(item.get("assigned_defects", ())),
            prompt=str(item.get("prompt", "")),
            generation_seed=item.get("generation_seed"),
            generation_attempts=int(item.get("generation_attempts", 1)),
            category_requirements_met=bool(
                item.get("category_requirements_met", False)
            ),
            missing_defect_categories=tuple(
                item.get("missing_defect_categories", ())
            ),
        )
        for item in payload.get("submissions", [])
    ]
    comparisons = [
        ProfileComparison(**item)
        for item in payload.get("comparison", [])
    ]
    return IterationResult(
        iteration=int(payload["iteration"]),
        task_id=str(payload["task_id"]),
        task_name=str(payload["task_name"]),
        target_profile={
            str(key): float(value)
            for key, value in payload.get("target_profile", {}).items()
        },
        tolerance=float(payload["tolerance"]),
        constraints=dict(payload.get("constraints", {})),
        specification=str(payload.get("specification", "")),
        submissions=submissions,
        observed_profile={
            str(key): float(value)
            for key, value in payload.get("observed_profile", {}).items()
        },
        comparison=comparisons,
        assignment_seed=payload.get("assignment_seed"),
        expected_assignment_counts={
            str(key): float(value)
            for key, value in payload.get("expected_assignment_counts", {}).items()
        },
        planned_assignment_counts={
            str(key): int(value)
            for key, value in payload.get("planned_assignment_counts", {}).items()
        },
        model=payload.get("model"),
        context_length=payload.get("context_length"),
        target_standard_errors={
            str(key): float(value)
            for key, value in payload.get("target_standard_errors", {}).items()
        },
        condition=str(payload.get("condition", "task_aware_non_adaptive")),
    )


def save_iteration(
    run_id: str,
    iteration: IterationResult,
    database_path: Path | None = None,
) -> None:
    """Persist an iteration and its submission index rows atomically."""
    initialise_database(database_path)
    payload = iteration_to_dict(iteration)
    now = _utc_now()
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO generation_runs(run_id, created_at, last_used_at) "
            "VALUES (?, ?, ?)",
            (run_id, now, now),
        )
        connection.execute(
            "UPDATE generation_runs SET last_used_at = ? WHERE run_id = ?",
            (now, run_id),
        )
        existing = connection.execute(
            "SELECT iteration_id FROM iterations "
            "WHERE run_id = ? AND task_id = ? AND iteration_number = ?",
            (run_id, iteration.task_id, iteration.iteration),
        ).fetchone()
        if existing:
            iteration_id = int(existing["iteration_id"])
            connection.execute(
                "UPDATE iterations SET accepted = ?, payload_json = ?, created_at = ? "
                "WHERE iteration_id = ?",
                (
                    int(iteration.accepted),
                    json.dumps(payload, ensure_ascii=False),
                    now,
                    iteration_id,
                ),
            )
            connection.execute(
                "DELETE FROM submissions WHERE iteration_id = ?", (iteration_id,)
            )
        else:
            cursor = connection.execute(
                "INSERT INTO iterations "
                "(run_id, task_id, iteration_number, accepted, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    iteration.task_id,
                    iteration.iteration,
                    int(iteration.accepted),
                    json.dumps(payload, ensure_ascii=False),
                    now,
                ),
            )
            iteration_id = int(cursor.lastrowid)
        connection.executemany(
            "INSERT INTO submissions "
            "(iteration_id, submission_id, source_code, prompt, validation_json, "
            "defects_json, assigned_defects_json, generation_attempts, "
            "category_requirements_met) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    iteration_id,
                    submission.submission_id,
                    submission.source_code,
                    submission.prompt,
                    json.dumps(asdict(submission.validation), ensure_ascii=False),
                    json.dumps(submission.defects, ensure_ascii=False),
                    json.dumps(list(submission.assigned_defects), ensure_ascii=False),
                    submission.generation_attempts,
                    int(submission.category_requirements_met),
                )
                for submission in iteration.submissions
            ],
        )


def load_iterations(
    run_id: str,
    task_id: str | None = None,
    database_path: Path | None = None,
) -> list[IterationResult]:
    """Load persisted iterations in generation order."""
    initialise_database(database_path)
    query = "SELECT payload_json FROM iterations WHERE run_id = ?"
    parameters: list[object] = [run_id]
    if task_id is not None:
        query += " AND task_id = ?"
        parameters.append(task_id)
    query += " ORDER BY task_id, iteration_number"
    with _connect(database_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [iteration_from_dict(json.loads(row["payload_json"])) for row in rows]


def persisted_submission_count(
    run_id: str,
    database_path: Path | None = None,
) -> int:
    """Return the number of indexed submissions in a run."""
    initialise_database(database_path)
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM submissions "
            "JOIN iterations USING(iteration_id) WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    return int(row["count"])
