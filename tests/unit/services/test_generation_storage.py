import sqlite3

from models.types import IterationResult, SubmissionResult, ValidationResult
from services.generation.storage import (
    create_run,
    get_run,
    initialise_database,
    list_runs,
    load_iterations,
    persisted_submission_count,
    save_iteration,
    update_run_status,
)


def _iteration(iteration_number: int = 1) -> IterationResult:
    return IterationResult(
        iteration=iteration_number,
        task_id="T1",
        task_name="Temperature classification",
        target_profile={"magic_number": 0.5},
        tolerance=0.1,
        constraints={},
        specification="task brief",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="def classify_temperature(temp):\n    return 'cold'\n",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": True},
                assigned_defects=("magic_number",),
                prompt="prompt",
                generation_attempts=1,
                category_requirements_met=True,
            )
        ],
        observed_profile={"magic_number": 1.0},
        comparison=[],
        temperature=0.2,
    )


def test_sqlite_round_trip_persists_iteration_and_submission_rows(tmp_path):
    database = tmp_path / "generation.sqlite3"
    initialise_database(database)
    run_id = create_run(database, run_id="run-1")

    save_iteration(run_id, _iteration(), database)

    loaded = load_iterations(run_id, database_path=database)

    assert [item.iteration for item in loaded] == [1]
    assert loaded[0].submissions[0].source_code.startswith("def classify")
    assert loaded[0].submissions[0].assigned_defects == ("magic_number",)
    assert loaded[0].temperature == 0.2
    assert persisted_submission_count(run_id, database) == 1


def test_sqlite_update_replaces_an_iteration_without_duplicate_rows(tmp_path):
    database = tmp_path / "generation.sqlite3"
    run_id = create_run(database, run_id="run-1")

    save_iteration(run_id, _iteration(), database)
    save_iteration(run_id, _iteration(1), database)

    assert len(load_iterations(run_id, database_path=database)) == 1
    assert persisted_submission_count(run_id, database) == 1


def test_sqlite_run_lifecycle_preserves_metadata_and_terminal_state(tmp_path):
    database = tmp_path / "generation.sqlite3"
    run_id = create_run(
        database,
        run_id="managed-run",
        task_id="T1",
        model="qwen2.5-coder:1.5b",
        batch_size=20,
        temperature=0.2,
        tolerance=0.1,
        context_length=16_384,
        metadata={"purpose": "controlled benchmark"},
    )

    draft = get_run(run_id, database)
    assert draft is not None
    assert draft["status"] == "draft"
    assert draft["task_id"] == "T1"
    assert draft["metadata"] == {"purpose": "controlled benchmark"}

    update_run_status(run_id, "running", database)
    update_run_status(run_id, "completed", database)

    completed = get_run(run_id, database)
    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["completed_at"]
    assert completed["error_message"] is None
    assert list_runs(database, limit=1)[0]["run_id"] == run_id


def test_sqlite_initialisation_migrates_the_original_run_table(tmp_path):
    database = tmp_path / "generation.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE generation_runs ("
            "run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, "
            "last_used_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO generation_runs VALUES (?, ?, ?)",
            ("legacy-run", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )

    initialise_database(database)

    migrated = get_run("legacy-run", database)
    assert migrated is not None
    assert migrated["status"] == "draft"
    assert migrated["metadata"] == {}
