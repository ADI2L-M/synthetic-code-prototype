import pytest
from urllib.error import URLError

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


def test_ollama_connection_failure_is_reported_as_runtime_error(monkeypatch):
    def unavailable(*args, **kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr("services.providers.ollama.urlopen", unavailable)

    with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
        OllamaProvider(base_url="http://localhost:11434")._generate_one(
            "prompt", "classify_temperature", 1
        )
