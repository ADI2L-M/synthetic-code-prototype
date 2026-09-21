import streamlit as st

from models.types import DefectDefinition, ProgrammingTask
from ui.components import render_profile_table, render_target_cards


def render_configure(
    task: ProgrammingTask,
    independent: dict[str, float],
    dependent: dict[str, float],
    target: dict[str, float],
    definitions: dict[str, DefectDefinition],
) -> None:
    st.subheader("Programming task")
    st.markdown(f"### {task.name}")
    st.write(task.description)
    st.markdown(f"**Task Context Profile:** `{', '.join(task.contexts)}`")

    st.info(
        "**Demonstration Profile** — These values are demonstration values, "
        "not results derived from authentic student data."
    )

    st.subheader("Profile composition")
    independent_column, dependent_column = st.columns(2, gap="medium")
    with independent_column:
        st.markdown("#### Task-Independent Defect Profile")
        render_profile_table(independent, definitions)
    with dependent_column:
        st.markdown("#### Applicable Task-Dependent Defect Profile")
        if dependent:
            render_profile_table(dependent, definitions)
        else:
            st.caption("No task-dependent defects apply to this context.")

    st.subheader("Context-Aware Target Profile")
    render_target_cards(target, definitions)
    render_profile_table(target, definitions)
