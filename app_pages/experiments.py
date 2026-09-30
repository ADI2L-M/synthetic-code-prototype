"""History and provenance view for reproducible generation experiments."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from services.generation.experiment import load_experiment_logs
from services.generation.storage import list_runs


def _condition_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for condition, metrics in record.get("condition_summary", {}).items():
        rows.append(
            {
                "Condition": condition,
                "Functional pass rate": metrics.get("functional_pass_rate"),
                "Task-independent coverage": metrics.get("independent_coverage"),
                "Task-dependent coverage": metrics.get("dependent_coverage"),
                "Mean absolute profile error": metrics.get(
                    "mean_absolute_profile_error"
                ),
                "Within-tolerance rate": metrics.get("within_tolerance_rate"),
            }
        )
    return rows


def _run_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for run in record.get("runs", []):
        final = run.get("iterations", [])[-1] if run.get("iterations") else {}
        metrics = final.get("metrics", {})
        rows.append(
            {
                "Run": run.get("run_id"),
                "Condition": run.get("condition"),
                "Repetition": run.get("repetition"),
                "Iterations": run.get("iteration_count"),
                "Selected iteration": run.get("selected_iteration"),
                "Stop reason": run.get("stop_reason"),
                "Valid submissions": metrics.get("valid_submissions"),
                "Profile error": metrics.get("mean_absolute_profile_error"),
                "Out-of-tolerance defects": ", ".join(
                    run.get("selected_out_of_tolerance", [])
                ),
            }
        )
    return rows


def _render_experiment_history() -> None:
    records = load_experiment_logs()
    st.subheader("Experiment history")
    st.caption(
        "Each record is an append-only comparison of the baseline, task-aware, "
        "and iterative prompting conditions. Source code is not stored in the "
        "experiment log."
    )
    if not records:
        st.info("No experiment logs are available yet.")
        return

    labels = [
        (
            f"{record.get('experiment_id', 'unknown')} · "
            f"{record.get('config', {}).get('task_id', 'unknown')} · "
            f"{record.get('created_at_utc', '')}"
        )
        for record in records
    ]
    selected_label = st.selectbox(
        "Experiment record",
        labels,
        index=len(labels) - 1,
        key="experiment_history_record",
    )
    selected = records[labels.index(selected_label)]
    config = selected.get("config", {})
    provenance = selected.get("provenance", {})

    summary = [
        ("Task", config.get("task_id", "unknown")),
        ("Batch size", config.get("batch_size", "unknown")),
        ("Repetitions", config.get("repetitions", "unknown")),
        ("Temperature", config.get("temperature", "unknown")),
    ]
    columns = st.columns(4, gap="small")
    for column, (label, value) in zip(columns, summary):
        with column:
            st.metric(label, value, border=True)

    st.caption(
        f"Created {selected.get('created_at_utc', 'unknown')} · "
        f"{selected.get('_log_file', 'unknown')} line "
        f"{selected.get('_line_number', 'unknown')}"
    )
    st.dataframe(
        pd.DataFrame(_condition_rows(selected)),
        hide_index=True,
        width="stretch",
        column_config={
            "Functional pass rate": st.column_config.NumberColumn(format="percent"),
            "Task-independent coverage": st.column_config.NumberColumn(format="percent"),
            "Task-dependent coverage": st.column_config.NumberColumn(format="percent"),
            "Mean absolute profile error": st.column_config.NumberColumn(
                format="percent"
            ),
            "Within-tolerance rate": st.column_config.NumberColumn(format="percent"),
        },
    )
    with st.expander("Run details"):
        st.dataframe(pd.DataFrame(_run_rows(selected)), hide_index=True, width="stretch")
    with st.expander("Runtime provenance"):
        st.json(provenance)
    st.download_button(
        "Download selected experiment record",
        data=json.dumps(selected, indent=2, ensure_ascii=False),
        file_name=f"{selected.get('experiment_id', 'experiment')}.json",
        mime="application/json",
        icon=":material/download:",
        key="download_selected_experiment",
    )


def _render_generation_runs() -> None:
    st.subheader("Interactive generation runs")
    st.caption(
        "Interactive batches are stored separately from CLI experiment logs, "
        "including their lifecycle status, model settings, and completion errors."
    )
    runs = list_runs(limit=50)
    if not runs:
        st.info("No interactive generation runs are available yet.")
        return
    rows = [
        {
            "Run": run.get("run_id"),
            "Status": run.get("status"),
            "Task": run.get("task_id"),
            "Model": run.get("model"),
            "Batch size": run.get("batch_size"),
            "Temperature": run.get("temperature"),
            "Created": run.get("created_at"),
            "Completed": run.get("completed_at"),
            "Error": run.get("error_message"),
        }
        for run in runs
    ]
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Temperature": st.column_config.NumberColumn(format="%.2f"),
        },
    )


st.title("Experiments")
st.write(
    "Review reproducible CLI comparisons and the persisted lifecycle of interactive "
    "generation runs."
)
_render_experiment_history()
st.divider()
_render_generation_runs()

