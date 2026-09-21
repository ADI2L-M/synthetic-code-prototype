import pandas as pd
import streamlit as st

from models.types import DefectDefinition, IterationResult, ProgrammingTask


def display_name(defect_id: str, definitions: dict[str, DefectDefinition]) -> str:
    return definitions[defect_id].display_name


def render_header() -> None:
    st.caption("RESEARCH PROTOTYPE · DEMO MODE")
    st.title("Synthetic Code Generation & Calibration")
    st.caption(
        "Context-aware target profiles, reproducible validation, and transparent calibration."
    )


def render_kpis(
    selected_task: ProgrammingTask, current: IterationResult | None
) -> None:
    valid_count = (
        sum(item.validation.status == "PASS" for item in current.submissions)
        if current
        else 0
    )
    task_label = selected_task.name.split("—", maxsplit=1)[-1].strip()
    values = (
        ("metric_task", "Selected task", task_label),
        (
            "metric_iteration",
            "Current iteration",
            current.iteration if current else "—",
        ),
        (
            "metric_correct",
            "Functionally correct",
            f"{valid_count}/{len(current.submissions)}" if current else "—",
        ),
        (
            "metric_status",
            "Profile status",
            "Accepted"
            if current and current.accepted
            else ("Needs calibration" if current else "Not run"),
        ),
    )

    first_row = st.columns(2, gap="small")
    second_row = st.columns(2, gap="small")
    for column, (key, label, value) in zip(first_row + second_row, values):
        with column, st.container(key=key):
            st.metric(label, value, border=True, height=112)


def profile_dataframe(
    profile: dict[str, float], definitions: dict[str, DefectDefinition]
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Defect": display_name(defect_id, definitions),
                "Classification": definitions[defect_id].classification,
                "Target": value,
            }
            for defect_id, value in profile.items()
        ]
    )


def render_profile_table(
    profile: dict[str, float], definitions: dict[str, DefectDefinition]
) -> None:
    st.dataframe(
        profile_dataframe(profile, definitions),
        hide_index=True,
        width="stretch",
        column_config={
            "Target": st.column_config.ProgressColumn(
                "Target", min_value=0, max_value=1, format="percent"
            )
        },
    )


def render_target_cards(
    target: dict[str, float], definitions: dict[str, DefectDefinition]
) -> None:
    cards = st.columns(len(target), gap="small", border=True)
    for card, (defect_id, value) in zip(cards, target.items()):
        card.markdown(f"**{display_name(defect_id, definitions)}**")
        card.caption(definitions[defect_id].classification)
        card.metric("Target prevalence", f"{value:.0%}")
