"""Subprocess entry point for isolated functional validation."""

# The runner intentionally executes untrusted demonstration code and captures
# arbitrary submission exceptions. It is launched only in a timed subprocess.
# ruff: noqa: BLE001, S102

import json
import sys
from typing import Any


def execute(payload: dict[str, Any]) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    test_cases = payload["test_cases"]
    try:
        exec(compile(payload["source"], "<submission>", "exec"), namespace)
        function = namespace[payload["function_name"]]
    except Exception as exc:  # The submission may fail in arbitrary ways.
        return {
            "status": "FAIL",
            "tests_passed": 0,
            "tests_failed": len(test_cases),
            "failure_message": str(exc),
        }

    passed = 0
    failed = 0
    messages: list[str] = []
    for index, case in enumerate(test_cases, start=1):
        try:
            result = function(*case["args"])
            expected_exception = case.get("raises")
            correct = not expected_exception and result == case.get("expected")
            if not correct:
                messages.append(
                    f"Test {index}: expected {case.get('expected')!r}, got {result!r}"
                )
        except Exception as exc:  # The expected result can itself be an exception.
            correct = bool(case.get("raises") and type(exc).__name__ == case["raises"])
            if not correct:
                messages.append(f"Test {index}: {type(exc).__name__}: {exc}")

        if correct:
            passed += 1
        else:
            failed += 1

    return {
        "status": "PASS" if failed == 0 else "FAIL",
        "tests_passed": passed,
        "tests_failed": failed,
        "failure_message": "; ".join(messages),
    }


def main() -> None:
    payload = json.loads(sys.stdin.read())
    print(json.dumps(execute(payload)))


if __name__ == "__main__":
    main()
