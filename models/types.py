from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCase:
    args: list[Any]
    expected: Any = None
    raises: str | None = None
    expected_type: str | None = None


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
    applicable_contexts: tuple[str, ...] = ()


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
    assigned_defects: tuple[str, ...] = ()
    prompt: str = ""
    generation_seed: int | None = None
    generation_attempts: int = 1
    category_requirements_met: bool = False
    missing_defect_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProfileComparison:
    defect: str
    target: float
    observed: float
    difference: float
    status: str
    action: str
    observed_count: int = 0
    observed_denominator: int = 0
    target_standard_error: float = 0.0
    observed_interval_low: float = 0.0
    observed_interval_high: float = 0.0
    allowed_difference: float = 0.0


@dataclass
class IterationResult:
    iteration: int
    task_id: str
    task_name: str
    target_profile: dict[str, float]
    tolerance: float
    constraints: dict[str, str]
    specification: str
    submissions: list[SubmissionResult]
    observed_profile: dict[str, float]
    comparison: list[ProfileComparison]
    assignment_seed: int | None = None
    expected_assignment_counts: dict[str, float] = field(default_factory=dict)
    planned_assignment_counts: dict[str, int] = field(default_factory=dict)
    model: str | None = None
    context_length: int | None = None
    target_standard_errors: dict[str, float] = field(default_factory=dict)
    condition: str = "task_aware_non_adaptive"

    @property
    def accepted(self) -> bool:
        return all(item.status == "Within tolerance" for item in self.comparison)
