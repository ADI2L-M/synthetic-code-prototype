import ast
from collections.abc import Callable, Iterable

from detectors.research.registry import RESEARCH_DETECTORS
from models.research import (
    DetectionResult,
    Eligibility,
    ResearchAnalysisRecord,
)
from services.authentic.ingestion import AuthenticSubmission
from services.research.eligibility import eligibility_for


TASK_FAMILIES = {
    "T1": "conditional_logic",
    "T2": "list_processing",
    "T3": "numeric_iteration",
}

ResearchDetector = Callable[[str], DetectionResult]


def _parse_error(source_code: str) -> str | None:
    try:
        ast.parse(source_code)
    except (SyntaxError, UnicodeError, ValueError) as error:
        return str(error)
    return None


def analyze_submission(
    submission: AuthenticSubmission,
    detectors: dict[str, ResearchDetector] | None = None,
    functional_correct: bool | None = None,
    constraint_compliant: bool | None = None,
) -> ResearchAnalysisRecord:
    detectors = detectors or RESEARCH_DETECTORS
    parse_error = _parse_error(submission.source_code)
    parse_success = parse_error is None
    task_family = TASK_FAMILIES.get(submission.task_id)
    if task_family is None:
        raise ValueError(f"Unknown research task: {submission.task_id}")

    defects: dict[str, DetectionResult] = {}
    eligibility: dict[str, Eligibility] = {}
    for defect, detector in detectors.items():
        eligibility[defect] = eligibility_for(submission.task_id, defect)
        if parse_success:
            defects[defect] = detector(submission.source_code)
        else:
            defects[defect] = DetectionResult(
                defect=defect,
                notes="Raw detection skipped because parsing failed.",
            )

    exclusion_reason = None
    if not parse_success:
        exclusion_reason = "parse_error"
    elif functional_correct is False:
        exclusion_reason = "functional_incorrect"
    elif constraint_compliant is False:
        exclusion_reason = "constraint_violation"

    return ResearchAnalysisRecord(
        submission_id=submission.submission_id,
        lab=submission.lab,
        question=submission.question,
        task_id=submission.task_id,
        task_family=task_family,
        source_code=submission.source_code,
        parse_success=parse_success,
        parse_error=parse_error,
        functional_correct=functional_correct,
        constraint_compliant=constraint_compliant,
        defects=defects,
        eligibility=eligibility,
        exclusion_reason=exclusion_reason,
    )


def analyze_submissions(
    submissions: Iterable[AuthenticSubmission],
    detectors: dict[str, ResearchDetector] | None = None,
) -> list[ResearchAnalysisRecord]:
    return [analyze_submission(submission, detectors) for submission in submissions]
