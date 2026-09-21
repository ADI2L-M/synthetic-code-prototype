import streamlit as st

from services.calibrator import calibration_constraints
from services.data_loader import load_profiles, load_tasks
from services.profile_composer import compose_target_profile, definitions_by_id
from services.workflow import run_iteration
from ui.components import render_header, render_kpis
from ui.sections.analysis import render_analysis
from ui.sections.configure import render_configure
from ui.sections.generate import render_generate
from ui.sections.results import render_results
from ui.sidebar import render_sidebar
from ui.state import (
    append_iteration,
    constraints_for,
    consume_calibration_request,
    current_iteration,
    initialise_state,
    next_iteration_number,
    set_constraints,
    task_iterations,
)
from ui.styles import load_styles

st.set_page_config(
    page_title="Synthetic Code Prototype",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_styles()
initialise_state()

tasks = load_tasks()
profiles = load_profiles()
definitions = definitions_by_id()
controls = render_sidebar(tasks)
independent, dependent, target = compose_target_profile(controls.task, profiles)
constraints = constraints_for(controls.task.id)

if controls.generate_requested:
    append_iteration(
        run_iteration(
            task=controls.task,
            target_profile=target,
            batch_size=controls.batch_size,
            iteration_number=next_iteration_number(controls.task.id),
            tolerance=controls.tolerance,
            constraints=constraints,
        )
    )

current = current_iteration(controls.task.id)

if consume_calibration_request() and current is not None:
    revised_constraints = calibration_constraints(current.comparison)
    set_constraints(controls.task.id, revised_constraints)
    append_iteration(
        run_iteration(
            task=controls.task,
            target_profile=current.target_profile,
            batch_size=controls.batch_size,
            iteration_number=next_iteration_number(controls.task.id),
            tolerance=controls.tolerance,
            constraints=revised_constraints,
        )
    )

current = current_iteration(controls.task.id)
history = task_iterations(controls.task.id)

render_header()
render_kpis(controls.task, current)

configure_tab, generate_tab, results_tab, analysis_tab = st.tabs(
    [
        ":material/settings: Configure",
        ":material/auto_awesome: Generate",
        ":material/table_view: Results",
        ":material/analytics: Analyse & Calibrate",
    ],
    key="workflow_tabs",
    on_change="rerun",
)

with configure_tab:
    if configure_tab.open:
        render_configure(controls.task, independent, dependent, target, definitions)

with generate_tab:
    if generate_tab.open:
        render_generate(
            controls.task,
            target,
            constraints,
            definitions,
            current,
        )

with results_tab:
    if results_tab.open:
        render_results(current, definitions)

with analysis_tab:
    if analysis_tab.open:
        render_analysis(current, history, definitions)
