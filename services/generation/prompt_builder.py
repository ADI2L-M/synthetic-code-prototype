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

DEFECT_REQUIRED_SIGNATURES = {
    "inappropriate_formatting": "include a valid spacing violation such as `temp<10`",
    "magic_number": "use an unnamed numeric literal in the task decision logic",
    "one_letter_name": "bind a non-exempt one-letter local such as `t = temp`",
    "built_in_name": "bind a Python built-in name such as `list = temp`",
    "else_if": "include `else:` containing a nested `if`, not an `elif` replacement",
    "redundant_comparison": "include a Boolean comparison such as `(temp < 10) == True`",
    "redundant_not": "include `not` directly before a comparison such as `not temp >= 25`",
    "duplicate_if": "include an `elif` branch with the same side-effect-free body as the preceding `if`",
    "nested_if": "include an `if` directly inside another `if`, with both conditions side-effect-free",
    "redundant_elif": "include an `elif` that is the direct inverse of the preceding `if` condition",
    "empty_if": "include a branch whose only statement is `pass`",
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

TASK_SPECIFIC_PATTERNS = {
    ("T1", "inappropriate_formatting"): (
        "if temp<10:\n"
        "    return 'cold'\n"
        "if temp <= 24:\n"
        "    return 'mild'\n"
        "return 'hot'"
    ),
    ("T1", "magic_number"): (
        "if temp < 10:\n"
        "    return 'cold'\n"
        "if temp <= 24:\n"
        "    return 'mild'\n"
        "return 'hot'"
    ),
    ("T1", "one_letter_name"): (
        "t = temp\n"
        "if t < 10:\n"
        "    return 'cold'\n"
        "if t <= 24:\n"
        "    return 'mild'\n"
        "return 'hot'"
    ),
    ("T1", "built_in_name"): (
        "list = temp\n"
        "if list < 10:\n"
        "    return 'cold'\n"
        "if list <= 24:\n"
        "    return 'mild'\n"
        "return 'hot'"
    ),
    ("T2", "duplicate_expression"): (
        "total = 0\n"
        "for s in scores:\n"
        "    total = total + (s * 2 + 1) - (s * 2 + 1) + s\n"
        "return total"
    ),
    ("T2", "misleading_iterator_name"): (
        "total = 0\n"
        "for i in scores:\n"
        "    total = total + i\n"
        "return total"
    ),
    ("T2", "one_letter_name"): (
        "total = 0\n"
        "for s in scores:\n"
        "    total = total + (s * 2 + 1) - (s * 2 + 1) + s\n"
        "return total"
    ),
    ("T3", "one_letter_name"): (
        "total = 0\n"
        "for v in range(1, n + 1):\n"
        "    total = total + v\n"
        "return total"
    ),
    ("T1", "else_if"): (
        "if temp < 10:\n"
        "    return 'cold'\n"
        "else:\n"
        "    if temp <= 24:\n"
        "        return 'mild'\n"
        "    else:\n"
        "        return 'hot'"
    ),
    ("T1", "redundant_not"): (
        "if not temp >= 25:\n"
        "    if temp < 10:\n"
        "        return 'cold'\n"
        "    return 'mild'\n"
        "else:\n"
        "    return 'hot'"
    ),
    ("T1", "duplicate_if"): (
        "if temp < 5:\n"
        "    return 'cold'\n"
        "elif temp < 10:\n"
        "    return 'cold'\n"
        "if temp <= 24:\n"
        "    return 'mild'\n"
        "return 'hot'"
    ),
    ("T1", "nested_if"): (
        "if temp < 10:\n"
        "    return 'cold'\n"
        "if temp >= 10:\n"
        "    if temp < 25:\n"
        "        return 'mild'\n"
        "return 'hot'"
    ),
    ("T1", "redundant_elif"): (
        "if temp < 10:\n"
        "    return 'cold'\n"
        "elif temp >= 10:\n"
        "    if temp <= 24:\n"
        "        return 'mild'\n"
        "    return 'hot'"
    ),
    ("T1", "empty_if"): (
        "if temp < 10:\n"
        "    pass\n"
        "else:\n"
        "    if temp <= 24:\n"
        "        return 'mild'\n"
        "    return 'hot'\n"
        "return 'cold'"
    ),
    ("T1", "redundant_comparison"): (
        "if (temp < 10) == True:\n"
        "    return 'cold'\n"
        "if temp <= 24:\n"
        "    return 'mild'\n"
        "return 'hot'"
    ),
    ("T2", "augmentable_assignment"): (
        "for score in scores:\n"
        "    total = total + score"
    ),
    ("T3", "augmentable_assignment"): (
        "for value in range(1, n + 1):\n"
        "    total = total + value"
    ),
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


def _task_defect_names(task_id: str, category: str) -> tuple[str, ...]:
    """Return every catalogue defect applicable to a task and category."""
    return tuple(
        item["name"]
        for item in _defect_catalog().values()
        if item.get("category") == category
        and task_id in item.get("applicable_tasks", [])
    )


def applicable_defect_names(task: ProgrammingTask, category: str) -> tuple[str, ...]:
    """Return catalogue defects that can be generated for a task category."""
    return _task_defect_names(task.id, category)


def _calibration_section(constraints: dict[str, str] | None) -> str:
    if not constraints:
        return ""
    rows = "\n".join(
        f"- {defect.replace('_', ' ')}: {instruction}"
        for defect, instruction in constraints.items()
    )
    return (
        "\n\nCALIBRATION ADJUSTMENTS\n\n"
        "These actions update the next iteration's defect emphasis. Follow them "
        "without breaking functional correctness or the mandatory category requirement.\n"
        + rows
    )


def build_generation_specification(
    task: ProgrammingTask,
    target: dict[str, float],
    constraints: dict[str, str] | None = None,
) -> str:
    del target
    independent_names = applicable_defect_names(task, "task_independent")
    dependent_names = applicable_defect_names(task, "task_dependent")
    return (
        f"PROGRAMMING TASK\n\n{task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\nPOTENTIAL TASK-INDEPENDENT DEFECTS\n\n"
        + "\n".join(f"- {name.replace('_', ' ')}" for name in independent_names)
        + "\n\nPOTENTIAL TASK-DEPENDENT DEFECTS\n\n"
        + "\n".join(f"- {name.replace('_', ' ')}" for name in dependent_names)
        + "\n\nGENERATION FOCUS\n\n"
        "Task-dependent structural defects are the primary research focus. "
        "When a task-dependent defect is assigned in the submission brief, "
        "implement that exact structure while preserving functional correctness. "
        "Do not substitute a task-independent style."
        + _calibration_section(constraints)
        + "\n\nIMPORTANT\n\nThe program must remain functionally correct."
    )


def build_submission_specification(
    task: ProgrammingTask,
    assigned_defects: tuple[str, ...],
    constraints: dict[str, str] | None = None,
) -> str:
    """Build a detailed, per-submission defect-guidance brief."""
    independent_names = applicable_defect_names(task, "task_independent")
    dependent_names = applicable_defect_names(task, "task_dependent")
    assigned_task_dependent = tuple(
        defect for defect in assigned_defects if defect in dependent_names
    )
    independent_section = "\n".join(
        f"- {name.replace('_', ' ')}" for name in independent_names
    ) or "- None applicable to this task."
    dependent_section = "\n".join(
        f"- {name.replace('_', ' ')}" for name in dependent_names
    ) or "- None applicable to this task."
    assigned_task_dependent_names = "\n".join(
        f"- {defect.replace('_', ' ')}" for defect in assigned_task_dependent
    ) or "- None assigned; choose a task-dependent defect from the list."
    assigned_task_independent = tuple(
        defect for defect in assigned_defects if defect in independent_names
    )
    assigned_task_independent_names = "\n".join(
        f"- {defect.replace('_', ' ')}" for defect in assigned_task_independent
    ) or "- None assigned; choose a task-independent defect from the list."
    guidance_defects = tuple(
        dict.fromkeys(assigned_task_independent + assigned_task_dependent)
    )
    guidance_sections: list[str] = []
    for defect in guidance_defects:
        hint = GENERATION_HINTS.get(defect)
        example = GENERATION_EXAMPLES.get(defect, {}).get("defective")
        if hint:
            guidance = f"- {defect.replace('_', ' ')}: {hint}"
            signature = DEFECT_REQUIRED_SIGNATURES.get(defect)
            if signature:
                guidance += f" Required observable signature: {signature}."
            if example:
                guidance += f" Example pattern:\n    {example}"
            task_pattern = TASK_SPECIFIC_PATTERNS.get((task.id, defect))
            if task_pattern:
                guidance += (
                    "\n  Task-specific valid pattern to adapt:\n    "
                    + task_pattern.replace("\n", "\n    ")
                )
            guidance_sections.append(guidance)
    guidance = "\n".join(guidance_sections) or "- Use the task contract to construct the required styles."
    assigned_section = (
        "REFERENCE DEFECT CATALOG — names only; do not implement every item:\n\n"
        "Task-Independent defects:\n\n"
        + independent_section
        + "\n\n"
        "Task-Dependent defects:\n\n"
        + dependent_section
        + "\n\nMANDATORY SELECTED DEFECTS — implement these two styles:\n\n"
        + "Task-independent:\n"
        + assigned_task_independent_names
        + "\nASSIGNED TASK-DEPENDENT DEFECTS TO PRIORITISE:\n"
        + assigned_task_dependent_names
        + "\n\nMANDATORY CATEGORY REQUIREMENT:\n\n"
        + "- Include at least one task-independent defect.\n"
        + "- Include at least one task-dependent defect.\n"
        + "Include at least one task-independent and at least one task-dependent "
        "defect. The two selected defects above are the simplest required choices; "
        "do not substitute another style.\n\n"
        "MANDATORY DEFECT IMPLEMENTATION GUIDANCE:\n\n"
        + guidance
        + "\n\nGENERATION PROCEDURE:\n\n"
        "1. Write the complete function so every functional requirement and evaluator "
        "case is satisfied.\n"
        "2. Add the selected task-independent style without changing behavior.\n"
        "3. Add the selected task-dependent style without changing behavior.\n"
        "4. Recheck every evaluator case and remove any module-level execution."
    )

    return (
        "SUBMISSION GENERATION BRIEF\n\n"
        "ROLE\n\n"
        "You are generating one python submission imitating a CS1 student with beginner programming coding style. "
        "The coding style is stated in two distinct categories: task-dependent and task-independent. "
        "The source will be executed and structurally evaluated after generation.\n\n"
        "PROGRAMMING TASK\n\n"
        f"Task ID: {task.id}\n"
        f"Function to implement: {task.function_name}\n"
        f"Task contexts: {', '.join(task.contexts)}\n"
        f"Description: {task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\nFUNCTIONAL COVERAGE CHECKLIST\n\n"
        + "Before returning the source, mentally evaluate the required function "
        + "for every evaluator case and ensure every listed input has an explicit "
        + "return path with the required result. Do not copy the evaluator cases "
        + "into the submission.\n"
        + "\n".join(
            f"- {task.function_name}({', '.join(repr(arg) for arg in case.args)}) "
            + (
                f"must raise {case.raises}"
                if case.raises
                else f"must return {case.expected!r}"
            )
            for case in task.test_cases
        )
        + "\n\nASSIGNED DEFECT STYLE BRIEFS\n\n"
        + assigned_section
        + "\n\nGENERATION OBJECTIVE\n\n"
        + "Include at least one defect from each category while preserving "
        + "functional correctness. If one construction conflicts with the task, "
        + "revise the construction rather than omitting the category.\n\n"
        + _calibration_section(constraints)
        + "\n\n"
        "PRIVATE PRE-RETURN CHECK\n\n"
        "Before returning the source, silently check that the required function "
        "exists, every functional requirement is satisfied, every mandatory "
        "assigned style is represented as described, excluded forms are avoided, and the result "
        "contains only executable Python code.\n\n"
        "OUTPUT CONTRACT\n\n"
        "Return only the complete executable Python source for the required function. "
        "Define the required function and do not execute anything at module level. "
        "The functional test cases are evaluator inputs, not code to copy. Do not "
        "include print(), input(), assertions, test cases, a test harness, Markdown, "
        "explanations, or a partial revision.\n\n"
        "IMPORTANT NOTE:\n\n"
        "Implementing coding style is mandatory, do not return the submission without including the task-dependent coding style criteria. "
        "The defect guidance is a hard acceptance criterion, not a suggestion. "
        "Copy the key syntax and control-flow shape of every task-specific valid pattern."
    )
