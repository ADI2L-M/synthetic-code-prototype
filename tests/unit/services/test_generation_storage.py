from models.types import IterationResult, SubmissionResult, ValidationResult
from services.generation.storage import (
    create_run,
    initialise_database,
    load_iterations,
    persisted_submission_count,
    save_iteration,
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
