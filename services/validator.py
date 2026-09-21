import json
import subprocess
import sys
import tempfile
from pathlib import Path

from models.types import ProgrammingTask, ValidationResult


def validate_source(
    source: str, task: ProgrammingTask, timeout_seconds: int = 3
) -> ValidationResult:
    payload = {
        "source": source,
        "function_name": task.function_name,
        "test_cases": [case.__dict__ for case in task.test_cases],
    }
    runner = Path(__file__).with_name("validation_runner.py")
    with tempfile.TemporaryDirectory() as directory:
        try:
            completed = subprocess.run(
                [sys.executable, str(runner)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=directory,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                "FAIL", 0, len(task.test_cases), "Execution timed out", timed_out=True
            )
        if not completed.stdout.strip():
            return ValidationResult(
                "FAIL",
                0,
                len(task.test_cases),
                completed.stderr.strip() or "No validation result",
                error=completed.stderr.strip(),
            )
        try:
            return ValidationResult(**json.loads(completed.stdout))
        except (json.JSONDecodeError, TypeError) as exc:
            return ValidationResult(
                "FAIL",
                0,
                len(task.test_cases),
                str(exc),
                error=completed.stderr.strip(),
            )
