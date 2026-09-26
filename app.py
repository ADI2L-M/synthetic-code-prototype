import streamlit as st

from ui.state import initialise_state
from ui.styles import load_styles

st.set_page_config(
    page_title="Synthetic Code Research Prototype",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_styles()
initialise_state()

page = st.navigation(
    [
        st.Page(
            "app_pages/home.py",
            title="Home",
            icon=":material/home:",
        ),
        st.Page(
            "app_pages/generation.py",
            title="Generation",
            icon=":material/auto_awesome:",
            default=True,
        ),
        st.Page(
            "app_pages/defect_detection.py",
            title="Defect detection",
            icon=":material/analytics:",
        ),
    ],
    position="top",
)
page.run()
