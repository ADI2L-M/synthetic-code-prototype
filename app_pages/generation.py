"""Primary synthetic-generation page."""

from math import sqrt

import streamlit as st

from services.generation.calibrator import (
    calibration_constraints,
    calibration_is_non_regressive,
    calibration_regression_message,
)
from services.generation.jobs import GenerationCancelled, GenerationJob
from services.generation.prototype_runner import run_prototype_iteration
from services.generation.prototype_tasks import load_prototype_task
from services.generation.storage import update_run_status
from services.providers.ollama import OLLAMA_CONTEXT_LENGTH
from ui.app_data import load_dashboard_data_cached
from ui.generation import (
    render_generation,
    render_generation_job_dialog,
    render_generation_sidebar,
)
from ui.state import (
    append_iteration,
    begin_generation,
    constraints_for,
    consume_calibration_request,
    consume_generation_error,
    current_iteration,
    finish_generation,
    finish_generation_run,
    next_iteration_number,
    set_constraints,
    set_generation_error,
    set_generation_summary,
    start_new_generation_run,
    task_iterations,
)

dashboard_data = load_dashboard_data_cached()
generation_controls = render_generation_sidebar(dashboard_data)
generation_error = consume_generation_error()
task = dashboard_data["prototype_tasks"][generation_controls.task_id]
current = current_iteration(generation_controls.task_id)
calibration_requested = consume_calibration_request()

if calibration_requested and current is not None:
    set_constraints(
        generation_controls.task_id,
        calibration_constraints(current.comparison),
    )

generate_requested = generation_controls.generate_requested or calibration_requested

if generate_requested and "generation_job" not in st.session_state:
    if not calibration_requested:
        start_new_generation_run(
            task_id=generation_controls.task_id,
            model=generation_controls.model,
            batch_size=int(generation_controls.batch_size),
            temperature=generation_controls.temperature,
            tolerance=generation_controls.tolerance,
            context_length=OLLAMA_CONTEXT_LENGTH,
        )
    active_constraints = constraints_for(generation_controls.task_id)

    target = {
        row["defect"]: row["target_prevalence"] for row in task["target_rows"]
    }
    target_standard_errors = {
        row["defect"]: (
            float(row["standard_deviation"])
            / sqrt(int(row["eligible_tasks"]))
            if int(row["eligible_tasks"]) > 1
            else 0.0
        )
        for row in task["target_rows"]
    }

    iteration_number = next_iteration_number(generation_controls.task_id)

    set_generation_summary(
        generation_controls.task_id,
        task_name=task["label"],
        model=generation_controls.model,
        batch_size=int(generation_controls.batch_size),
        temperature=generation_controls.temperature,
        tolerance=generation_controls.tolerance,
    )

    def worker(progress_callback, cancel_check):
        return run_prototype_iteration(
            task_id=generation_controls.task_id,
            target_profile=target,
            batch_size=int(generation_controls.batch_size),
            iteration_number=iteration_number,
            tolerance=generation_controls.tolerance,
            model=generation_controls.model,
            base_url=generation_controls.base_url,
            temperature=generation_controls.temperature,
            constraints=active_constraints,
            target_standard_errors=target_standard_errors,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )

    st.session_state.generation_job_context = {
        "task_id": generation_controls.task_id,
        "calibrating": calibration_requested,
        "iteration_number": iteration_number,
    }
    begin_generation()
    st.session_state.generation_job = GenerationJob(worker)
    st.rerun()

job = st.session_state.get("generation_job")
if job is not None:
    context = st.session_state["generation_job_context"]

    def complete_generation(result, error) -> None:
        if error is not None:
            set_generation_error(str(error))
            finish_generation_run(
                "cancelled" if isinstance(error, GenerationCancelled) else "failed",
                str(error),
            )
        else:
            previous = current_iteration(context["task_id"])
            if (
                context["calibrating"]
                and previous is not None
                and not calibration_is_non_regressive(previous, result)
            ):
                set_constraints(context["task_id"], dict(previous.constraints))
                set_generation_error(
                    calibration_regression_message(previous, result)
                )
            else:
                append_iteration(result)
                set_generation_error(None)
            finish_generation_run("completed")
        st.session_state.pop("generation_job", None)
        st.session_state.pop("generation_job_context", None)
        finish_generation()

    def request_generation_cancellation() -> None:
        update_run_status(
            st.session_state.generation_run_id,
            "cancelling",
        )

    render_generation_job_dialog(
        job,
        task_name=task["label"],
        model=generation_controls.model,
        temperature=generation_controls.temperature,
        batch_size=int(generation_controls.batch_size),
        iteration_number=int(context["iteration_number"]),
        on_complete=complete_generation,
        on_cancel=request_generation_cancellation,
    )

render_generation(
    dashboard_data,
    generation_controls,
    current_iteration(generation_controls.task_id),
    load_prototype_task(generation_controls.task_id),
    generation_error,
    task_iterations(generation_controls.task_id),
)
