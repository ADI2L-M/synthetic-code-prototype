import json
import subprocess
import sys
import tempfile
from pathlib import Path

from models.types import ProgrammingTask, ValidationResult


def validate_source(source: str, task: ProgrammingTask, timeout_seconds: int = 3) -> ValidationResult:
    payload = {"source": source, "function_name": task.function_name, "test_cases": [case.__dict__ for case in task.test_cases]}
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / "runner.py"
        script.write_text("""import json, sys\np=json.loads(sys.stdin.read())\nns={}\ntry:\n    exec(compile(p['source'], '<submission>', 'exec'), ns)\n    fn=ns[p['function_name']]\n    passed=failed=0\n    messages=[]\n    for case in p['test_cases']:\n        try:\n            result=fn(*case['args'])\n            ok=result == case.get('expected') and not case.get('raises')\n        except Exception as exc:\n            ok=bool(case.get('raises') and type(exc).__name__ == case['raises'])\n            if not ok: messages.append(str(exc))\n        if ok: passed += 1\n        else: failed += 1\n    print(json.dumps({'status': 'PASS' if failed == 0 else 'FAIL', 'tests_passed': passed, 'tests_failed': failed, 'failure_message': '; '.join(messages)}))\nexcept Exception as exc:\n    print(json.dumps({'status': 'FAIL', 'tests_passed': 0, 'tests_failed': len(p['test_cases']), 'failure_message': str(exc)}))\n""", encoding="utf-8")
        try:
            completed = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), capture_output=True, text=True, timeout=timeout_seconds, cwd=directory, check=False)
        except subprocess.TimeoutExpired:
            return ValidationResult("FAIL", 0, len(task.test_cases), "Execution timed out", timed_out=True)
        if not completed.stdout.strip():
            return ValidationResult("FAIL", 0, len(task.test_cases), completed.stderr.strip() or "No validation result", error=completed.stderr.strip())
        try:
            return ValidationResult(**json.loads(completed.stdout))
        except (json.JSONDecodeError, TypeError) as exc:
            return ValidationResult("FAIL", 0, len(task.test_cases), str(exc), error=completed.stderr.strip())
