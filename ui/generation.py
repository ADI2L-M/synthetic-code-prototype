"""Generation controls and results for the empirical prototype tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st

from models.types import IterationResult, ProgrammingTask
from services.generation.analytics import (
    defect_analytics_rows,
    generation_quality,
    iteration_history_rows,
)
from services.generation.export import iteration_export_archive
from ui.research_dashboard import target_dataframe
from ui.state import request_calibration as _request_calibration

OLLAMA_MODELS = (
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:7b",
    "deepseek-coder:6.7b",
    "granite-code:8b",
)


@dataclass(frozen=True)
class GenerationControls:
    task_id: str
    model: str
    batch_size: int
    tolerance: float
    base_url: str
    generate_requested: bool


def render_generation_sidebar(data: dict[str, Any]) -> GenerationControls:
    """Render the generation controls in the sidebar and return their values."""
    with st.sidebar:
        st.header(":material/auto_awesome: Generation controls")
        task_id = st.selectbox(
            "Prototype task",
            list(data["prototype_tasks"]),
            format_func=lambda item: data["prototype_tasks"][item]["label"],
            key="generation_task",
        )
        model = st.selectbox(
            "Model",
            OLLAMA_MODELS,
            index=0,
            key="generation_model",
        )
        batch_size = st.number_input(
            "Submissions to generate",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            key="generation_batch_size",
        )
        tolerance = st.slider(
            "Minimum relative tolerance",
            min_value=0.0,
            max_value=0.5,
            value=0.10,
            step=0.01,
            format="%.2f",
            key="generation_tolerance",
        )
        with st.expander("Connection settings"):
            base_url = st.text_input(
                "Ollama URL",
                value="http://localhost:11434",
                key="generation_base_url",
            )
        st.divider()
        generate_requested = st.button(
            "Generate batch",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
            key="generate_batch",
        )
        st.caption("Generation uses the empirical target profile and validates every submission.")

    return GenerationControls(
        task_id=task_id,
        model=model,
        batch_size=int(batch_size),
        tolerance=float(tolerance),
        base_url=base_url,
        generate_requested=generate_requested,
    )


def _render_comparison(iteration: IterationResult) -> None:
    rows = [
        {
            "Defect": item.defect.replace("_", " ").title(),
            "Guided": iteration.planned_assignment_counts.get(item.defect, 0),
            "Target": item.target,
            "Observed": item.observed,
            "Difference": item.difference,
            "Status": item.status,
            "Action": item.action,
        }
        for item in iteration.comparison
    ]
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Target": st.column_config.ProgressColumn(
                min_value=0, max_value=1, format="percent"
            ),
            "Observed": st.column_config.ProgressColumn(
                min_value=0, max_value=1, format="percent"
            ),
        },
    )


def _render_submissions(iteration: IterationResult) -> None:
    st.subheader("Generated submissions")
    rows = [
        {
            "Submission": item.submission_id,
            "Functional validation": item.validation.status,
            "Tests passed": item.validation.tests_passed,
            "Tests failed": item.validation.tests_failed,
            "Attempts": item.generation_attempts,
            "Category requirement": (
                "Met" if item.category_requirements_met else "Not met"
            ),
            "Guided defects": ", ".join(item.assigned_defects) or "Clean",
            "Detected defects": ", ".join(
                defect for defect, present in item.defects.items() if present
            )
            or "None",
        }
        for item in iteration.submissions
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    for item in iteration.submissions:
        detected = ", ".join(
            defect for defect, present in item.defects.items() if present
        ) or "None"
        with st.expander(
            f"Submission {item.submission_id} · {item.validation.status} · "
            f"guided: {', '.join(item.assigned_defects) or 'clean'}"
        ):
            st.caption(f"Detected defects: {detected}")
            if item.category_requirements_met:
                st.caption(
                    f"Category requirement met after {item.generation_attempts} "
                    "attempt(s): at least one task-independent and one "
                    "task-dependent defect."
                )
            else:
                missing = ", ".join(item.missing_defect_categories) or "unknown"
                st.warning(
                    f"Category requirement not met after {item.generation_attempts} "
                    f"attempt(s). Missing: {missing}."
                )
            st.code(item.source_code, language="python")
            if item.validation.failure_message:
                st.caption(item.validation.failure_message)


def _render_programming_task(task: ProgrammingTask) -> None:
    st.subheader(task.name)
    st.write(task.description)
    st.dataframe(
        pd.DataFrame(
            [
                {"Field": "Function", "Value": task.function_name},
                {"Field": "Contexts", "Value": ", ".join(task.contexts)},
                {
                    "Field": "Functional requirements",
                    "Value": "\n".join(f"- {item}" for item in task.functional_requirements),
                },
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.subheader("Functional test cases")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Arguments": repr(case.args),
                    "Expected": repr(case.expected),
                    "Raises": case.raises or "—",
                }
                for case in task.test_cases
            ]
        ),
        hide_index=True,
        width="stretch",
    )


def _render_prompt(
    current: IterationResult | None,
) -> None:
    if current is None:
        st.info(
            "The exact provider prompts will appear here after a generation "
            "batch is run."
        )
        return

    st.caption(
        "These are the exact prompts captured immediately before each provider "
        "request. The prompt is shown separately for every submission because "
        "assigned defect guidance can differ."
    )
    for item in current.submissions:
        label = ", ".join(item.assigned_defects) or "clean control"
        with st.expander(f"Submission {item.submission_id} · {label}"):
            st.code(item.prompt, language="text")


def _open_iteration_overlay(iteration_number: int) -> None:
    st.session_state["generation_overlay_iteration"] = iteration_number


def _close_iteration_overlay() -> None:
    st.session_state.pop("generation_overlay_iteration", None)


@st.dialog(
    "Generation iteration",
    width="large",
    dismissible=True,
    on_dismiss=_close_iteration_overlay,
)
def _render_iteration_overlay(iteration: IterationResult) -> None:
    """Show one iteration's generated submissions in an overlay card."""
    quality = generation_quality(iteration)
    st.caption(
        f"{iteration.task_id} · iteration {iteration.iteration} · "
        f"{iteration.model or 'model unavailable'}"
    )
    metrics = [
        ("Submissions", str(quality["total_submissions"])),
        ("Functional pass rate", f"{quality['functional_pass_rate']:.0%}"),
        ("Category requirement", f"{quality['category_requirement_rate']:.0%}"),
        ("Average attempts", f"{quality['average_attempts']:.1f}"),
    ]
    columns = st.columns(4, gap="small")
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value, border=True)
    _render_submissions(iteration)


