from dataclasses import dataclass

import streamlit as st

from models.types import ProgrammingTask


@dataclass(frozen=True)
class SidebarControls:
    task: ProgrammingTask
    batch_size: int
    tolerance: float
    generate_requested: bool
    provider_mode: str
    ollama_model: str
    ollama_base_url: str


def render_sidebar(tasks: tuple[ProgrammingTask, ...]) -> SidebarControls:
    with st.sidebar:
        st.header(":material/science: Prototype controls")
        provider_mode = st.selectbox(
            "Generation provider",
            ["Demo", "Local Ollama"],
            key="provider_mode",
        )
        ollama_model = "qwen2.5-coder:7b"
        ollama_base_url = "http://localhost:11434"
        if provider_mode == "Local Ollama":
            ollama_model = st.text_input(
                "Ollama model", value=ollama_model, key="ollama_model"
            )
            ollama_base_url = st.text_input(
                "Ollama URL", value=ollama_base_url, key="ollama_base_url"
            )
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
            "Relative prevalence tolerance",
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
            "Generate batch",
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
        provider_mode=provider_mode,
        ollama_model=ollama_model,
        ollama_base_url=ollama_base_url,
    )
