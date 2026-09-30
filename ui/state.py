from collections.abc import Iterable
from typing import cast

import streamlit as st

from models.types import IterationResult
from services.generation.storage import (
    create_run,
    latest_run_id,
    load_iterations,
    save_iteration,
    update_run_status,
)


def initialise_state() -> None:
    if "generation_run_id" not in st.session_state:
        st.session_state.generation_run_id = latest_run_id() or create_run()
    if "iterations" not in st.session_state:
        st.session_state.iterations = load_iterations(
            st.session_state.generation_run_id
        )
    if "generation_summary_by_task" not in st.session_state:
        st.session_state.generation_summary_by_task = {
            item.task_id: _summary_from_iteration(item)
            for item in st.session_state.iterations
        }
    if "constraints_by_task" not in st.session_state:
        st.session_state.constraints_by_task = {}
    if "calibration_requested" not in st.session_state:
        st.session_state.calibration_requested = False
    if "generation_in_progress" not in st.session_state:
        st.session_state.generation_in_progress = False
    elif (
        st.session_state.generation_in_progress
        and "generation_job" not in st.session_state
    ):
        # Recover sessions left by the earlier synchronous implementation.
        st.session_state.generation_in_progress = False


def generation_in_progress() -> bool:
    """Return whether the current session is executing a generation request."""
    return bool(st.session_state.get("generation_in_progress", False))


def begin_generation() -> None:
    """Mark the current session as busy before a generation rerun starts."""
    st.session_state.generation_in_progress = True
    update_run_status(st.session_state.generation_run_id, "running")


def start_new_generation_run(
    *,
    task_id: str,
    model: str,
    batch_size: int,
    temperature: float,
    tolerance: float,
    context_length: int,
) -> None:
    """Start a fresh run for a normal Generate batch action.

    Persisted runs remain available in SQLite, but the active run is reset so
    a new batch starts at iteration 1. Calibration deliberately does not call
    this function because it must continue the current run and repair the
    latest retained artefact.
    """
    st.session_state.generation_run_id = create_run(
        task_id=task_id,
        model=model,
        batch_size=batch_size,
        temperature=temperature,
        tolerance=tolerance,
        context_length=context_length,
    )
    st.session_state.iterations = []
    st.session_state.constraints_by_task = {}


def finish_generation() -> None:
    """Clear the busy marker after generation succeeds or fails."""
    st.session_state.generation_in_progress = False


def finish_generation_run(status: str, error_message: str | None = None) -> None:
    """Persist the final lifecycle state for the active generation run."""
    update_run_status(
        st.session_state.generation_run_id,
        status,
        error_message=error_message,
    )


def set_generation_error(message: str | None) -> None:
    """Preserve a generation error for the rerun that restores the UI."""
    st.session_state.generation_error_message = message


def consume_generation_error() -> str | None:
    """Read and clear the generation error shown after a completed run."""
    return cast(
        str | None,
        st.session_state.pop("generation_error_message", None),
    )


def all_iterations() -> list[IterationResult]:
    return cast(list[IterationResult], st.session_state.iterations)


def task_iterations(task_id: str) -> list[IterationResult]:
    return [item for item in all_iterations() if item.task_id == task_id]


def current_iteration(task_id: str) -> IterationResult | None:
    iterations = task_iterations(task_id)
    return iterations[-1] if iterations else None


def next_iteration_number(task_id: str) -> int:
    return len(task_iterations(task_id)) + 1


def append_iteration(iteration: IterationResult) -> None:
    all_iterations().append(iteration)
    generation_summary_by_task()[iteration.task_id] = _summary_from_iteration(
        iteration
    )
    save_iteration(st.session_state.generation_run_id, iteration)


def _summary_from_iteration(iteration: IterationResult) -> dict[str, object]:
    return {
        "task_name": iteration.task_name,
        "model": iteration.model,
        "batch_size": len(iteration.submissions),
        "temperature": iteration.temperature,
        "tolerance": iteration.tolerance,
    }


def generation_summary_by_task() -> dict[str, dict[str, object]]:
    return cast(
        dict[str, dict[str, object]],
        st.session_state.generation_summary_by_task,
    )


def set_generation_summary(
    task_id: str,
    *,
    task_name: str,
    model: str,
    batch_size: int,
    temperature: float,
    tolerance: float,
) -> None:
    generation_summary_by_task()[task_id] = {
        "task_name": task_name,
        "model": model,
        "batch_size": batch_size,
        "temperature": temperature,
        "tolerance": tolerance,
    }


def generation_summary(task_id: str) -> dict[str, object] | None:
    return generation_summary_by_task().get(task_id)


def constraints_for(task_id: str) -> dict[str, str]:
    constraints = cast(dict[str, dict[str, str]], st.session_state.constraints_by_task)
    return dict(constraints.get(task_id, {}))


def set_constraints(task_id: str, values: dict[str, str]) -> None:
    constraints = cast(dict[str, dict[str, str]], st.session_state.constraints_by_task)
    constraints[task_id] = dict(values)


def request_calibration() -> None:
    st.session_state.calibration_requested = True


def consume_calibration_request() -> bool:
    requested = bool(st.session_state.calibration_requested)
    st.session_state.calibration_requested = False
    return requested


def replace_iterations(iterations: Iterable[IterationResult]) -> None:
    """Testing helper for replacing state without exposing storage details."""
    st.session_state.iterations = list(iterations)
