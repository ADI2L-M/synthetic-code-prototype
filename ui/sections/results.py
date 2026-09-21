import pandas as pd
import streamlit as st

from models.types import DefectDefinition, IterationResult
from ui.components import display_name


def render_results(
    current: IterationResult | None,
    definitions: dict[str, DefectDefinition],
) -> None:
    if current is None:
        st.info(
            "Configure the task and select Generate Demo Batch to create the "
            "first iteration."
        )
        return

    valid_count = sum(item.validation.status == "PASS" for item in current.submissions)
    failed_count = len(current.submissions) - valid_count
    st.subheader(f"Generation Results — Iteration {current.iteration}")
    st.caption(
        f"Generated: {len(current.submissions)} · "
        f"Functionally Correct: {valid_count} · Failed: {failed_count}"
    )

    result_rows = []
    for item in current.submissions:
        labels = [
            display_name(defect_id, definitions)
            for defect_id, detected in item.defects.items()
            if detected
        ]
        result_rows.append(
            {
                "Submission": f"#{item.submission_id:02d}",
                "Functional Status": item.validation.status,
                "Tests Passed": item.validation.tests_passed,
                "Tests Failed": item.validation.tests_failed,
                "Detected Defects": ", ".join(labels)
                or (
                    "Not analysed"
                    if item.validation.status != "PASS"
                    else "None detected"
                ),
            }
        )
    st.dataframe(
        pd.DataFrame(result_rows),
        hide_index=True,
        width="stretch",
    )

    st.subheader("Submission details")
    st.caption("Expand a submission to inspect its generated Python code.")
    for item in current.submissions:
        labels = [
            display_name(defect_id, definitions)
            for defect_id, detected in item.defects.items()
            if detected
        ]
        expander = st.expander(
            f"#{item.submission_id:02d} · {item.validation.status} · "
            f"{', '.join(labels) or 'No selected defects'}",
            key=(
                f"submission_{current.task_id}_{current.iteration}_{item.submission_id}"
            ),
            on_change="rerun",
        )
        with expander:
            if expander.open:
                if item.validation.status == "PASS":
                    st.success("PASS")
                else:
                    st.error("FAIL")
                if item.validation.failure_message:
                    st.caption(item.validation.failure_message)
                st.code(item.source_code, language="python")
