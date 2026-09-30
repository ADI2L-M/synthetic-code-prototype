import json
from urllib.error import URLError

import pytest

from models.types import ProgrammingTask
from models.types import TestCase as TaskTestCase
from services.providers.ollama import OllamaProvider


def test_ollama_prompt_includes_generation_instructions():
    task = ProgrammingTask(
        id="T1",
        name="Temperature Classification",
        description="Classify a temperature.",
        function_name="classify_temperature",
        contexts=["conditional_logic"],
        functional_requirements=["Return a category string."],
        test_cases=[TaskTestCase(args=[10], expected="mild")],
    )

    prompt = OllamaProvider.build_prompt(task, "ASSIGNED DEFECTS")

    assert "INSTRUCTIONS" in prompt
    assert "Include at least one assigned task-independent defect" in prompt
    assert "Copy the key syntax and control-flow shape" in prompt
    assert "Return only executable Python source code" in prompt


def test_ollama_baseline_repair_prompt_does_not_add_defect_guidance():
    task = ProgrammingTask(
        id="T1",
        name="Temperature Classification",
        description="Classify a temperature.",
        function_name="classify_temperature",
        contexts=["conditional_logic"],
        functional_requirements=["Return a category string."],
        test_cases=[TaskTestCase(args=[10], expected="mild")],
    )

    prompt = OllamaProvider.build_prompt(
        task,
        "PROMPTING CONDITION: NON-ADAPTIVE BASELINE\n\nREVISION REQUEST\n\n"
        "Repair functional correctness only.",
    )

    assert "Follow only the programming task and functional requirements." in prompt
    assert "Include at least one assigned task-independent defect" not in prompt
    assert "Include at least one assigned task-dependent defect" not in prompt


def test_ollama_connection_failure_is_reported_as_runtime_error(monkeypatch):
    def unavailable(*args, **kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr("services.providers.ollama.urlopen", unavailable)

    with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
        OllamaProvider(base_url="http://localhost:11434")._generate_one(
            "prompt", "classify_temperature", 1
        )


def test_ollama_temperature_is_forwarded_to_generation_request(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"response":"def classify_temperature(temp):\\n    return \'cold\'"}'

    def generate(request, timeout):
        captured.update(json.loads(request.data.decode("utf-8")))
        return Response()

    monkeypatch.setattr("services.providers.ollama.urlopen", generate)

    OllamaProvider(temperature=0.35)._generate_one(
        "prompt", "classify_temperature", 1
    )

    assert captured["options"]["temperature"] == 0.35
