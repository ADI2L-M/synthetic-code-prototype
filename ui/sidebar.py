from dataclasses import dataclass

import streamlit as st

from models.types import ProgrammingTask


@dataclass(frozen=True)
class SidebarControls:
    task: ProgrammingTask
    batch_size: int
    tolerance: float
    generate_requested: bool


def render_sidebar(tasks: tuple[ProgrammingTask, ...]) -> SidebarControls:
    with st.sidebar:
        st.header(":material/science: Prototype controls")
        st.caption("Deterministic Demo/Mock mode")
        st.divider()

        selected_task = st.selectbox(
            "Programming Task",
            tasks,
            format_func=lambda item: item.name,
            key="selected_task",
        )
        batch_size = st.number_input(
            "Number of submissions",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            key="batch_size",
        )
        tolerance = st.slider(
            "Accepted discrepancy tolerance",
            min_value=0.0,
            max_value=0.5,
            value=0.10,
            step=0.01,
            format="%.2f",
            key="tolerance",
        )

        st.divider()
        st.caption(f"Task context: {', '.join(selected_task.contexts)}")
        generate_requested = st.button(
            "Generate Demo Batch",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
            key="generate_demo",
        )

    return SidebarControls(
        task=selected_task,
        batch_size=int(batch_size),
        tolerance=float(tolerance),
        generate_requested=generate_requested,
    )
