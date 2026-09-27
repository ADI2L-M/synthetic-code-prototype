"""Complementary authentic-submission defect-detection page."""

from ui.app_data import load_dashboard_data_cached
from ui.research_dashboard import render_dashboard, render_sidebar


dashboard_data = load_dashboard_data_cached()
selected_task = render_sidebar(dashboard_data)
render_dashboard(dashboard_data, selected_task)