def _render_iteration_explorer(
    history: list[IterationResult], task_id: str
) -> None:
    """Render iteration selection, overlay review, and ZIP export controls."""
    if not history:
        st.info("No generation iterations are available yet.")
        return

    st.subheader("Iteration explorer")
    labels = [
        f"Iteration {item.iteration} · {item.model or 'model unavailable'}"
        for item in history
    ]
    selected_label = st.selectbox(
        "Iteration to inspect",
        labels,
        index=len(labels) - 1,
        key=f"generation_iteration_selector_{task_id}",
    )
    selected = history[labels.index(selected_label)]
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        st.button(
            "View generated code",
            icon=":material/visibility:",
            on_click=_open_iteration_overlay,
            args=(selected.iteration,),
            key=f"view_iteration_{task_id}_{selected.iteration}",
        )
        st.download_button(
            "Export iteration code",
            data=iteration_export_archive(selected),
            file_name=f"{task_id.lower()}_iteration_{selected.iteration}.zip",
            mime="application/zip",
            icon=":material/download:",
            key=f"export_iteration_{task_id}_{selected.iteration}",
        )

    if st.session_state.get("generation_overlay_iteration") == selected.iteration:
        _render_iteration_overlay(selected)


def _render_analytics(
    current: IterationResult | None,
    history: list[IterationResult] | None = None,
) -> None:
    if current is None:
        st.info("Analytics will appear after a generation batch is completed.")
        return
    quality = generation_quality(current)
    status = "Accepted" if current.accepted else "Needs review"
    st.subheader("Generation quality")
    st.caption(
        "Observed prevalence uses only functionally valid submissions. Profile "
        "status includes synthetic sampling uncertainty and authentic task-level "
        "uncertainty; the target is not treated as an exact batch quota."
    )
    quality_metrics = [
        ("Functional pass rate", f"{quality['functional_pass_rate']:.0%}"),
        (
            "Category requirement",
            f"{quality['category_requirement_rate']:.0%}",
        ),
        (
            "Valid denominator",
            f"{quality['valid_submissions']}/{quality['total_submissions']}",
        ),
        ("Average attempts", f"{quality['average_attempts']:.1f}"),
    ]
    columns = st.columns(4, gap="small")
    for column, (label, value) in zip(columns, quality_metrics):
        with column:
            st.metric(label, value, border=True)

    st.subheader("Defect generation profile")
    analytics_rows = defect_analytics_rows(current)
    profile = pd.DataFrame(analytics_rows).set_index("Defect")[["Target", "Observed"]]
    st.bar_chart(profile, y_label="Prevalence", x_label="Defect")
    st.dataframe(
        pd.DataFrame(analytics_rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Target": st.column_config.ProgressColumn(
                min_value=0, max_value=1, format="percent"
            ),
            "Observed": st.column_config.ProgressColumn(
                min_value=0, max_value=1, format="percent"
            ),
            "Target standard error": st.column_config.NumberColumn(
                format="percent"
            ),
            "Observed 95% low": st.column_config.NumberColumn(format="percent"),
            "Observed 95% high": st.column_config.NumberColumn(format="percent"),
            "Decision margin": st.column_config.NumberColumn(format="percent"),
            "Difference": st.column_config.NumberColumn(format="percent"),
        },
    )

    st.subheader("Profile status")
    st.caption(f"{status} · relative tolerance ±{current.tolerance:.0%}")
    if current.constraints:
        st.subheader("Active calibration adjustments")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Defect": defect.replace("_", " ").title(),
                        "Adjustment": instruction,
                    }
                    for defect, instruction in current.constraints.items()
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    if history and len(history) > 1:
        st.subheader("Calibration history")
        st.dataframe(
            pd.DataFrame(iteration_history_rows(history)),
            hide_index=True,
            width="stretch",
            column_config={
                "Pass rate": st.column_config.NumberColumn(format="percent"),
                "Category coverage": st.column_config.NumberColumn(
                    format="percent"
                ),
                "Average attempts": st.column_config.NumberColumn(format="%.1f"),
            },
        )
    if not current.accepted:
        st.button(
            "Apply calibration and regenerate",
            type="primary",
            icon=":material/autorenew:",
            width="stretch",
            key="apply_generation_calibration",
            on_click=_request_calibration,
        )


