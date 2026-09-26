"""Cached data access shared by the Streamlit pages."""

from __future__ import annotations

import streamlit as st

from services.research.dashboard import load_dashboard_data


@st.cache_data(show_spinner=False)
def load_dashboard_data_cached() -> dict:
    return load_dashboard_data()
