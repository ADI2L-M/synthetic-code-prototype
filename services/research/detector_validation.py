"""Controlled-fixture and manual-label support for detector validation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

from detectors.research.registry import RESEARCH_DETECTORS
from services.research.validation_metrics import ValidationLabel


def _review_required_defects() -> set[str]:
    specification_path = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "defect_specifications.json"
    )
    specification = json.loads(specification_path.read_text(encoding="utf-8"))
    return {
        str(defect["name"])
        for defect in specification.get("defects", [])
        if defect.get("requires_review")
    }


ASSISTED_REVIEW_REASONS = {
    "duplicate_if": (
        "The branch bodies may be identical, but human review is needed to "
        "confirm that merging the conditions preserves evaluation order and "
        "does not change side effects."
    ),
    "nested_if": (
        "Human review is needed to confirm that flattening the nested condition "
        "does not change short-circuit behavior, scope, or else association."
    ),
    "redundant_elif": (
        "Human review is needed to confirm that preceding conditions prove the "
        "elif condition is guaranteed whenever control reaches it."
    ),
    "augmentable_assignment": (
        "Human review is needed to confirm that replacing the assignment with "
        "an augmented assignment preserves evaluation and aliasing behavior."
    ),
    "magic_number": (
        "Human review is needed to distinguish an unexplained domain literal "
        "from a task-required threshold, sentinel, index, or configuration value."
    ),
}


@dataclass(frozen=True)
class ControlledCase:
    case_id: str
    defect: str
    task_family: str
    expected_present: bool
    source_code: str
    description: str


def _case(
    case_id: str,
    defect: str,
    task_family: str,
    expected_present: bool,
    source_code: str,
    description: str,
) -> ControlledCase:
    return ControlledCase(
        case_id=case_id,
        defect=defect,
        task_family=task_family,
        expected_present=expected_present,
        source_code=dedent(source_code).lstrip(),
        description=description,
    )


CONTROLLED_CASES: tuple[ControlledCase, ...] = (
    _case(
        "redundant_if_else_positive",
        "redundant_if_else",
        "conditional_logic",
        True,
        """
        if condition:
            return True
        else:
            return False
        """,
        "Boolean if/else branches return the condition and its inverse.",
    ),
    _case(
        "redundant_if_else_negative",
        "redundant_if_else",
        "conditional_logic",
        False,
        "return condition\n",
        "No conditional branch is present.",
    ),
    _case(
        "redundant_comparison_positive",
        "redundant_comparison",
        "conditional_logic",
        True,
        """
        if (temp < 10) == True:
            return 'cold'
        """,
        "A comparison result is compared with True.",
    ),
    _case(
        "redundant_comparison_negative",
        "redundant_comparison",
        "conditional_logic",
        False,
        """
        if temp < 10:
            return 'cold'
        """,
        "The comparison result is used directly.",
    ),
    _case(
        "redundant_not_positive",
        "redundant_not",
        "conditional_logic",
        True,
        """
        if not temp >= 10:
            return 'cold'
        """,
        "Negation is applied to an inequality that can be rewritten directly.",
    ),
    _case(
        "redundant_not_negative",
        "redundant_not",
        "conditional_logic",
        False,
        """
        if temp in values:
            return True
        """,
        "No redundant negated comparison is present.",
    ),
    _case(
        "duplicate_if_positive",
        "duplicate_if",
        "conditional_logic",
        True,
        """
        if temp < 0:
            return 'cold'
        elif temp < 10:
            return 'cold'
        """,
        "Two branches return the same result for overlapping conditions.",
    ),
    _case(
        "duplicate_if_negative",
        "duplicate_if",
        "conditional_logic",
        False,
        """
        if temp < 0:
            return 'cold'
        elif temp < 10:
            return 'mild'
        """,
        "Adjacent branches return different results.",
    ),
    _case(
        "else_if_positive",
        "else_if",
        "conditional_logic",
        True,
        """
        if temp < 10:
            return 'cold'
        else:
            if temp < 25:
                return 'mild'
        """,
        "An else branch contains a nested if that can be expressed as elif.",
    ),
    _case(
        "else_if_negative",
        "else_if",
        "conditional_logic",
        False,
        """
        if temp < 10:
            return 'cold'
        elif temp < 25:
            return 'mild'
        """,
        "The conditional already uses elif.",
    ),
    _case(
        "nested_if_positive",
        "nested_if",
        "conditional_logic",
        True,
        """
        if temp >= 10:
            if temp < 25:
                return 'mild'
        """,
        "A conditional is nested inside another conditional.",
    ),
    _case(
        "nested_if_negative",
        "nested_if",
        "conditional_logic",
        False,
        """
        if temp >= 10:
            log('entered')
            if temp < 25:
                return 'mild'
        """,
        "The nested branch has an intervening statement and is not the supported case.",
    ),
    _case(
        "redundant_elif_positive",
        "redundant_elif",
        "conditional_logic",
        True,
        """
        if temp < 10:
            return 'cold'
        elif temp >= 10:
            return 'mild'
        """,
        "The elif condition is the direct inverse of the preceding condition.",
    ),
    _case(
        "redundant_elif_negative",
        "redundant_elif",
        "conditional_logic",
        False,
        """
        if temp < 10:
            return 'cold'
        elif temp < 25:
            return 'mild'
        """,
        "The elif condition is not a direct inverse.",
    ),
    _case(
        "empty_if_positive",
        "empty_if",
        "conditional_logic",
        True,
        """
        if temp >= 10:
            pass
        else:
            return 'cold'
        """,
        "The if branch contains only pass.",
    ),
    _case(
        "empty_if_negative",
        "empty_if",
        "conditional_logic",
        False,
        """
        if temp >= 10:
            return 'mild'
        """,
        "The if branch contains executable logic.",
    ),
    _case(
        "redundant_indexing_positive",
        "redundant_indexing",
        "list_processing",
        True,
        """
        total = 0
        for i in range(len(scores)):
            total += scores[i]
        """,
        "An index is used only to read the current collection element.",
    ),
    _case(
        "redundant_indexing_negative",
        "redundant_indexing",
        "list_processing",
        False,
        """
        total = 0
        for i in range(len(scores)):
            total += scores[i]
            print(i)
        """,
        "The index has another observable use.",
    ),
    _case(
        "misleading_iterator_name_positive",
        "misleading_iterator_name",
        "list_processing",
        True,
        """
        for i in scores:
            total += i
        """,
        "A generic index-style name is used as a collection element.",
    ),
    _case(
        "misleading_iterator_name_negative",
        "misleading_iterator_name",
        "list_processing",
        False,
        """
        for score in scores:
            total += score
        """,
        "The iterator name describes the collection element.",
    ),
    _case(
        "duplicate_expression_positive",
        "duplicate_expression",
        "list_processing",
        True,
        """
        for i in range(len(scores)):
            if scores[i] > 0:
                total += scores[i]
        """,
        "A pure collection expression is repeated in the local region.",
    ),
    _case(
        "duplicate_expression_negative",
        "duplicate_expression",
        "list_processing",
        False,
        """
        if scores[i] > 0:
            total += scores[j]
        """,
        "The expressions are not duplicated.",
    ),
    _case(
        "while_as_for_positive",
        "while_as_for",
        "numeric_iteration",
        True,
        """
        i = 1
        total = 0
        while i <= n:
            total += i
            i += 1
        """,
        "A while loop has a constant monotonic counter update and bound.",
    ),
    _case(
        "while_as_for_negative",
        "while_as_for",
        "numeric_iteration",
        False,
        """
        while input('continue?'):
            pass
        """,
        "The loop is input-controlled rather than a counted iteration.",
    ),
    _case(
        "redundant_for_positive",
        "redundant_for",
        "numeric_iteration",
        True,
        """
        for i in range(1):
            return n
        """,
        "A one-iteration loop can be replaced by its body.",
    ),
    _case(
        "redundant_for_negative",
        "redundant_for",
        "numeric_iteration",
        False,
        """
        for item in items:
            use(item)
        """,
        "The loop may execute an arbitrary number of times.",
    ),
    _case(
        "augmentable_assignment_positive",
        "augmentable_assignment",
        "numeric_iteration",
        True,
        "total = total + score\n",
        "A simple addition assignment can use +=.",
    ),
    _case(
        "augmentable_assignment_negative",
        "augmentable_assignment",
        "numeric_iteration",
        False,
        "total = score + total\n",
        "The target is not the left operand of the addition.",
    ),
    _case(
        "inappropriate_formatting_positive",
        "inappropriate_formatting",
        "shared",
        True,
        "total=0\n",
        "Operator spacing violates the configured formatting rule.",
    ),
    _case(
        "inappropriate_formatting_negative",
        "inappropriate_formatting",
        "shared",
        False,
        "total = 0\n",
        "Operator spacing follows the configured formatting rule.",
    ),
    _case(
        "magic_number_positive",
        "magic_number",
        "shared",
        True,
        """
        if temp < 10:
            return 'cold'
        """,
        "A non-exempt numeric literal appears in domain logic.",
    ),
    _case(
        "magic_number_negative",
        "magic_number",
        "shared",
        False,
        """
        total = 0
        for i in range(1):
            total += i
        """,
        "Only exempt literals are used.",
    ),
    _case(
        "one_letter_name_positive",
        "one_letter_name",
        "shared",
        True,
        """
        x = 0
        return_value = x
        """,
        "A non-exempt one-letter variable name is used.",
    ),
    _case(
        "one_letter_name_negative",
        "one_letter_name",
        "shared",
        False,
        """
        for i in range(n):
            total += i
        """,
        "The conventional loop index is exempt.",
    ),
    _case(
        "built_in_name_positive",
        "built_in_name",
        "shared",
        True,
        "sum = 0\n",
        "A built-in name is shadowed by a local binding.",
    ),
    _case(
        "built_in_name_negative",
        "built_in_name",
        "shared",
        False,
        "total = 0\n",
        "No built-in name is shadowed.",
    ),
)


def run_controlled_fixtures(
    cases: Iterable[ControlledCase] = CONTROLLED_CASES,
) -> dict[str, Any]:
    """Run every controlled positive/negative detector case."""
    results: list[dict[str, Any]] = []
    for case in cases:
        detector = RESEARCH_DETECTORS[case.defect]
        detection = detector(case.source_code)
        passed = detection.present is case.expected_present
        results.append(
            {
                **asdict(case),
                "source_code": None,
                "detected_present": detection.present,
                "detected_count": detection.count,
                "passed": passed,
                "evidence_available": bool(detection.evidence),
            }
        )
    return {
        "report_type": "controlled_detector_validation",
        "case_count": len(results),
        "passed_count": sum(item["passed"] for item in results),
        "failed_count": sum(not item["passed"] for item in results),
        "all_passed": all(item["passed"] for item in results),
        "detector_count": len({item["defect"] for item in results}),
        "cases": results,
    }


def load_validation_labels(path: Path) -> list[ValidationLabel]:
    """Load completed binary manual labels from a JSONL file."""
    labels: list[ValidationLabel] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = json.loads(line)
        if item.get("manual_label") in (None, "", "uncertain"):
            continue
        try:
            labels.append(
                ValidationLabel(
                    submission_id=str(item["submission_id"]),
                    task_id=str(item["task_id"]),
                    defect=str(item["defect"]),
                    manual_label=int(item["manual_label"]),
                    detector_label=int(item["detector_label"]),
                    task_family=str(item.get("task_family", "")),
                    eligibility=str(item.get("eligibility", "eligible")),
                    reviewer=str(item.get("reviewer", "")),
                    notes=str(item.get("notes", "")),
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid validation label at {path}:{line_number}: {error}"
            ) from error
    return labels


def create_assisted_validation(
    input_path: Path,
    output_path: Path,
    uncertain_output_path: Path,
) -> dict[str, int]:
    """Create a provisional first-pass label file and uncertainty queue.

    This is intentionally separate from official manual validation. Cases whose
    specification requires contextual review are left as ``uncertain``. Other
    cases receive the detector result as a provisional label because their
    operational definition states that AST evidence is sufficient. A human
    reviewer must audit the resulting file before it is used as gold data.
    """
    review_required = _review_required_defects()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    uncertain_output_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {"total": 0, "provisional": 0, "uncertain": 0}

    with (
        input_path.open(encoding="utf-8") as input_file,
        output_path.open("w", encoding="utf-8") as output_file,
        uncertain_output_path.open("w", encoding="utf-8") as uncertain_file,
    ):
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            item = json.loads(line)
            defect = str(item["defect"])
            detector_label = int(item["detector_label"])
            counts["total"] += 1
            if defect in review_required:
                item["manual_label"] = "uncertain"
                item["reviewer"] = "Codex AI first pass"
                item["ai_first_pass_reason"] = ASSISTED_REVIEW_REASONS[defect]
                uncertain_file.write(
                    json.dumps(item, ensure_ascii=False) + "\n"
                )
                counts["uncertain"] += 1
            else:
                item["manual_label"] = detector_label
                item["reviewer"] = "Codex AI first pass"
                item["ai_first_pass_reason"] = (
                    "Provisional label follows the detector result because the "
                    "operational specification states that AST evidence is "
                    "sufficient; human audit remains required."
                )
                counts["provisional"] += 1
            output_file.write(json.dumps(item, ensure_ascii=False) + "\n")

    counts["input_line_count"] = line_number if "line_number" in locals() else 0
    return counts


def merge_assisted_labels(
    assisted_path: Path,
    reviewed_uncertain_path: Path,
    output_path: Path,
) -> dict[str, int]:
    """Merge reviewed uncertainty decisions into the complete label file."""
    base_rows = [
        json.loads(line)
        for line in assisted_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    reviewed_rows = [
        json.loads(line)
        for line in reviewed_uncertain_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    by_key = {
        (str(row["submission_id"]), str(row["task_id"]), str(row["defect"])): row
        for row in base_rows
    }
    merged = 0
    for reviewed in reviewed_rows:
        key = (
            str(reviewed["submission_id"]),
            str(reviewed["task_id"]),
            str(reviewed["defect"]),
        )
        if key not in by_key:
            raise ValueError(
                "Reviewed uncertainty case is not present in the assisted file: "
                f"{key}"
            )
        if reviewed.get("manual_label") in (None, "", "uncertain"):
            continue
        target = by_key[key]
        for field in ("manual_label", "reviewer", "notes", "evidence_reference"):
            if field in reviewed:
                target[field] = reviewed[field]
        target["ai_review_status"] = "human-reviewed"
        merged += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for row in base_rows:
            output_file.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"total": len(base_rows), "merged": merged}
