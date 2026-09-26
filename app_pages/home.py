"""Home page for the research prototype."""

from ui.app_data import load_dashboard_data_cached
from ui.home import render_home


render_home(load_dashboard_data_cached())
