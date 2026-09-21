import altair as alt
import pandas as pd
import streamlit as st

from detectors.all import detect_defects
from models.types import IterationResult, SubmissionResult
from services.analysis import compare_profiles, observed_profile
from services.calibrator import calibration_constraints
from services.data_loader import load_profiles, load_tasks
from services.demo_provider import DemoProvider
from services.profile_composer import compose_target_profile, definitions_by_id
from services.prompt_builder import build_generation_specification
from services.validator import validate_source

st.set_page_config(page_title="Synthetic Code Prototype", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stApp"], :root {
    /* These are Streamlit's own theme tokens; they change with the active
       light/dark theme, unlike hard-coded colors or optional data attributes. */
    --dash-bg: var(--st-background-color, #f5f7fb);
    --dash-surface: var(--st-secondary-bg, #ffffff);
    --dash-surface-muted: var(--st-secondary-bg, #eef3f9);
    --dash-border: var(--st-widget-border-color, color-mix(in srgb, var(--st-body-text, #61708a) 18%, var(--dash-surface)));
    --dash-heading: var(--st-body-text, #14213d);
    --dash-text-muted: var(--st-faded-text-60, #61708a);
    --dash-sidebar: var(--st-secondary-bg, #eaf0f7);
    --dash-sidebar-text: var(--st-body-text, #17233d);
    --dash-accent: var(--st-primary, #2563eb);
    --dash-success: #15803d;
    --dash-danger: #b91c1c;
    --dash-shadow: 0 2px 10px color-mix(in srgb, var(--st-body-text, #14213d) 10%, transparent);
}

/* Keep semantic status colors readable when the native theme is dark. */
@media (prefers-color-scheme: dark) {
    :root {
        --dash-success: #58d68d;
        --dash-danger: #ff8585;
    }
}

[data-testid="stAppViewContainer"] { background: transparent !important; color: inherit; }
[data-testid="stMainBlockContainer"] {
    background: color-mix(in srgb, currentColor 3%, transparent) !important;
    color: inherit;
    border: 1px solid color-mix(in srgb, currentColor 14%, transparent);
    border-radius: 18px;
    padding: 2rem 2.25rem 2.5rem;
    width: min(calc(100% - 2rem)) !important;
    max-width: 1000px !important;
    margin: 4rem auto !important;
    box-sizing: border-box;
    box-shadow: 0 4px 18px color-mix(in srgb, currentColor 8%, transparent);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: transparent !important; border-right: 1px solid var(--dash-border); color: inherit; }
[data-testid="stSidebar"] * { color: inherit; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div { background: transparent !important; border-color: var(--dash-border); color: inherit; }
[data-baseweb="tab-list"] { gap: .5rem; border-bottom-color: color-mix(in srgb, currentColor 14%, transparent); }
[data-baseweb="tab-list"] button[role="tab"] {
    flex: 0 0 210px;
    width: 210px;
    min-width: 210px;
    max-width: 210px;
    height: 48px;
    padding: .65rem 1rem;
    border-radius: 10px 10px 0 0;
    background: color-mix(in srgb, currentColor 7%, transparent);
    color: inherit;
    transition: background-color 120ms ease, color 120ms ease;
}
[data-baseweb="tab-list"] button[role="tab"]:hover {
    background: color-mix(in srgb, currentColor 12%, transparent);
}
[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] {
    background: color-mix(in srgb, currentColor 15%, transparent);
    color: inherit;
}
.dashboard-eyebrow { color: inherit; opacity: .65; font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .2rem; }
.dashboard-title { color: inherit; font-size: 2.2rem; font-weight: 750; line-height: 1.1; margin: 0; }
.dashboard-subtitle { color: inherit; opacity: .7; font-size: 1rem; margin: .35rem 0 1.35rem; }
.section-label { color: inherit; opacity: .65; font-size: .76rem; font-weight: 750; letter-spacing: .1em; text-transform: uppercase; margin: 1.2rem 0 .5rem; }
.profile-card { background: transparent; border: 1px solid color-mix(in srgb, currentColor 18%, transparent); border-radius: 14px; padding: 1rem 1.1rem; height: auto; min-height: 170px; box-sizing: border-box; display: flex; flex-direction: column; box-shadow: var(--dash-shadow); }
.profile-card h4 { margin: 0 0 .25rem; color: inherit; font-size: 1rem}
.profile-card p { margin: 0; color: inherit; opacity: .68; font-size: .9rem; }
.profile-value { color: var(--dash-accent); font-size: 1.65rem; font-weight: 750; margin-top: auto; }
.status-pass { color: var(--dash-success); font-weight: 700; }
.status-fail { color: var(--dash-danger); font-weight: 700; }
div[data-testid="stMetric"] {
    --metric-accent: var(--st-primary, #79a8ff);
    background: color-mix(in srgb, var(--metric-accent) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--metric-accent) 42%, currentColor 12%);
    border-left: 5px solid var(--metric-accent);
    border-radius: 14px;
    padding: .8rem 1rem;
    box-shadow: var(--dash-shadow);
}
.st-key-metric_task div[data-testid="stMetric"], [class*="st-key-metric_task"] div[data-testid="stMetric"] { --metric-accent: #5B9BFF; }
.st-key-metric_iteration div[data-testid="stMetric"], [class*="st-key-metric_iteration"] div[data-testid="stMetric"] { --metric-accent: #A78BFA; }
.st-key-metric_correct div[data-testid="stMetric"], [class*="st-key-metric_correct"] div[data-testid="stMetric"] { --metric-accent: #4ADE80; }
.st-key-metric_status div[data-testid="stMetric"], [class*="st-key-metric_status"] div[data-testid="stMetric"] { --metric-accent: #FBBF24; }
div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricLabel"] { color: inherit; opacity: .7; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--metric-accent); font-size: 1.25rem; line-height: 1.2; }
[data-testid="stDataFrame"] { border: 1px solid var(--dash-border); border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

tasks = load_tasks()
profiles = load_profiles()
definitions = definitions_by_id()
if "iterations" not in st.session_state:
    st.session_state.iterations = []
if "constraints" not in st.session_state:
    st.session_state.constraints = {}
if "run_requested" not in st.session_state:
    st.session_state.run_requested = False
if "tolerance" not in st.session_state:
    st.session_state.tolerance = 0.10


def display_name(defect_id: str) -> str:
    return definitions[defect_id].display_name


def run_demo(task, target, batch_size: int) -> IterationResult:
    iteration_number = len(st.session_state.iterations) + 1
    specification = build_generation_specification(task, target, st.session_state.constraints)
    sources = DemoProvider().generate(task, batch_size, iteration_number)
    defect_ids = list(target)
    submissions = []
    for number, source in enumerate(sources, 1):
        validation = validate_source(source, task)
        defects = detect_defects(source, defect_ids) if validation.status == "PASS" else {}
        submissions.append(SubmissionResult(number, source, validation, defects))
    observed = observed_profile(submissions, defect_ids)
    comparison = compare_profiles(target, observed, st.session_state.tolerance)
    return IterationResult(iteration_number, specification, submissions, observed, comparison)


with st.sidebar:
    st.markdown("## 🧪 Prototype controls")
    st.caption("Deterministic Demo/Mock mode")
    st.markdown("---")
    selected_task = st.selectbox("Programming Task", tasks, format_func=lambda item: item.name)
    batch_size = st.number_input("Number of submissions", min_value=1, max_value=50, value=10, step=1)
    tolerance = st.slider("Accepted discrepancy tolerance", 0.0, 0.5, st.session_state.tolerance, 0.01, format="%.2f")
    st.session_state.tolerance = tolerance
    independent, dependent, target = compose_target_profile(selected_task, profiles)
    st.markdown("---")
    st.caption(f"Task context: {', '.join(selected_task.contexts)}")
    if st.button("Generate Demo Batch", type="primary", use_container_width=True):
        st.session_state.run_requested = True

if st.session_state.run_requested:
    st.session_state.iterations.append(run_demo(selected_task, target, int(batch_size)))
    st.session_state.run_requested = False

current = st.session_state.iterations[-1] if st.session_state.iterations else None
valid_count = sum(item.validation.status == "PASS" for item in current.submissions) if current else 0
accepted = bool(current and all(row["status"] == "Within tolerance" for row in current.comparison))

st.markdown('<div class="dashboard-eyebrow">Research prototype · Demo mode</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-title">Synthetic Code Generation & Calibration</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Context-aware target profiles, reproducible validation, and transparent calibration.</div>', unsafe_allow_html=True)

metric_a, metric_b = st.columns(2)
metric_c, metric_d = st.columns(2)
with metric_a, st.container(key="metric_task"):
    st.metric("Selected task", selected_task.id.replace("_", " ").title())
with metric_b, st.container(key="metric_iteration"):
    st.metric("Current iteration", current.iteration if current else "—")
with metric_c, st.container(key="metric_correct"):
    st.metric("Functionally correct", f"{valid_count}/{len(current.submissions)}" if current else "—")
with metric_d, st.container(key="metric_status"):
    st.metric("Profile status", "Accepted" if accepted else ("Needs calibration" if current else "Not run"))

configure_tab, generate_tab, results_tab, analyse_tab = st.tabs(["⚙ Configure", "✦ Generate", "▤ Results", "◌ Analyse & Calibrate"])

with configure_tab:
    st.markdown('<div class="section-label">Programming task</div>', unsafe_allow_html=True)
    st.subheader(selected_task.name)
    st.write(selected_task.description)
    st.markdown(f"**Task Context Profile:** `{', '.join(selected_task.contexts)}`")
    st.markdown('<div class="section-label">Context-aware target profile</div>', unsafe_allow_html=True)
    st.caption("All values below are demonstration values, not results from authentic student data.")
    cards = st.columns(max(1, len(target)))
    for card, defect_id, value in zip(cards, target, target.values()):
        with card:
            st.markdown(f'<div class="profile-card"><h4>{display_name(defect_id)}</h4><p>{definitions[defect_id].classification}</p><div class="profile-value">{value:.0%}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Profile composition</div>', unsafe_allow_html=True)
    profile_table = pd.DataFrame([{"Defect": display_name(key), "Classification": definitions[key].classification, "Target": value} for key, value in target.items()])
    st.dataframe(profile_table, hide_index=True, width='stretch', column_config={"Target": st.column_config.ProgressColumn("Target", min_value=0, max_value=1, format="%0.0%")})

with generate_tab:
    st.markdown('<div class="section-label">Generation specification</div>', unsafe_allow_html=True)
    st.info("The specification is constructed programmatically from the Programming Task and Context-Aware Target Profile.")
    st.code(build_generation_specification(selected_task, target, st.session_state.constraints), language="text")
    if st.session_state.constraints:
        st.markdown('<div class="section-label">Active calibration constraints</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"Defect": display_name(key), "Constraint": value} for key, value in st.session_state.constraints.items()]), hide_index=True, width='stretch')

with results_tab:
    if not current:
        st.info("Configure the task and select Generate Demo Batch to create the first iteration.")
    else:
        st.markdown(f'<div class="section-label">Generation Results — Iteration {current.iteration}</div>', unsafe_allow_html=True)
        st.write(f"Generated {len(current.submissions)} deterministic submissions using the Demo/Mock provider.")
        result_rows = []
        for item in current.submissions:
            labels = [display_name(key) for key, value in item.defects.items() if value]
            result_rows.append({"Submission": f"#{item.submission_id:02d}", "Functional Status": item.validation.status, "Detected Defects": ", ".join(labels) or ("Not analysed" if item.validation.status != "PASS" else "None detected")})
        st.dataframe(pd.DataFrame(result_rows), hide_index=True, use_container_width=True)
        st.markdown('<div class="section-label">Submission details</div>', unsafe_allow_html=True)
        for item in current.submissions:
            labels = [display_name(key) for key, value in item.defects.items() if value]
            status_class = "status-pass" if item.validation.status == "PASS" else "status-fail"
            with st.expander(f"#{item.submission_id:02d} · {item.validation.status} · {', '.join(labels) or 'No selected defects'}"):
                st.markdown(f'<span class="{status_class}">{item.validation.status}</span>', unsafe_allow_html=True)
                if item.validation.failure_message:
                    st.caption(item.validation.failure_message)
                st.code(item.source_code, language="python")

with analyse_tab:
    if not current:
        st.info("Generate a batch first to compare target and observed defect profiles.")
    else:
        st.markdown('<div class="section-label">Target vs observed defect profile</div>', unsafe_allow_html=True)
        st.caption(f"Tolerance: ±{st.session_state.tolerance:.0%} percentage points · Failed submissions are excluded from the observed-profile denominator.")
        defect_order = [display_name(defect_id) for defect_id in target]
        chart_data = pd.DataFrame(
            [
                {"Defect": display_name(defect_id), "Profile": "Target", "Value": target[defect_id]}
                for defect_id in target
            ]
            + [
                {"Defect": display_name(defect_id), "Profile": "Observed", "Value": current.observed_profile.get(defect_id, 0.0)}
                for defect_id in target
            ]
        )
        profile_chart = (
            alt.Chart(chart_data)
            .mark_bar(size=24)
            .encode(
                x=alt.X(
                    "Defect:N",
                    sort=defect_order,
                    title=None,
                    scale=alt.Scale(paddingInner=0.75, paddingOuter=0.5),
                    axis=alt.Axis(labelAngle=-20, labelLimit=180, labelPadding=10),
                ),
                xOffset=alt.XOffset("Profile:N", sort=["Target", "Observed"]),
                y=alt.Y(
                    "Value:Q",
                    title="Prevalence",
                    scale=alt.Scale(domain=[0, 1]),
                    axis=alt.Axis(format="%", tickCount=6, titlePadding=16),
                ),
                color=alt.Color(
                    "Profile:N",
                    scale=alt.Scale(domain=["Target", "Observed"], range=["#5B9BFF", "#A78BFA"]),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[alt.Tooltip("Defect:N"), alt.Tooltip("Profile:N"), alt.Tooltip("Value:Q", format=".0%")],
            )
            .properties(
                height=340,
                padding={"left": 16, "right": 16, "top": 16, "bottom": 16},
            )
            .configure_view(stroke=None)
        )
        st.altair_chart(profile_chart, use_container_width=True)
        comparison_table = pd.DataFrame(current.comparison)
        comparison_table["defect"] = comparison_table["defect"].map(display_name)
        st.dataframe(comparison_table.rename(columns={"defect": "Defect", "target": "Target", "observed": "Observed", "difference": "Difference", "status": "Status", "action": "Action"}), hide_index=True, use_container_width=True, column_config={"Target": st.column_config.ProgressColumn("Target", min_value=0, max_value=1, format="%0.0%"), "Observed": st.column_config.ProgressColumn("Observed", min_value=0, max_value=1, format="%0.0%"), "Difference": st.column_config.NumberColumn("Difference", format="%+.0%")})
        if accepted:
            st.success("All relevant discrepancies are within tolerance. Accept Synthetic Python Submissions.")
        else:
            st.warning("One or more discrepancies exceed tolerance. Calibration actions are shown in the table above.")
            if st.button("Apply Calibration and Regenerate", type="primary", use_container_width=True):
                st.session_state.constraints = calibration_constraints(current.comparison)
                st.session_state.run_requested = True
                st.rerun()
        if len(st.session_state.iterations) > 1:
            st.markdown('<div class="section-label">Iteration history</div>', unsafe_allow_html=True)
            history = pd.DataFrame([{"Iteration": item.iteration, "Generated": len(item.submissions), "Functionally correct": sum(s.validation.status == "PASS" for s in item.submissions), "Valid profile": all(row["status"] == "Within tolerance" for row in item.comparison)} for item in st.session_state.iterations])
            st.dataframe(history, hide_index=True, use_container_width=True)
