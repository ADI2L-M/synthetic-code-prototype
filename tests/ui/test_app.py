from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[2] / "app.py"


def _app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def _open_tab(app: AppTest, label: str) -> AppTest:
    app.session_state["application_tabs"] = label
    return app.run()


def test_home_exposes_separate_generation_and_detection_tabs():
    app = _app()

    assert not app.exception
    assert app.title[0].value == "Synthetic code research prototype"
    assert [tab.label for tab in app.tabs] == [
        ":material/home: Home",
        ":material/auto_awesome: Generation",
        ":material/analytics: Defect detection",
    ]
    assert "generate_demo" not in [button.key for button in app.button]
    assert len(app.selectbox) == 0


def test_default_task_shows_empirical_metrics_and_profile():
    app = _open_tab(_app(), ":material/analytics: Defect detection")

    assert app.title[0].value == "Programming defect prevalence"
    labels = [metric.label for metric in app.metric]
    assert labels[:4] == [
        "Mapped authentic tasks",
        "Functionally correct submissions",
        "Eligible defect targets",
        "Shared detectors",
    ]
    assert app.metric[0].value == "20"
    assert app.metric[1].value == "10778"
    assert app.metric[2].value == "12"
    assert app.metric[3].value == "18"
    assert any("Empirical target profile" in item.value for item in app.subheader)


def test_switching_prototype_task_updates_authentic_scope():
    app = _app()
    app.session_state["application_tabs"] = ":material/analytics: Defect detection"
    app.session_state["prototype_task"] = "T3"
    app.run()

    assert not app.exception
    assert app.metric[0].value == "7"
    assert app.metric[1].value == "3859"
    assert app.selectbox(key="authentic_task").options[0] == "Lab 6 Q1"


def test_authentic_task_browser_exposes_lab_12_q2_report():
    app = _app()
    app.session_state["application_tabs"] = ":material/analytics: Defect detection"
    app.session_state["prototype_task"] = "T2"
    app.session_state["authentic_task"] = "Lab 12 Q2"
    app.run()

    assert not app.exception
    assert "Lab 12 Q2" in app.selectbox(key="authentic_task").options
    assert any("Task report browser" in item.value for item in app.subheader)
    assert any("Lab_12_Q2.json" in item.value for item in app.caption)


def test_generation_tab_exposes_empirical_handoff_without_demo_controls():
    app = _open_tab(_app(), ":material/auto_awesome: Generation")

    assert not app.exception
    assert app.title[0].value == "Generation"
    assert app.selectbox(key="generation_task").options == [
        "T1 · Temperature Classification",
        "T2 · Total Scores",
        "T3 · Sum to N",
    ]
    assert any("Target profile passed to generation" in item.value for item in app.subheader)
    assert "generate_demo" not in [button.key for button in app.button]