def render_generation(
    data: dict[str, Any],
    controls: GenerationControls,
    current: IterationResult | None,
    task: ProgrammingTask,
    error: str | None = None,
    history: list[IterationResult] | None = None,
) -> None:
    """Render generation inputs, empirical targets, and the latest batch."""
    task_data = data["prototype_tasks"][controls.task_id]
    st.caption("SYNTHETIC DATA GENERATION")
    st.title("Generation")
    st.write(
        "Generate functionally correct T1/T2/T3 submissions against the empirical "
        "prevalence target. Defect detection remains available as a complementary "
        "research view."
    )

    metrics = [
        ("Selected task", task_data["label"]),
        ("Model", controls.model),
        ("Batch size", controls.batch_size),
        ("Tolerance floor", f"±{controls.tolerance:.0%}"),
    ]
    for start in range(0, len(metrics), 2):
        columns = st.columns(2, gap="small")
        for column, (label, value) in zip(columns, metrics[start : start + 2]):
            with column:
                st.metric(label, value, border=True)

    if error:
        st.error(error)

    target_tab, task_tab, prompt_tab, results_tab, analytics_tab = st.tabs(
        [
            ":material/analytics: Target profile",
            ":material/code: Programming task",
            ":material/description: Prompt",
            ":material/table_view: Results",
            ":material/insights: Analytics",
        ],
        key="generation_content_tabs",
        on_change="rerun",
    )
    with target_tab:
        if target_tab.open:
            st.subheader("Empirical target profile")
            st.dataframe(
                target_dataframe(task_data),
                hide_index=True,
                width="stretch",
                column_config={
                    "Target prevalence": st.column_config.ProgressColumn(
                        min_value=0, max_value=1, format="percent"
                    ),
                    "Pooled prevalence": st.column_config.ProgressColumn(
                        min_value=0, max_value=1, format="percent"
                    ),
                },
            )
    with task_tab:
        if task_tab.open:
            _render_programming_task(task)
    with prompt_tab:
        if prompt_tab.open:
            _render_prompt(current)
    with results_tab:
        if results_tab.open:
            if current is None:
                st.info("Choose the generation controls and select Generate batch to start.")
            else:
                st.subheader(f"Latest generation · iteration {current.iteration}")
                _render_submissions(current)
                _render_iteration_explorer(history or [current], controls.task_id)
    with analytics_tab:
        if analytics_tab.open:
            _render_analytics(current, history)
