from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCase:
    args: list[Any]
    expected: Any = None
    raises: str | None = None


@dataclass(frozen=True)
class ProgrammingTask:
    id: str
    name: str
    description: str
    function_name: str
    contexts: list[str]
    functional_requirements: list[str]
    test_cases: list[TestCase]


@dataclass(frozen=True)
class DefectDefinition:
    id: str
    display_name: str
    classification: str
    detector: str
    description: str


@dataclass
class ValidationResult:
    status: str
    tests_passed: int
    tests_failed: int
    failure_message: str = ""
    timed_out: bool = False
    error: str = ""


@dataclass
class SubmissionResult:
    submission_id: int
    source_code: str
    validation: ValidationResult
    defects: dict[str, bool] = field(default_factory=dict)


@dataclass
class IterationResult:
    iteration: int
    specification: str
    submissions: list[SubmissionResult]
    observed_profile: dict[str, float]
    comparison: list[dict[str, Any]]
