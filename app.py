import streamlit as st

from services.research.dashboard import load_dashboard_data
from ui.generation import render_generation
from ui.home import render_home
from ui.research_dashboard import render_dashboard, render_sidebar
from ui.styles import load_styles

st.set_page_config(
    page_title="Synthetic Code Research Prototype",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_styles()


@st.cache_data(show_spinner=False)
def _dashboard_data() -> dict:
    return load_dashboard_data()


try:
    dashboard_data = _dashboard_data()
except (FileNotFoundError, KeyError, ValueError) as error:
    st.error(f"Research report data could not be loaded: {error}")
    st.stop()

home_tab, generation_tab, detection_tab = st.tabs(
    [
        ":material/home: Home",
        ":material/auto_awesome: Generation",
        ":material/analytics: Defect detection",
    ],
    key="application_tabs",
    on_change="rerun",
)

with home_tab:
    if home_tab.open:
        render_home(dashboard_data)

with generation_tab:
    if generation_tab.open:
        render_generation(dashboard_data)

with detection_tab:
    if detection_tab.open:
        selected_task = render_sidebar(dashboard_data)
        render_dashboard(dashboard_data, selected_task)
