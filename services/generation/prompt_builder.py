import json
from functools import lru_cache
from pathlib import Path

from models.types import ProgrammingTask

TASK_INDEPENDENT_DEFECTS = {
    "non_descriptive_naming",
    "unused_variable",
    "inappropriate_formatting",
    "magic_number",
    "one_letter_name",
    "built_in_name",
}

ROOT = Path(__file__).resolve().parents[2]
DEFECT_SPECIFICATION_PATH = ROOT / "config" / "defect_specifications.json"

GENERATION_HINTS = {
    "redundant_if_else": (
        "When the task permits Boolean results, use an if/else whose branches "
        "directly return opposite Boolean constants. Do not change a required "
        "category-string or numeric return contract."
    ),
    "redundant_comparison": (
        "Make a proven Boolean expression explicitly compare with True or False "
        "using == or !=, while keeping the operand genuinely Boolean-valued."
    ),
    "redundant_not": (
        "Apply not directly to one ordinary comparison, such as not (value < "
        "bound), where an inverse comparison would preserve the same behaviour."
    ),
    "duplicate_if": (
        "Use adjacent if/elif branches with structurally identical, "
        "side-effect-free bodies so their conditions could be combined."
    ),
    "else_if": (
        "Write an else branch containing exactly one nested if instead of using "
        "elif, without adding wrapper statements or changing branch order."
    ),
    "nested_if": (
        "Place one side-effect-free if directly inside another if, with no else "
        "branches, so the conditions could safely be joined with and."
    ),
    "redundant_elif": (
        "Use an elif whose condition is already guaranteed by the preceding "
        "condition, while preserving the task's complete branch coverage."
    ),
    "empty_if": (
        "Make one if or else branch contain only pass and put the meaningful "
        "task behaviour in the alternative branch."
    ),
    "redundant_indexing": (
        "Iterate through range(len(collection)) and use the index only to read "
        "the matching current element; do not mutate or otherwise expose it."
    ),
    "misleading_iterator_name": (
        "Use an index-style name such as i or j as the direct iterator over "
        "collection elements, not as a numeric range index."
    ),
    "duplicate_expression": (
        "Repeat the same pure, non-trivial expression in a small region at least "
        "twice, avoiding calls or expressions with possible side effects."
    ),
    "while_as_for": (
        "Use a counter-controlled while loop with a constant update on every "
        "executable path and no break, return, or bypassing continue."
    ),
    "redundant_for": (
        "Use a for loop over a statically zero- or one-element iterable where the "
        "body does not depend on repetition."
    ),
    "augmentable_assignment": (
        "Write a matching update as ordinary assignment, such as total = total "
        "+ value, instead of using the equivalent augmented assignment."
    ),
    "inappropriate_formatting": (
        "Include one documented whitespace violation while keeping the source "
        "valid Python, such as missing operator or comma spacing."
    ),
    "magic_number": (
        "Use an unnamed, meaningful numeric literal directly in decision or "
        "domain-computation logic rather than naming that value."
    ),
    "one_letter_name": (
        "Use a one-letter local or binding whose role is not an allowed index, "
        "bound, mathematical variable, ignored value, or required task name."
    ),
    "built_in_name": (
        "Bind a user-defined variable or function to a Python built-in name, "
        "such as list or sum, without changing the required public function."
    ),
}

