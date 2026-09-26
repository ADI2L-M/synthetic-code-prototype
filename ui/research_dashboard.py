"""Streamlit presentation for empirical authentic-submission prevalence."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def _percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:.2%}"


def render_header() -> None:
    st.caption("RESEARCH DATASET · AUTHENTIC SUBMISSION ANALYSIS")
    st.title("Programming defect prevalence")
    st.caption(
        "Empirical estimates from functionally correct CS1 submissions, organised by prototype task."
    )


def render_sidebar(data: dict[str, Any]) -> str:
    tasks = data["prototype_tasks"]
    with st.sidebar:
        st.header(":material/science: Research navigation")
        selected = st.selectbox(
            "Prototype task",
            list(tasks),
            format_func=lambda task_id: tasks[task_id]["label"],
            key="prototype_task",
        )
        task = tasks[selected]
        st.divider()
        st.caption(f"Task family: {task['task_family']}")
        st.caption(f"Mapped authentic tasks: {task['authentic_task_count']}")
        st.caption(f"Detectors: {data['detector_count']}")
        st.divider()
        st.caption("Source: authentic CS1 submissions")
        st.caption("Generation is available in its own application tab.")
        if st.button("Reload report data", width="stretch", key="reload_reports"):
            st.cache_data.clear()
            st.rerun()
    return selected


def render_kpis(task: dict[str, Any], detector_count: int) -> None:
    values = [
        ("Mapped authentic tasks", task["authentic_task_count"]),
        ("Functionally correct submissions", task["functionally_correct_count"]),
        ("Eligible defect targets", len(task["target_rows"])),
        ("Shared detectors", detector_count),
    ]
    columns = st.columns(len(values), gap="small")
    for column, (label, value) in zip(columns, values):
        with column:
            st.metric(label, value, border=True)


def target_dataframe(task: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Defect": row["display_name"],
                "Category": row["category"].replace("_", " ").title(),
                "Opportunity": row["opportunity_level"],
                "Target prevalence": row["target_prevalence"],
                "Pooled prevalence": row["pooled_prevalence"],
                "Eligible lab tasks": row["eligible_tasks"],
                "Valid submissions": row["valid_submissions"],
                "Affected submissions": row["affected_submissions"],
                "Task range": (
                    f"{_percentage(row['minimum_prevalence'])} – "
                    f"{_percentage(row['maximum_prevalence'])}"
                ),
            }
            for row in task["target_rows"]
        ]
    )


def render_profile(task: dict[str, Any], data: dict[str, Any]) -> None:
    st.subheader("Empirical target profile")
    st.write(
        "The target is the equal-weighted mean of prevalence across eligible "
        "authentic lab tasks. The pooled value is shown as a secondary estimate."
    )
    st.dataframe(
        target_dataframe(task),
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
    if task["omitted_not_applicable"]:
        omitted = ", ".join(
            data["defect_catalog"].get(item, {}).get("display_name", item)
            for item in task["omitted_not_applicable"]
        )
        st.info(
            "Not applicable to this task family and therefore omitted from the "
            f"generation target: {omitted}."
        )
    st.caption(
        "Detector status: "
        f"{data['detector_validation_status'].replace('_', ' ')}."
    )


def _task_prevalence_dataframe(task: dict[str, Any], defect: str) -> pd.DataFrame:
    target = next(row for row in task["target_rows"] if row["defect"] == defect)
    rows = []
    for item in target["task_prevalence"]:
        authentic = next(
            row
            for row in task["authentic_tasks"]
            if row["authentic_task"] == item["task_id"]
        )
        rows.append(
            {
                "Authentic task": item["task_id"],
                "Mapping role": authentic["mapping_role"],
                "Valid submissions": item["valid_eligible_submission_count"],
                "Affected submissions": item["affected_submission_count"],
                "Prevalence": item["prevalence"],
                "Task report": authentic["report_path"],
            }
        )
    return pd.DataFrame(rows)


def render_authentic_tasks(task: dict[str, Any], data: dict[str, Any]) -> None:
    st.subheader("Authentic task detection")
    st.write(
        "Use the task selector to inspect the prevalence for each mapped Lab/Question. "
        "The denominator is parseable, functionally correct submissions."
    )
    defect_options = [row["defect"] for row in task["target_rows"]]
    selected_defect = st.selectbox(
        "Defect to inspect",
        defect_options,
        format_func=lambda defect: data["defect_catalog"][defect]["display_name"],
        key="authentic_defect",
    )
    selected_target = next(
        row for row in task["target_rows"] if row["defect"] == selected_defect
    )
    st.caption(
        f"Task-level mean: {_percentage(selected_target['target_prevalence'])} · "
        f"Pooled: {_percentage(selected_target['pooled_prevalence'])}"
    )
    st.dataframe(
        _task_prevalence_dataframe(task, selected_defect),
        hide_index=True,
        width="stretch",
        column_config={
            "Prevalence": st.column_config.ProgressColumn(
                min_value=0, max_value=1, format="percent"
            )
        },
    )

    st.subheader("Task report browser")
    labels = [row["authentic_task"] for row in task["authentic_tasks"]]
    selected_task = st.selectbox(
        "Authentic task report",
        labels,
        key="authentic_task",
    )
    report_task = next(
        row for row in task["authentic_tasks"] if row["authentic_task"] == selected_task
    )
    report_rows = []
    for defect, result in report_task["defects"].items():
        report_rows.append(
            {
                "Defect": data["defect_catalog"].get(defect, {}).get(
                    "display_name", defect
                ),
                "Eligibility": result["eligibility"],
                "Prevalence": result["prevalence"],
                "Affected": result["affected_submission_count"],
                "Denominator": result["eligible_denominator"],
                "Raw detections": result["raw_detected_submission_count"],
                "Examples": len(result["example_detections"]),
            }
        )
    st.dataframe(
        pd.DataFrame(report_rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Prevalence": st.column_config.ProgressColumn(
                min_value=0, max_value=1, format="percent"
            )
        },
    )
    st.caption(f"Report file: {report_task['report_path']}")


def render_method(task: dict[str, Any], data: dict[str, Any]) -> None:
    st.subheader("Detection and prevalence method")
    st.markdown(
        "The dashboard uses the shared research detector registry for both the "
        "authentic analysis and later synthetic generation. Raw detections are "
        "kept separate from task eligibility."
    )
    method_rows = [
        {"Field": "Prototype task", "Value": str(task["id"])},
        {"Field": "Task definition", "Value": str(task["definition_file"])},
        {"Field": "Detector count", "Value": str(data["detector_count"])},
        {"Field": "Profile source", "Value": str(data["profile_source"])},
        {"Field": "Primary estimator", "Value": str(data["primary_estimator"])},
        {"Field": "Secondary estimator", "Value": str(data["secondary_estimator"])},
        {"Field": "Denominator", "Value": str(data["denominator_definition"])},
    ]
    st.dataframe(pd.DataFrame(method_rows), hide_index=True, width="stretch")

    st.subheader("Defect definitions covered")
    definition_rows = [
        {
            "Defect": row["display_name"],
            "Category": row["category"].replace("_", " ").title(),
            "Definition": data["defect_catalog"][row["defect"]]["definition"],
        }
        for row in task["target_rows"]
    ]
    st.dataframe(pd.DataFrame(definition_rows), hide_index=True, width="stretch")


def render_dashboard(data: dict[str, Any], selected_task: str) -> None:
    task = data["prototype_tasks"][selected_task]
    render_header()
    render_kpis(task, data["detector_count"])

    profile_tab, authentic_tab, method_tab = st.tabs(
        [
            ":material/analytics: Prevalence profile",
            ":material/table_view: Authentic task detection",
            ":material/info: Method & coverage",
        ]
    )
    with profile_tab:
        render_profile(task, data)
    with authentic_tab:
        render_authentic_tasks(task, data)
    with method_tab:
        render_method(task, data)
