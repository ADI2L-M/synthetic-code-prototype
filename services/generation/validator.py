import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from models.types import ProgrammingTask, ValidationResult

UNSAFE_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "open",
}
UNSAFE_MODULES = {
    "ctypes",
    "importlib",
    "os",
    "pathlib",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "sys",
    "urllib",
}


def _unsafe_construct(source: str) -> str | None:
    """Return a reason when generated source leaves the safe task subset."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, UnicodeError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = (
                node.module or "."
                if isinstance(node, ast.ImportFrom)
                else node.names[0].name
            )
            root = module.split(".", maxsplit=1)[0]
            if root in UNSAFE_MODULES or isinstance(node, ast.ImportFrom):
                return f"imports are not allowed: {module}"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in UNSAFE_CALLS:
                return f"unsafe call is not allowed: {node.func.id}"
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in UNSAFE_MODULES
            ):
                return f"unsafe module access is not allowed: {node.func.value.id}"
    return None


def validate_source(
    source: str, task: ProgrammingTask, timeout_seconds: int = 3
) -> ValidationResult:
    unsafe_reason = _unsafe_construct(source)
    if unsafe_reason:
        return ValidationResult(
            "FAIL",
            0,
            len(task.test_cases),
            f"Unsafe source rejected before execution: {unsafe_reason}",
            error=unsafe_reason,
        )
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
