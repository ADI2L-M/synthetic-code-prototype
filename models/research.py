from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DetectionLocation:
    line: int
    column: int


@dataclass
class DetectionResult:
    defect: str
    present: bool = False
    count: int = 0
    locations: list[DetectionLocation] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    notes: str | None = None


@dataclass(frozen=True)
class TaskContext:
    task_id: str
    task_family: str
    required_constructs: tuple[str, ...] = ()
    restricted_constructs: tuple[str, ...] = ()
    required_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class Eligibility:
    status: str
    opportunity_level: str = "normal"
    reason: str | None = None


@dataclass
class ResearchAnalysisRecord:
    submission_id: str
    lab: int
    question: int
    task_id: str
    task_family: str
    source_code: str
    parse_success: bool
    parse_error: str | None = None
    functional_correct: bool | None = None
    constraint_compliant: bool | None = None
    defects: dict[str, DetectionResult] = field(default_factory=dict)
    eligibility: dict[str, Eligibility] = field(default_factory=dict)
    exclusion_reason: str | None = None

    @property
    def valid_for_prevalence(self) -> bool:
        return (
            self.parse_success
            and self.functional_correct is True
            and self.constraint_compliant is True
        )
