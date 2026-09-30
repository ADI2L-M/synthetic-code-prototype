from dataclasses import replace
from pathlib import Path
from time import sleep

from streamlit.testing.v1 import AppTest

from models.types import (
    IterationResult,
    ProfileComparison,
    SubmissionResult,
    ValidationResult,
)
from services.generation.jobs import GenerationCancelled, GenerationJob

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


def _stored_iteration() -> IterationResult:
    return IterationResult(
        iteration=1,
        task_id="T1",
        task_name="Temperature Classification",
        target_profile={"magic_number": 0.5},
        tolerance=0.1,
        constraints={},
        specification="task specification",
        submissions=[
            SubmissionResult(
                submission_id=1,
                source_code="def classify_temperature(temp):\n    return 'cold'\n",
                validation=ValidationResult("PASS", 1, 0),
                defects={"magic_number": True},
            )
        ],
        observed_profile={"magic_number": 1.0},
        comparison=[
            ProfileComparison(
                defect="magic_number",
                target=0.5,
                observed=1.0,
                difference=0.5,
                status="Overrepresented",
                action="Reduce",
            )
        ],
    )


def test_home_is_the_default_view():
    app = _app()

    assert not app.exception
    assert app.title[0].value == "Synthetic code research prototype"
    assert any("Prototype at a glance" in item.value for item in app.subheader)


def test_generation_view_exposes_main_controls():
    app = _open_page(_app(), GENERATION_PAGE)

    assert not app.exception
    assert app.title[0].value == "Generation"
    assert [tab.label for tab in app.tabs] == [
        ":material/code: Programming task",
        ":material/analytics: Target profile",
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
        "deepseek-coder:1.3b",
        "granite-code:3b",
    ]
    assert app.number_input(key="generation_batch_size").value == 10
    assert app.slider(key="generation_temperature").value == 0.2
    assert app.slider(key="generation_tolerance").value == 0.10
    assert "generate_batch" in [button.key for button in app.button]
    assert "generate_demo" not in [button.key for button in app.button]


def test_stale_generation_state_is_recovered_on_reload():
    app = _open_page(_app(), GENERATION_PAGE)
    app.session_state["generation_in_progress"] = True
    app.run()

    assert not app.exception
    assert app.button(key="generate_batch").disabled is False


def test_generation_dialog_exposes_a_working_cancel_button():
    def worker(progress, cancel_check):
        progress("Generating submission 1 of 1", 0, 1)
        while not cancel_check():
            sleep(0.001)
        raise GenerationCancelled("Generation cancelled by user.")

    app = _open_page(_app(), GENERATION_PAGE)
    app.session_state["generation_in_progress"] = True
    app.session_state["generation_job"] = GenerationJob(worker)
    app.session_state["generation_job_context"] = {
        "task_id": "T1",
        "calibrating": False,
        "iteration_number": 1,
    }
    app.run()

    assert not app.exception
    assert app.button(key="generate_batch").disabled is True
    assert app.button(key="cancel_generation")
    app.button(key="cancel_generation").click().run()
    assert not app.exception


def test_generation_main_content_has_task_and_prompt_tabs():
    app = _open_page(_app(), GENERATION_PAGE)
    app.session_state["generation_content_tabs"] = ":material/code: Programming task"
    app.run()

    assert not app.exception
    assert any("T1 · Temperature Classification" in item.value for item in app.subheader)
    assert any("Functional test cases" in item.value for item in app.subheader)

    app.session_state["generation_content_tabs"] = ":material/description: Prompt"
    app.run()
    prompt_text = [item.value for item in app.info] + [item.value for item in app.caption]
    assert any("exact" in item and "prompts" in item for item in prompt_text)


def test_generation_analytics_browses_persisted_experiment_logs():
    app = _open_page(_app(), GENERATION_PAGE)
    app.session_state["iterations"] = [_stored_iteration()]
    app.session_state["generation_content_tabs"] = ":material/insights: Analytics"
    app.run()

    assert not app.exception
    assert any("Experiment history" in item.value for item in app.subheader)
    assert app.selectbox(key="generation_experiment_log_T1")


def test_generation_summary_keeps_stored_iteration_metadata():
    app = _open_page(_app(), GENERATION_PAGE)
    app.session_state["iterations"] = [
        replace(
            _stored_iteration(),
            model="granite-code:3b",
            temperature=0.65,
            tolerance=0.25,
        )
    ]
    app.session_state["generation_summary_by_task"] = {
        "T1": {
            "task_name": "Temperature Classification",
            "model": "granite-code:3b",
            "batch_size": 1,
            "temperature": 0.65,
            "tolerance": 0.25,
        }
    }
    app.session_state["generation_model"] = "qwen2.5-coder:1.5b"
    app.session_state["generation_temperature"] = 0.2
    app.session_state["generation_tolerance"] = 0.1
    app.run()

    assert not app.exception
    metrics = {item.label: item.value for item in app.metric}
    assert metrics["Model"] == "granite-code:3b"
    assert metrics["Batch size"] == "1"
    assert metrics["LLM temperature"] == "0.65"
    assert metrics["Tolerance floor"] == "±25%"


def test_home_is_accessible_as_a_separate_application_view():
    app = _open_page(_app(), HOME_PAGE)

    assert not app.exception
    assert app.title[0].value == "Synthetic code research prototype"
    assert any("Prototype at a glance" in item.value for item in app.subheader)
    assert any("Research basis and citation notes" in item.value for item in app.subheader)
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
