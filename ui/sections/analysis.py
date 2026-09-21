from dataclasses import asdict

import pandas as pd
import streamlit as st

from models.types import DefectDefinition, IterationResult
from ui.charts import build_profile_chart
from ui.components import display_name
from ui.state import request_calibration


def _comparison_dataframe(
    current: IterationResult, definitions: dict[str, DefectDefinition]
) -> pd.DataFrame:
    table = pd.DataFrame([asdict(row) for row in current.comparison])
    table["defect"] = table["defect"].map(
        lambda defect_id: display_name(defect_id, definitions)
    )
    return table.rename(
        columns={
            "defect": "Defect",
            "target": "Target",
            "observed": "Observed",
            "difference": "Difference",
            "status": "Status",
            "action": "Action",
        }
    )


def render_analysis(
    current: IterationResult | None,
    history: list[IterationResult],
    definitions: dict[str, DefectDefinition],
) -> None:
    if current is None:
        st.info(
            "Generate a batch first to compare target and observed defect profiles."
        )
        return

    st.subheader("Target vs Observed Defect Profile")
    st.caption(
        f"Tolerance: ±{current.tolerance:.0%} percentage points · Failed "
        "submissions are excluded from the observed-profile denominator."
    )
    chart = build_profile_chart(current, definitions, st.context.theme.type)
    st.altair_chart(chart, width="stretch")

    st.dataframe(
        _comparison_dataframe(current, definitions),
        hide_index=True,
        width="stretch",
        column_config={
            "Target": st.column_config.ProgressColumn(
                "Target", min_value=0, max_value=1, format="percent"
            ),
            "Observed": st.column_config.ProgressColumn(
                "Observed", min_value=0, max_value=1, format="percent"
            ),
            "Difference": st.column_config.NumberColumn("Difference", format="percent"),
        },
    )

    if current.accepted:
        st.success(
            "All relevant discrepancies are within tolerance. Accept Synthetic "
            "Python Submissions."
        )
    else:
        st.warning(
            "One or more discrepancies exceed tolerance. Calibration actions "
            "are shown in the table above."
        )
        st.button(
            "Apply Calibration and Regenerate",
            type="primary",
            icon=":material/autorenew:",
            width="stretch",
            key="apply_calibration",
            on_click=request_calibration,
        )

    if len(history) > 1:
        st.subheader("Iteration history")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Iteration": item.iteration,
                        "Generated": len(item.submissions),
                        "Functionally correct": sum(
                            submission.validation.status == "PASS"
                            for submission in item.submissions
                        ),
                        "Tolerance": item.tolerance,
                        "Accepted": item.accepted,
                    }
                    for item in history
                ]
            ),
            hide_index=True,
            width="stretch",
            column_config={
                "Tolerance": st.column_config.NumberColumn(
                    "Tolerance", format="percent"
                )
            },
        )
