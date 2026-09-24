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
