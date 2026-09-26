"""Primary synthetic-generation page."""

from services.generation.prototype_runner import run_prototype_iteration
from services.generation.prototype_tasks import load_prototype_task
from ui.app_data import load_dashboard_data_cached
from ui.generation import render_generation, render_generation_sidebar
from ui.state import append_iteration, current_iteration, next_iteration_number


dashboard_data = load_dashboard_data_cached()
generation_controls = render_generation_sidebar(dashboard_data)
generation_error = None

if generation_controls.generate_requested:
    task = dashboard_data["prototype_tasks"][generation_controls.task_id]
    target = {
        row["defect"]: row["target_prevalence"] for row in task["target_rows"]
    }
    try:
        append_iteration(
            run_prototype_iteration(
                task_id=generation_controls.task_id,
                target_profile=target,
                batch_size=generation_controls.batch_size,
                iteration_number=next_iteration_number(generation_controls.task_id),
                tolerance=generation_controls.tolerance,
                model=generation_controls.model,
                base_url=generation_controls.base_url,
            )
        )
    except (RuntimeError, ValueError) as error:
        generation_error = str(error)

render_generation(
    dashboard_data,
    generation_controls,
    current_iteration(generation_controls.task_id),
    load_prototype_task(generation_controls.task_id),
    generation_error,
)
