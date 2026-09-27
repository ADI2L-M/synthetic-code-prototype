"""Registry for all authoritative research defect detectors."""

from __future__ import annotations

from collections.abc import Callable

from models.research import DetectionResult, TaskContext

from detectors.research.assignments import detect_augmentable_assignment
from detectors.research.collections import (
    detect_duplicate_expression,
    detect_misleading_iterator_name,
    detect_redundant_indexing,
)
from detectors.research.conditionals import (
    detect_duplicate_if,
    detect_else_if,
    detect_empty_if,
    detect_nested_if,
    detect_redundant_elif,
    detect_redundant_if_else,
    detect_redundant_not,
)
from detectors.research.formatting import detect_inappropriate_formatting
from detectors.research.iteration import detect_redundant_for, detect_while_as_for
from detectors.research.magic import detect_magic_number
from detectors.research.names import detect_built_in_name, detect_one_letter_name
from detectors.research.redundant_comparison import detect_redundant_comparison_result

ResearchDetector = Callable[[str, TaskContext | None], DetectionResult]

RESEARCH_DETECTORS: dict[str, ResearchDetector] = {
    "redundant_if_else": detect_redundant_if_else,
    "redundant_comparison": detect_redundant_comparison_result,
    "redundant_not": detect_redundant_not,
    "duplicate_if": detect_duplicate_if,
    "else_if": detect_else_if,
    "nested_if": detect_nested_if,
    "redundant_elif": detect_redundant_elif,
    "empty_if": detect_empty_if,
    "redundant_indexing": detect_redundant_indexing,
    "misleading_iterator_name": detect_misleading_iterator_name,
    "duplicate_expression": detect_duplicate_expression,
    "while_as_for": detect_while_as_for,
    "redundant_for": detect_redundant_for,
    "augmentable_assignment": detect_augmentable_assignment,
    "inappropriate_formatting": detect_inappropriate_formatting,
    "magic_number": detect_magic_number,
    "one_letter_name": detect_one_letter_name,
    "built_in_name": detect_built_in_name,
}


def detect_research_defects(
    source: str,
    defect_ids: list[str] | None = None,
    context: TaskContext | None = None,
) -> dict[str, DetectionResult]:
    """Run selected authoritative detectors while preserving raw results."""
    selected = defect_ids or list(RESEARCH_DETECTORS)
    unknown = set(selected).difference(RESEARCH_DETECTORS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"No research detector registered for: {names}")
    return {
        defect_id: RESEARCH_DETECTORS[defect_id](source, context)
        for defect_id in selected
    }
