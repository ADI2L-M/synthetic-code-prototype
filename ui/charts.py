import altair as alt
import pandas as pd

from models.types import DefectDefinition, IterationResult
from ui.components import display_name


def build_profile_chart(
    iteration: IterationResult,
    definitions: dict[str, DefectDefinition],
    theme_type: str,
) -> alt.Chart:
    defect_order = [
        display_name(defect_id, definitions) for defect_id in iteration.target_profile
    ]
    chart_data = pd.DataFrame(
        [
            {
                "Defect": display_name(row.defect, definitions),
                "Profile": "Target",
                "Value": row.target,
            }
            for row in iteration.comparison
        ]
        + [
            {
                "Defect": display_name(row.defect, definitions),
                "Profile": "Observed",
                "Value": row.observed,
            }
            for row in iteration.comparison
        ]
    )
    colours = ["#79A8FF", "#C4A7FF"] if theme_type == "dark" else ["#2563EB", "#7C3AED"]

    return (
        alt.Chart(chart_data)
        .mark_bar(size=24, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                "Defect:N",
                sort=defect_order,
                title=None,
                scale=alt.Scale(paddingInner=0.72, paddingOuter=0.45),
                axis=alt.Axis(
                    labelAngle=-18,
                    labelLimit=190,
                    labelPadding=12,
                    ticks=False,
                ),
            ),
            xOffset=alt.XOffset("Profile:N", sort=["Target", "Observed"]),
            y=alt.Y(
                "Value:Q",
                title="Prevalence",
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(
                    format="%",
                    tickCount=6,
                    titlePadding=24,
                    labelPadding=8,
                ),
            ),
            color=alt.Color(
                "Profile:N",
                scale=alt.Scale(domain=["Target", "Observed"], range=colours),
                legend=alt.Legend(
                    title=None, orient="top", direction="horizontal", offset=12
                ),
            ),
            tooltip=[
                alt.Tooltip("Defect:N"),
                alt.Tooltip("Profile:N"),
                alt.Tooltip("Value:Q", format=".0%"),
            ],
        )
        .properties(
            height=350,
            padding={"left": 42, "right": 28, "top": 20, "bottom": 30},
        )
        .configure_view(stroke=None)
    )