# Short contrastive examples make the structural intent concrete without
# putting a complete task solution in the model's context.  These examples
# are deliberately task-independent; the construction hint and task contract
# determine whether the pattern is suitable for the current submission.
GENERATION_EXAMPLES = {
    "redundant_if_else": {
        "defective": "if value > 0:\n    return True\nelse:\n    return False",
        "corrected": "return value > 0",
    },
    "redundant_comparison": {
        "defective": "if (value > 0) == True:\n    return 'positive'",
        "corrected": "if value > 0:\n    return 'positive'",
    },
    "redundant_not": {
        "defective": "if not (value < limit):\n    return 'outside'",
        "corrected": "if value >= limit:\n    return 'outside'",
    },
    "duplicate_if": {
        "defective": "if value < 0:\n    return 'invalid'\nelif value == 0:\n    return 'invalid'",
        "corrected": "if value <= 0:\n    return 'invalid'",
    },
    "else_if": {
        "defective": "if value < 0:\n    return 'negative'\nelse:\n    if value == 0:\n        return 'zero'",
        "corrected": "if value < 0:\n    return 'negative'\nelif value == 0:\n    return 'zero'",
    },
    "nested_if": {
        "defective": "if value >= 0:\n    if value <= 10:\n        return 'small'",
        "corrected": "if value >= 0 and value <= 10:\n    return 'small'",
    },
    "redundant_elif": {
        "defective": "if value < 10:\n    return 'low'\nelif value >= 10:\n    return 'high'",
        "corrected": "if value < 10:\n    return 'low'\nelse:\n    return 'high'",
    },
    "empty_if": {
        "defective": "if valid:\n    pass\nelse:\n    return value",
        "corrected": "if not valid:\n    return value",
    },
    "redundant_indexing": {
        "defective": "for i in range(len(items)):\n    total += items[i]",
        "corrected": "for item in items:\n    total += item",
    },
    "misleading_iterator_name": {
        "defective": "for i in items:\n    total += i",
        "corrected": "for item in items:\n    total += item",
    },
    "duplicate_expression": {
        "defective": "if value * scale + offset > 0:\n    result = value * scale + offset",
        "corrected": "computed = value * scale + offset\nif computed > 0:\n    result = computed",
    },
    "while_as_for": {
        "defective": "i = 0\nwhile i < limit:\n    process(i)\n    i += 1",
        "corrected": "for i in range(limit):\n    process(i)",
    },
    "redundant_for": {
        "defective": "for _ in range(1):\n    result = compute(value)",
        "corrected": "result = compute(value)",
    },
    "augmentable_assignment": {
        "defective": "total = total + value",
        "corrected": "total += value",
    },
    "inappropriate_formatting": {
        "defective": "if value==limit:\n    result = first,second",
        "corrected": "if value == limit:\n    result = first, second",
    },
    "magic_number": {
        "defective": "if score >= 50:\n    return 'pass'",
        "corrected": "PASS_SCORE = 50\nif score >= PASS_SCORE:\n    return 'pass'",
    },
    "one_letter_name": {
        "defective": "x = temperature * scale",
        "corrected": "scaled_temperature = temperature * scale",
    },
    "built_in_name": {
        "defective": "list = []\nlist.append(value)",
        "corrected": "values = []\nvalues.append(value)",
    },
}


@lru_cache(maxsize=1)
def _defect_catalog() -> dict[str, dict[str, object]]:
    specification = json.loads(
        DEFECT_SPECIFICATION_PATH.read_text(encoding="utf-8")
    )
    return {
        item["name"]: item
        for item in specification.get("defects", [])
        if "name" in item
    }


def build_generation_specification(
    task: ProgrammingTask,
    target: dict[str, float],
    constraints: dict[str, str] | None = None,
) -> str:
    constraints = constraints or {}
    catalog = _defect_catalog()
    potential_task_dependent = [
        key for key in target if key not in TASK_INDEPENDENT_DEFECTS
    ]
    potential_defects = [
        f"- {key.replace('_', ' ')}: "
        f"{catalog.get(key, {}).get('authoritative_definition', 'Use the documented structural condition.')}."
        + (f" Guidance: {constraints[key]}." if constraints.get(key) else "")
        for key in potential_task_dependent
    ]
    return (
        f"PROGRAMMING TASK\n\n{task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\nPOTENTIAL TASK-DEPENDENT DEFECTS\n\n"
        + (
            "\n".join(potential_defects)
            or "- No additional task-dependent characteristics selected."
        )
        + "\n\nGENERATION FOCUS\n\n"
        "Task-dependent structural defects are the primary research focus. "
        "When a task-dependent defect is assigned in the submission brief, "
        "implement that exact structure while preserving functional correctness. "
        "Do not substitute a task-independent style."
        + "\n\nIMPORTANT\n\nThe program must remain functionally correct."
    )


