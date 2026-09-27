"""Primary synthetic-generation page."""

from services.generation.calibrator import (
    calibration_constraints,
    calibration_is_non_regressive,
    calibration_regression_message,
)
from services.generation.prototype_runner import run_prototype_iteration
from services.generation.prototype_tasks import load_prototype_task
from ui.app_data import load_dashboard_data_cached
from ui.generation import render_generation, render_generation_sidebar
from ui.state import (
    append_iteration,
    constraints_for,
    consume_calibration_request,
    current_iteration,
    next_iteration_number,
    set_constraints,
    task_iterations,
)

dashboard_data = load_dashboard_data_cached()
generation_controls = render_generation_sidebar(dashboard_data)
generation_error = None
task = dashboard_data["prototype_tasks"][generation_controls.task_id]
current = current_iteration(generation_controls.task_id)
calibration_requested = consume_calibration_request()

if calibration_requested and current is not None:
    set_constraints(
        generation_controls.task_id,
        calibration_constraints(current.comparison),
    )

active_constraints = constraints_for(generation_controls.task_id)
generate_requested = generation_controls.generate_requested or calibration_requested

if generate_requested:
    target = {
        row["defect"]: row["target_prevalence"] for row in task["target_rows"]
    }
    try:
        candidate = run_prototype_iteration(
            task_id=generation_controls.task_id,
            target_profile=target,
            batch_size=generation_controls.batch_size,
            iteration_number=next_iteration_number(generation_controls.task_id),
            tolerance=generation_controls.tolerance,
            model=generation_controls.model,
            base_url=generation_controls.base_url,
            constraints=active_constraints,
        )
        if (
            calibration_requested
            and current is not None
            and not calibration_is_non_regressive(current, candidate)
        ):
            set_constraints(
                generation_controls.task_id,
                dict(current.constraints),
            )
            generation_error = calibration_regression_message(current, candidate)
        else:
            append_iteration(candidate)
    except (RuntimeError, ValueError) as error:
        generation_error = str(error)

render_generation(
    dashboard_data,
    generation_controls,
    current_iteration(generation_controls.task_id),
    load_prototype_task(generation_controls.task_id),
    generation_error,
    task_iterations(generation_controls.task_id),
)
