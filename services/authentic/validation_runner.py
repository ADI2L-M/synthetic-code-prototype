"""Isolated runner for reference-derived authentic functional validation."""

# This subprocess executes untrusted student code with a parent timeout.
# ruff: noqa: BLE001, S102

from __future__ import annotations

import builtins
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any


def _equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, (tuple, list)) and isinstance(expected, (tuple, list)):
        return len(actual) == len(expected) and all(
            _equal(left, right) for left, right in zip(actual, expected)
        )
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _equal(actual[key], expected[key]) for key in actual
        )
    return actual == expected


def _normalise_output(value: str) -> str:
    lines = [line.rstrip() for line in value.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip()


def _files(case: dict[str, Any]) -> None:
    for filename, contents in case.get("files", {}).items():
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")


def _run_function(source: str, function_name: str, args: list[Any]) -> tuple[Any, str]:
    namespace: dict[str, Any] = {}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(source, "<submission>", "exec"), namespace)
        result = namespace[function_name](*args)
    return result, _normalise_output(output.getvalue())


def _run_script(source: str, inputs: list[str]) -> str:
    namespace: dict[str, Any] = {}
    values = iter(inputs)

    def fake_input(_prompt: str = "") -> str:
        return next(values)

    output = io.StringIO()
    original_input = builtins.input
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(output):
            exec(compile(source, "<submission>", "exec"), namespace)
    finally:
        builtins.input = original_input
    return _normalise_output(output.getvalue())


def execute(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload["mode"]
    source = payload["source"]
    reference = payload["reference"]
    function_name = payload.get("function_name")
    cases = payload["cases"]
    passed = 0
    messages: list[str] = []

    try:
        for index, case in enumerate(cases, start=1):
            _files(case)
            if mode == "function":
                expected, expected_output = _run_function(
                    reference, function_name, case["args"]
                )
                actual, actual_output = _run_function(
                    source, function_name, case["args"]
                )
                correct = _equal(actual, expected) and actual_output == expected_output
                if not correct:
                    messages.append(
                        f"Test {index}: expected result/output {expected!r}/{expected_output!r}, "
                        f"got {actual!r}/{actual_output!r}"
                    )
            else:
                expected_output = _run_script(reference, case["inputs"])
                actual_output = _run_script(source, case["inputs"])
                correct = actual_output == expected_output
                if not correct:
                    messages.append(
                        f"Test {index}: expected output {expected_output!r}, "
                        f"got {actual_output!r}"
                    )
            if correct:
                passed += 1
    except Exception as exc:
        return {
            "status": "FAIL",
            "tests_passed": passed,
            "tests_failed": len(cases) - passed,
            "failure_message": str(exc),
        }

    failed = len(cases) - passed
    return {
        "status": "PASS" if failed == 0 else "FAIL",
        "tests_passed": passed,
        "tests_failed": failed,
        "failure_message": "; ".join(messages),
    }


def main() -> None:
    print(json.dumps(execute(json.loads(sys.stdin.read()))))


if __name__ == "__main__":
    main()
