import pandas as pd
import streamlit as st

from models.types import DefectDefinition, IterationResult, ProgrammingTask
from services.generation.prompt_builder import build_generation_specification
from ui.components import display_name


def render_generate(
    task: ProgrammingTask,
    target: dict[str, float],
    constraints: dict[str, str],
    definitions: dict[str, DefectDefinition],
    current: IterationResult | None,
) -> None:
    st.subheader("Generation Specification")
    st.info(
        "The specification is constructed programmatically from the Programming "
        "Task and Context-Aware Target Profile."
    )
    specification = (
        current.specification
        if current
        else build_generation_specification(task, target, constraints)
    )
    st.code(specification, language="text")

    if constraints:
        st.subheader("Active calibration constraints")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Defect": display_name(defect_id, definitions),
                        "Constraint": value,
                    }
                    for defect_id, value in constraints.items()
                ]
            ),
            hide_index=True,
            width="stretch",
        )
