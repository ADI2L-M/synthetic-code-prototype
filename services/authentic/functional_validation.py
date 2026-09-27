"""Reference-derived functional validation for authentic lab submissions.

This module deliberately contains no defect detection. It uses the right-answer
column as a functional oracle and supports the mixed response formats present
in the authentic workbook: executable scripts, function submissions, and
structured answer values.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from models.types import ValidationResult

_DEFAULT_CASES = (
    Path(__file__).resolve().parents[2]
    / "research-notes"
    / "functional-tests"
    / "authentic_test_cases.json"
)
_RUNNER = Path(__file__).with_name("validation_runner.py")


@dataclass(frozen=True)
class AuthenticTestPlan:
    label: str
    mode: str
    cases: tuple[dict[str, Any], ...] = ()
    function_name: str | None = None
    prelude: str = ""


def load_test_plans(path: Path = _DEFAULT_CASES) -> dict[str, AuthenticTestPlan]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    plans: dict[str, AuthenticTestPlan] = {}
    for label, definition in raw.items():
        plans[label] = AuthenticTestPlan(
            label=label,
            mode=definition["mode"],
            cases=tuple(definition.get("cases", [])),
            function_name=definition.get("function_name"),
            prelude=definition.get("prelude", ""),
        )
    return plans


def _normalise_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return tuple(_normalise_value(item) for item in value)
    if isinstance(value, list):
        return [_normalise_value(item) for item in value]
    if isinstance(value, dict):
        return {
            _normalise_value(key): _normalise_value(item)
            for key, item in value.items()
        }
    return value


def _canonicalise_expression_strings(value: Any) -> Any:
    if isinstance(value, list):
        return [_canonicalise_expression_strings(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_canonicalise_expression_strings(item) for item in value)
    if isinstance(value, dict):
        return {
            key: _canonicalise_expression_strings(item)
            for key, item in value.items()
        }
    if isinstance(value, str):
        try:
            return ast.dump(ast.parse(value, mode="eval").body, include_attributes=False)
        except SyntaxError:
            return value
    return value


def _parse_structured(value: str) -> Any:
    try:
        return _normalise_value(json.loads(value))
    except json.JSONDecodeError:
        return _normalise_value(ast.literal_eval(value))


def _validate_structured(source: str, reference: str) -> ValidationResult:
    try:
        actual = _parse_structured(source)
        expected = _parse_structured(reference)
    except (SyntaxError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return ValidationResult("FAIL", 0, 1, f"Unable to parse structured answer: {exc}")
    if _canonicalise_expression_strings(actual) == _canonicalise_expression_strings(
        expected
    ):
        return ValidationResult("PASS", 1, 0)
    return ValidationResult(
        "FAIL", 0, 1, f"Expected {expected!r}, got {actual!r}"
    )


def validate_authentic_source(
    source: str,
    reference: str,
    plan: AuthenticTestPlan,
    timeout_seconds: int = 5,
) -> ValidationResult:
    """Validate one source against its right-answer oracle in a subprocess."""
    if plan.mode == "structured":
        return _validate_structured(source, reference)
    if plan.mode not in {"script", "function"}:
        raise ValueError(f"Unknown authentic test mode: {plan.mode}")

    payload = {
        "mode": plan.mode,
        "source": f"{plan.prelude}\n{source}" if plan.prelude else source,
        "reference": f"{plan.prelude}\n{reference}" if plan.prelude else reference,
        "function_name": plan.function_name,
        "cases": list(plan.cases),
    }
    with tempfile.TemporaryDirectory() as directory:
        try:
            completed = subprocess.run(
                [sys.executable, str(_RUNNER)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=directory,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                "FAIL", 0, len(plan.cases), "Execution timed out", timed_out=True
            )
        if not completed.stdout.strip():
            return ValidationResult(
                "FAIL",
                0,
                len(plan.cases),
                completed.stderr.strip() or "No validation result",
                error=completed.stderr.strip(),
            )
        try:
            return ValidationResult(**json.loads(completed.stdout))
        except (json.JSONDecodeError, TypeError) as exc:
            return ValidationResult(
                "FAIL",
                0,
                len(plan.cases),
                str(exc),
                error=completed.stderr.strip(),
            )
