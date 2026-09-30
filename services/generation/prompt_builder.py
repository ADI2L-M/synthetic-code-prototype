from models.types import ProgrammingTask
from services.generation.configuration import (
    applicable_defect_names as configured_applicable_defect_names,
)
from services.generation.configuration import (
    defect_names_by_category,
    generation_policy,
)

TASK_INDEPENDENT_DEFECTS = defect_names_by_category("task_independent")
GENERATION_HINTS = generation_policy("hints")
GENERATION_AVOIDANCE_HINTS = generation_policy("avoidance_hints")
DEFECT_REQUIRED_SIGNATURES = generation_policy("required_signatures")
GENERATION_EXAMPLES = generation_policy("examples")
TASK_SPECIFIC_PATTERNS = {
    (task_id, defect): pattern
    for task_id, patterns in generation_policy("task_specific_patterns").items()
    for defect, pattern in patterns.items()
}

def _task_defect_names(task_id: str, category: str) -> tuple[str, ...]:
    """Return every catalogue defect applicable to a task and category."""
    return configured_applicable_defect_names(task_id, category)


def applicable_defect_names(task: ProgrammingTask, category: str) -> tuple[str, ...]:
    """Return catalogue defects that can be generated for a task category."""
    return _task_defect_names(task.id, category)


def _task_pattern_without_magic_number(task_id: str, pattern: str) -> str:
    """Keep task examples functional while avoiding unassigned magic numbers."""
    if task_id != "T1":
        return pattern
    replacements = (
        ("10", "COLD_LIMIT"),
        ("24", "MILD_LIMIT"),
        ("25", "HOT_LIMIT"),
    )
    declarations: list[str] = []
    for literal, name in replacements:
        if literal in pattern:
            pattern = pattern.replace(literal, name)
            declarations.append(f"{name} = {literal}")
    return "\n".join(declarations + [pattern])


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


def build_baseline_specification(task: ProgrammingTask) -> str:
    """Build the task-only prompt specification for the baseline condition."""
    return (
        "PROMPTING CONDITION: NON-ADAPTIVE BASELINE\n\n"
        "Generate a conventional implementation from the task contract only. "
        "Do not add any generation objective beyond functional correctness.\n\n"
        f"PROGRAMMING TASK\n\n{task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
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
    assigned_set = set(guidance_defects)
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
                if "magic_number" not in assigned_set:
                    task_pattern = _task_pattern_without_magic_number(
                        task.id, task_pattern
                    )
                guidance += (
                    "\n  Task-specific valid pattern to adapt:\n    "
                    + task_pattern.replace("\n", "\n    ")
                )
            guidance_sections.append(guidance)
    guidance = "\n".join(guidance_sections) or "- Use the task contract to construct the required styles."
    unassigned_names = tuple(
        name
        for name in independent_names + dependent_names
        if name not in assigned_set
    )
    avoidance_sections = []
    for defect in unassigned_names:
        hint = GENERATION_AVOIDANCE_HINTS.get(defect)
        avoidance_sections.append(
            f"- {defect.replace('_', ' ')}: "
            + (hint or "do not intentionally create this style.")
        )
    avoidance = "\n".join(avoidance_sections) or "- None; all applicable styles are assigned."
    assigned_section = (
        "REFERENCE DEFECT CATALOG — names only; do not implement every item:\n\n"
        "Task-Independent defects:\n\n"
        + independent_section
        + "\n\n"
        "Task-Dependent defects:\n\n"
        + dependent_section
        + "\n\nMANDATORY SELECTED DEFECTS — implement every listed style:\n\n"
        + "Task-independent:\n"
        + assigned_task_independent_names
        + "\nASSIGNED TASK-DEPENDENT DEFECTS TO PRIORITISE:\n"
        + assigned_task_dependent_names
        + "\n\nMANDATORY CATEGORY REQUIREMENT:\n\n"
        + "- Include at least one task-independent defect.\n"
        + "- Include at least one task-dependent defect.\n"
        + "Include at least one task-independent and at least one task-dependent "
        "defect. Do not substitute another style for a listed assignment.\n\n"
        "MANDATORY DEFECT IMPLEMENTATION GUIDANCE:\n\n"
        + guidance
        + "\n\nUNASSIGNED DEFECTS TO AVOID:\n\n"
        + avoidance
        + "\n\nGENERATION PROCEDURE:\n\n"
        "1. Write the complete function so every functional requirement and evaluator "
        "case is satisfied.\n"
        "2. Add every selected task-independent style without changing behavior.\n"
        "3. Add every selected task-dependent style without changing behavior.\n"
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
