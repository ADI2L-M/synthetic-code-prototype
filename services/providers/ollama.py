"""Local Ollama provider for Qwen2.5-Coder submissions."""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from enum import Enum

from dotenv import load_dotenv

from models.types import ProgrammingTask
from services.providers.llm import GenerationProvider

load_dotenv()

class OllamaModel(Enum):
    """List of available Ollama models"""

    QW25_CODER_1_5B = "qwen2.5-coder:1.5b"
    QW25_CODER_7B = "qwen2.5-coder:7b"
    DS_CODER_6_7B = "deepseek-coder:6.7b"
    GRANITE_CODE_8B = "granite-code:8b"


class OllamaProvider(GenerationProvider):
    """Generate one plain Python submission per Ollama request."""

    def __init__(
        self,
        model: OllamaModel = OllamaModel.QW25_CODER_1_5B,
        base_url: str = "http://localhost:11434",
        timeout: int = 180,
    ) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        task: ProgrammingTask,
        batch_size: int,
        iteration: int = 1,
        specification: str | None = None,
    ) -> list[str]:
        prompt = self._build_prompt(task, specification or "")
        return [
            self._generate_one(prompt, task.function_name, iteration + index)
            for index in range(batch_size)
        ]

    def _generate_one(self, prompt: str, function_name: str, seed: int) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.8, "seed": seed, "num_predict": 1200},
        }
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama returned HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                "Could not connect to Ollama at "
                f"{self.base_url}. Ollama may not be running."
            ) from exc

        response = result.get("response", "")
        if not response.strip():
            raise RuntimeError("Ollama returned an empty response.")
        return self._extract_source(response, function_name)

    @staticmethod
    def _build_prompt(task: ProgrammingTask, specification: str) -> str:
        tests = "\n".join(
            f"- args={case.args!r}; "
            + (
                f"must raise {case.raises}"
                if case.raises
                else f"expected={case.expected!r}"
            )
            for case in task.test_cases
        )
        return f"""You are generating one Python submission for a programming task.

{specification}

FUNCTIONAL TEST CASES
{tests}

INSTRUCTIONS
- Implement the function named {task.function_name}.
- The submission must pass every functional test case above.
- Handle invalid inputs and required exceptions before normal return logic.
- The listed defect options are optional characteristics for natural variation.
- Do not force a defect if it would break functional correctness.
- Use readable, conventional multiline Python.
- Do not use semicolons to compress statements.
- Return only executable Python source code.
- Do not include Markdown fences, explanations, input(), print(), file access, or network access.
"""

    @staticmethod
    def _extract_source(response: str, function_name: str) -> str:
        fenced = re.search(
            r"```(?:python|py)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE
        )
        source = fenced.group(1) if fenced else response
        start = source.find(f"def {function_name}")
        if start >= 0:
            source = source[start:]
        return source.strip()
