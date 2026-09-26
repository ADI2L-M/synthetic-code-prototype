"""Generation controls and results for the empirical prototype tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st

from models.types import IterationResult, ProgrammingTask
from services.generation.prompt_builder import build_generation_specification
from ui.research_dashboard import target_dataframe

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
            index=1,
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
            "Relative prevalence tolerance",
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
        }
        for item in iteration.submissions
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    for item in iteration.submissions:
        with st.expander(f"Submission {item.submission_id} · {item.validation.status}"):
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
    task: ProgrammingTask,
    target: dict[str, float],
    current: IterationResult | None,
) -> None:
    st.write(
        "The prompt is constructed from the selected programming task, the "
        "empirical target profile, and the functional-correctness constraint."
    )
    prompt = (
        current.specification
        if current
        else build_generation_specification(task, target)
    )
    st.code(prompt, language="text")


def _render_analytics(current: IterationResult | None) -> None:
    if current is None:
        st.info("Analytics will appear after a generation batch is completed.")
        return
    valid_count = sum(
        item.validation.status == "PASS" for item in current.submissions
    )
    status = "Accepted" if current.accepted else "Needs review"
    result_columns = st.columns(3, gap="small")
    result_columns[0].metric(
        "Functionally correct", f"{valid_count}/{len(current.submissions)}"
    )
    result_columns[1].metric("Profile status", status)
    result_columns[2].metric("Relative tolerance", f"±{current.tolerance:.0%}")
    _render_comparison(current)


def render_generation(
    data: dict[str, Any],
    controls: GenerationControls,
    current: IterationResult | None,
    task: ProgrammingTask,
    error: str | None = None,
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
        ("Relative tolerance", f"±{controls.tolerance:.0%}"),
    ]
    columns = st.columns(len(metrics), gap="small")
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value, border=True)

    if error:
        st.error(error)

    target = {
        row["defect"]: row["target_prevalence"] for row in task_data["target_rows"]
    }
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
            _render_prompt(task, target, current)
    with results_tab:
        if results_tab.open:
            if current is None:
                st.info("Choose the generation controls and select Generate batch to start.")
            else:
                st.subheader(f"Latest generation · iteration {current.iteration}")
                _render_submissions(current)
    with analytics_tab:
        if analytics_tab.open:
            _render_analytics(current)
