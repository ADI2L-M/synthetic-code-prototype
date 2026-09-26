"""Home view for the research prototype application."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_home(data: dict[str, Any]) -> None:
    """Render the application landing view and research workflow map."""
    st.caption("RESEARCH PROTOTYPE · SYNTHETIC CODE STUDY")
    st.title("Synthetic code research prototype")
    st.write(
        "This application separates empirical defect detection from the later "
        "synthetic-code generation phase. Start with the empirical target profile "
        "and use the tabs above to move between research views."
    )
    st.info(
        "The current empirical source is the functionally correct authentic CS1 "
        "submission dataset. Generation uses these estimates as its target input."
    )

    prototype_tasks = data["prototype_tasks"]
    total_authentic_tasks = sum(
        task["authentic_task_count"] for task in prototype_tasks.values()
    )
    total_correct_submissions = sum(
        task["functionally_correct_count"] for task in prototype_tasks.values()
    )
    metrics = [
        ("Prototype tasks", len(prototype_tasks)),
        ("Mapped authentic tasks", total_authentic_tasks),
        ("Functionally correct submissions", total_correct_submissions),
        ("Shared detectors", data["detector_count"]),
    ]
    columns = st.columns(len(metrics), gap="small")
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value, border=True)

    st.subheader("Research workflow")
    workflow = pd.DataFrame(
        [
            {
                "Stage": "Home",
                "Purpose": "Orient to the research workflow and dataset scope",
                "Status": "Available",
            },
            {
                "Stage": "Generation",
                "Purpose": "Review the empirical target handoff for synthetic generation",
                "Status": "Target profile ready",
            },
            {
                "Stage": "Defect detection",
                "Purpose": "Inspect authentic task reports and prevalence estimates",
                "Status": "Available",
            },
        ]
    )
    st.dataframe(workflow, hide_index=True, width="stretch")

    st.subheader("Current research scope")
    scope = pd.DataFrame(
        [
            {
                "Prototype task": task["label"],
                "Task family": task["task_family"],
                "Authentic tasks": task["authentic_task_count"],
                "Correct submissions": task["functionally_correct_count"],
                "Eligible targets": len(task["target_rows"]),
            }
            for task in prototype_tasks.values()
        ]
    )
    st.dataframe(scope, hide_index=True, width="stretch")
