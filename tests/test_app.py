from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def test_initial_dashboard_renders_without_exceptions():
    app = _app()

    assert not app.exception
    assert [metric.label for metric in app.metric[:4]] == [
        "Selected task",
        "Current iteration",
        "Functionally correct",
        "Profile status",
    ]
    assert app.metric[1].value == "—"
    assert app.metric[3].value == "Not run"
    assert "Demonstration Profile" in " ".join(item.value for item in app.info)


def test_generate_button_runs_complete_demo_workflow():
    app = _app()
    app.button(key="generate_demo").click().run(timeout=30)

    assert not app.exception
    assert app.metric[1].value == "1"
    assert app.metric[2].value == "10/10"
    assert app.metric[3].value in {"Accepted", "Needs calibration"}
    iteration = app.session_state["iterations"][0]
    assert iteration.task_id == "conditional_validation"
    assert iteration.tolerance == 0.10


def test_switching_tasks_does_not_display_another_tasks_iteration():
    app = _app()
    app.button(key="generate_demo").click().run(timeout=30)
    app.selectbox(key="selected_task").select(
        app.selectbox(key="selected_task").options[1]
    ).run()

    assert not app.exception
    assert app.metric[0].value == "List Processing"
    assert app.metric[1].value == "—"
    assert app.metric[3].value == "Not run"


def test_results_and_calibration_tabs_render_on_demand():
    app = _app()
    app.button(key="generate_demo").click().run(timeout=30)

    app.session_state["workflow_tabs"] = ":material/table_view: Results"
    app.run(timeout=30)
    assert not app.exception
    assert len(app.expander) == 10
    assert any(
        "Generation Results — Iteration 1" in heading.value for heading in app.subheader
    )

    app.session_state["workflow_tabs"] = ":material/analytics: Analyse & Calibrate"
    app.run(timeout=30)
    assert not app.exception
    assert app.button(key="apply_calibration")

    app.button(key="apply_calibration").click().run(timeout=30)
    assert not app.exception
    assert len(app.session_state["iterations"]) == 2
    assert app.session_state["iterations"][1].iteration == 2
    assert app.session_state["constraints_by_task"]["conditional_validation"]


def test_analysis_uses_the_iterations_tolerance_snapshot():
    app = _app()
    app.button(key="generate_demo").click().run(timeout=30)
    app.slider(key="tolerance").set_value(0.20).run()
    app.session_state["workflow_tabs"] = ":material/analytics: Analyse & Calibrate"
    app.run(timeout=30)

    captions = " ".join(caption.value for caption in app.caption)
    assert "Tolerance: ±10%" in captions
