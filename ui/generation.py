"""Generation handoff view for empirical target profiles."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from ui.research_dashboard import target_dataframe


def render_generation(data: dict[str, Any]) -> None:
    """Render generation inputs without exposing the legacy demo workflow."""
    st.caption("SYNTHETIC DATA GENERATION")
    st.title("Generation")
    st.write(
        "This view is the handoff from authentic-submission analysis to synthetic "
        "generation. Select a prototype task to review the prevalence targets that "
        "the generator must reproduce."
    )

    task_id = st.selectbox(
        "Prototype task for generation",
        list(data["prototype_tasks"]),
        format_func=lambda item: data["prototype_tasks"][item]["label"],
        key="generation_task",
    )
    task = data["prototype_tasks"][task_id]

    metrics = [
        ("Target defects", len(task["target_rows"])),
        ("Mapped authentic tasks", task["authentic_task_count"]),
        ("Source correct submissions", task["functionally_correct_count"]),
    ]
    columns = st.columns(len(metrics), gap="small")
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value, border=True)

    st.subheader("Generation readiness")
    readiness = pd.DataFrame(
        [
            {"Input": "Prototype task definition", "Status": "Ready", "Source": task["definition_file"]},
            {"Input": "Empirical prevalence profile", "Status": "Ready", "Source": data["profile_source"]},
            {"Input": "Shared research detectors", "Status": "Ready", "Source": f"{data['detector_count']} detectors"},
            {"Input": "Synthetic generation runner", "Status": "Next integration step", "Source": "Generation services"},
        ]
    )
    st.dataframe(readiness, hide_index=True, width="stretch")

    st.subheader("Target profile passed to generation")
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
    st.info(
        "Execution controls will be connected after the T1/T2/T3 generation "
        "runner consumes this empirical target-profile format."
    )
