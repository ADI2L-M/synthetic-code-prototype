from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[2] / "app.py"
DETECTION_TAB = ":material/analytics: Defect detection"
HOME_TAB = ":material/home: Home"
GENERATION_PAGE = "app_pages/generation.py"
HOME_PAGE = "app_pages/home.py"
DETECTION_PAGE = "app_pages/defect_detection.py"


def _app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def _open_page(app: AppTest, page: str) -> AppTest:
    return app.switch_page(page).run()


def test_generation_is_the_default_view_and_exposes_main_controls():
    app = _app()

    assert not app.exception
    assert app.title[0].value == "Generation"
    assert [tab.label for tab in app.tabs] == [
        ":material/analytics: Target profile",
        ":material/code: Programming task",
        ":material/description: Prompt",
        ":material/table_view: Results",
        ":material/insights: Analytics",
    ]
    assert app.selectbox(key="generation_task").options == [
        "T1 · Temperature Classification",
        "T2 · Total Scores",
        "T3 · Sum to N",
    ]
    assert app.selectbox(key="generation_model").options == [
        "qwen2.5-coder:1.5b",
        "qwen2.5-coder:7b",
        "deepseek-coder:6.7b",
        "granite-code:8b",
    ]
    assert app.number_input(key="generation_batch_size").value == 10
    assert app.slider(key="generation_tolerance").value == 0.10
    assert "generate_batch" in [button.key for button in app.button]
    assert "generate_demo" not in [button.key for button in app.button]


def test_generation_main_content_has_task_and_prompt_tabs():
    app = _app()
    app.session_state["generation_content_tabs"] = ":material/code: Programming task"
    app.run()

    assert not app.exception
    assert any("T1 · Temperature Classification" in item.value for item in app.subheader)
    assert any("Functional test cases" in item.value for item in app.subheader)

    app.session_state["generation_content_tabs"] = ":material/description: Prompt"
    app.run()
    assert any("PROGRAMMING TASK" in item.value for item in app.code)


def test_home_is_accessible_as_a_separate_application_view():
    app = _open_page(_app(), HOME_PAGE)

    assert not app.exception
    assert app.title[0].value == "Synthetic code research prototype"
    assert any("Research workflow" in item.value for item in app.subheader)
    assert len(app.selectbox) == 0


def test_defect_detection_is_a_separate_complementary_view():
    app = _open_page(_app(), DETECTION_PAGE)

    assert not app.exception
    assert app.title[0].value == "Programming defect prevalence"
    assert app.selectbox(key="prototype_task").options == [
        "T1 · Temperature Classification",
        "T2 · Total Scores",
        "T3 · Sum to N",
    ]
    assert "generate_batch" not in [button.key for button in app.button]


def test_detection_view_can_switch_prototype_task():
    app = _open_page(_app(), DETECTION_PAGE)
    app.session_state["prototype_task"] = "T3"
    app.run()

    assert not app.exception
    assert app.metric[0].value == "7"
    assert app.metric[1].value == "3859"
    assert app.selectbox(key="authentic_task").options[0] == "Lab 6 Q1"


def test_authentic_task_browser_exposes_lab_12_q2_report():
    app = _open_page(_app(), DETECTION_PAGE)
    app.session_state["prototype_task"] = "T2"
    app.run()
    app.session_state["authentic_task"] = "Lab 12 Q2"
    app.run()

    assert not app.exception
    assert "Lab 12 Q2" in app.selectbox(key="authentic_task").options
    assert any("Task report browser" in item.value for item in app.subheader)
    assert any("Lab_12_Q2.json" in item.value for item in app.caption)
