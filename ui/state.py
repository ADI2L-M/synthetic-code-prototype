from collections.abc import Iterable
from typing import cast

import streamlit as st

from models.types import IterationResult


def initialise_state() -> None:
    if "iterations" not in st.session_state:
        st.session_state.iterations = []
    if "constraints_by_task" not in st.session_state:
        st.session_state.constraints_by_task = {}
    if "calibration_requested" not in st.session_state:
        st.session_state.calibration_requested = False


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