def build_submission_specification(
    task: ProgrammingTask,
    assigned_defects: tuple[str, ...],
    constraints: dict[str, str] | None = None,
) -> str:
    """Build a detailed, per-submission defect-guidance brief."""
    constraints = constraints or {}
    catalog = _defect_catalog()
    assigned_task_dependent = tuple(
        defect for defect in assigned_defects if defect not in TASK_INDEPENDENT_DEFECTS
    )
    guidance: list[str] = []
    for defect in assigned_defects:
        definition = catalog.get(defect, {})
        authoritative_definition = definition.get("authoritative_definition", "")
        positive_condition = definition.get("positive_condition", "")
        exclusions = definition.get("exclusions", [])
        expected_evidence = definition.get("expected_evidence", [])
        example = GENERATION_EXAMPLES.get(defect)
        exclusion_text = "; ".join(str(item) for item in exclusions)
        evidence_text = "; ".join(str(item) for item in expected_evidence)
        extra_constraint = constraints.get(defect)
        guidance.append(
            f"DEFECT: {defect.replace('_', ' ')}\n"
            f"  Definition: {authoritative_definition}\n"
            f"  Required structural condition: {positive_condition}\n"
            f"  Construction hint: {GENERATION_HINTS.get(defect, 'Follow the required structural condition exactly.')}\n"
            + (
                "  Defective pattern example:\n"
                f"    {example['defective'].replace(chr(10), chr(10) + '    ')}\n"
                "  Corrected contrast:\n"
                f"    {example['corrected'].replace(chr(10), chr(10) + '    ')}\n"
                if example
                else ""
            )
            + (f"  Avoid: {exclusion_text}.\n" if exclusion_text else "")
            + (f"  Evidence the evaluator will look for: {evidence_text}.\n" if evidence_text else "")
            + (
                f"  Additional guidance: {extra_constraint}.\n"
                if extra_constraint
                else ""
            )
        )

    if guidance:
        assigned_section = "\n".join(guidance)
        instruction = "Attempt to include every assigned style while preserving the functional contract."
    else:
        assigned_section = "- No intentional defect style assigned."
        instruction = (
            "Generate a conventional implementation and avoid intentionally introducing documented defect styles."
        )

    task_dependent_focus = ""
    if assigned_task_dependent:
        task_dependent_focus = (
            "TASK-DEPENDENT DEFECT FOCUS\n\n"
            "This submission has an assigned task-dependent structural defect. "
            "That structure is mandatory: realise it in the task's control flow "
            "or computation and do not replace it with a task-independent defect "
            "such as formatting, naming, or a magic number.\n\n"
        )

    return (
        "SUBMISSION GENERATION BRIEF\n\n"
        "ROLE\n\n"
        "You are generating one authentic-looking Python student submission. "
        "The source will be executed and structurally evaluated after generation.\n\n"
        "PROGRAMMING TASK\n\n"
        f"Task ID: {task.id}\n"
        f"Function to implement: {task.function_name}\n"
        f"Task contexts: {', '.join(task.contexts)}\n"
        f"Description: {task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\n"
        + task_dependent_focus
        + "\n\nASSIGNED DEFECT STYLE BRIEFS\n\n"
        + assigned_section
        + "\n\nGENERATION OBJECTIVE\n\n"
        + instruction
        + " The defect guidance is intentional, but functional correctness takes priority if a conflict is discovered.\n\n"
        "PRIVATE PRE-RETURN CHECK\n\n"
        "Before returning the source, silently check that the required function "
        "exists, every functional requirement is satisfied, each assigned style "
        "is represented as described, excluded forms are avoided, and the result "
        "contains only executable Python code."
    )
