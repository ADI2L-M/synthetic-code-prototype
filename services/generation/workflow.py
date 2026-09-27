from detectors.core.registry import detect_defects
from detectors.research.registry import RESEARCH_DETECTORS, detect_research_defects
from models.types import IterationResult, ProgrammingTask, SubmissionResult
from services.generation.analysis import (
    compare_profiles,
    observed_counts,
    observed_profile,
)
from services.generation.assignment import plan_defect_assignments, stable_seed
from services.generation.prompt_builder import (
    DEFECT_REQUIRED_SIGNATURES,
    TASK_INDEPENDENT_DEFECTS,
    TASK_SPECIFIC_PATTERNS,
    applicable_defect_names,
    build_generation_specification,
    build_submission_specification,
)
from services.generation.validator import validate_source
from services.providers.demo import DemoProvider
from services.providers.llm import GenerationProvider

MAX_CATEGORY_REPAIR_ATTEMPTS = 2
MAX_SUBMISSION_ATTEMPTS = MAX_CATEGORY_REPAIR_ATTEMPTS + 1

RELIABLE_DEFECT_ORDER = {
    "task_independent": (
        "magic_number",
        "one_letter_name",
        "built_in_name",
        "inappropriate_formatting",
    ),
    "task_dependent": (
        "else_if",
        "augmentable_assignment",
        "redundant_comparison",
        "redundant_not",
    ),
}

TASK_RELIABLE_DEFECT_ORDER = {
    "T1": {
        "task_independent": (
            "magic_number",
            "one_letter_name",
            "built_in_name",
            "inappropriate_formatting",
        ),
        "task_dependent": (
            "duplicate_if",
            "empty_if",
            "redundant_comparison",
            "redundant_not",
            "nested_if",
            "redundant_elif",
            "else_if",
        ),
    },
    "T2": {
        "task_independent": (
            "one_letter_name",
            "built_in_name",
            "magic_number",
            "inappropriate_formatting",
        ),
        "task_dependent": (
            "duplicate_expression",
            "misleading_iterator_name",
            "augmentable_assignment",
        ),
    },
    "T3": {
        "task_independent": (
            "one_letter_name",
            "built_in_name",
            "magic_number",
            "inappropriate_formatting",
        ),
        "task_dependent": ("augmentable_assignment",),
    },
}


def _detect_submission_defects(
    source: str,
    defect_ids: list[str],
) -> dict[str, bool]:
    if not defect_ids:
        return {}
    if set(defect_ids).issubset(RESEARCH_DETECTORS):
        results = detect_research_defects(source, defect_ids)
        return {defect: result.present for defect, result in results.items()}
    return detect_defects(source, defect_ids)


def _missing_defect_categories(
    defect_ids: list[str],
    defects: dict[str, bool],
) -> tuple[str, ...]:
    """Return required categories not represented in a valid submission."""
    missing: list[str] = []
    if (
        any(defect in TASK_INDEPENDENT_DEFECTS for defect in defect_ids)
        and not any(
            defects.get(defect, False)
            for defect in defect_ids
            if defect in TASK_INDEPENDENT_DEFECTS
        )):
            missing.append("task-independent")
    if (
        any(defect not in TASK_INDEPENDENT_DEFECTS for defect in defect_ids)
        and not any(
            defects.get(defect, False)
            for defect in defect_ids
            if defect not in TASK_INDEPENDENT_DEFECTS
        )):
            missing.append("task-dependent")
    return tuple(missing)


def _repair_specification(
    task: ProgrammingTask,
    assigned_defects: tuple[str, ...],
    source: str,
    validation_message: str,
    missing_categories: tuple[str, ...],
    missing_defects: tuple[str, ...],
) -> str:
    missing_text = ", ".join(missing_categories) or "none"
    assigned_text = ", ".join(
        defect.replace("_", " ") for defect in assigned_defects
    ) or "one task-independent and one task-dependent defect"
    missing_defect_text = ", ".join(
        defect.replace("_", " ") for defect in missing_defects
    ) or "none"
    task_patterns = []
    for defect in missing_defects or assigned_defects:
        pattern = TASK_SPECIFIC_PATTERNS.get((task.id, defect))
        if pattern:
            task_patterns.append(
                f"{defect.replace('_', ' ')}:\n{pattern}"
            )
    pattern_text = "\n\n".join(task_patterns) or (
        "Use the selected defect names while preserving the task contract."
    )
    signature_text = "\n".join(
        f"- {defect.replace('_', ' ')}: {DEFECT_REQUIRED_SIGNATURES[defect]}"
        for defect in missing_defects
        if defect in DEFECT_REQUIRED_SIGNATURES
    )
    if signature_text:
        pattern_text += "\n\nREQUIRED OBSERVABLE SIGNATURES\n" + signature_text
    return (
        "REVISION REQUEST\n\n"
        f"Implement {task.function_name}(...) for this task: {task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\nFAILED VALIDATION\n"
        + (validation_message or "The previous source was not accepted.")
        + f"\nMissing categories: {missing_text}\n"
        + f"Missing selected defect styles: {missing_defect_text}\n"
        + f"Required selected styles: {assigned_text}\n\n"
        + "ADAPT THIS STYLE PATTERN INSIDE THE FUNCTION\n"
        + pattern_text
        + "\n\nPREVIOUS SOURCE\n"
        + source
        + "\n\nREPAIR RULES\n"
        "- Keep every required behavior and add all missing return paths.\n"
        "- Add every missing selected defect style listed above; do not omit it.\n"
        "- Use the style pattern inside the required function; do not copy it as a separate example.\n"
        "- Return only the function definition. Do not include print(), input(), tests, a test harness, comments outside the function, Markdown, or explanations."
    )


def _mandatory_category_assignments(
    task: ProgrammingTask,
    target_profile: dict[str, float],
    submission_id: int,
    constraints: dict[str, str],
) -> tuple[str, ...]:
    """Select one reproducible defect from each task category."""
    selected: list[str] = []
    for category in ("task_independent", "task_dependent"):
        names = list(applicable_defect_names(task, category))
        if not names:
            continue
        preferred_order = TASK_RELIABLE_DEFECT_ORDER.get(
            task.id, {}
        ).get(category, RELIABLE_DEFECT_ORDER[category])
        candidates = [defect for defect in preferred_order if defect in names]
        if not candidates:
            candidates = names
        calibration_priority = {
            "strengthen the generation constraint": 0,
            "maintain the generation constraint": 1,
            "reduce the generation constraint": 2,
        }
        ordered = sorted(
            candidates,
            key=lambda defect: (
                calibration_priority.get(constraints.get(defect, ""), 1),
                preferred_order.index(defect)
                if defect in preferred_order
                else len(preferred_order),
                -target_profile.get(defect, 0.0),
                defect,
            ),
        )
        selected.append(ordered[(submission_id - 1) % len(ordered)])
    return tuple(selected)


def run_iteration(
    task: ProgrammingTask,
    target_profile: dict[str, float],
    batch_size: int,
    iteration_number: int,
    tolerance: float,
    constraints: dict[str, str] | None = None,
    provider: GenerationProvider | None = None,
    model: str | None = None,
    context_length: int | None = None,
    max_repair_attempts: int = 0,
    target_standard_errors: dict[str, float] | None = None,
) -> IterationResult:
    """Run one generation and analysis iteration."""
    active_constraints = dict(constraints or {})
    if max_repair_attempts < 0:
        raise ValueError("max_repair_attempts cannot be negative")
    specification = build_generation_specification(
        task, target_profile, active_constraints
    )
    source_provider = provider or DemoProvider()
    defect_ids = list(target_profile)
    required_defect_ids = list(
        dict.fromkeys(
            applicable_defect_names(task, "task_independent")
            + applicable_defect_names(task, "task_dependent")
        )
    )
    detection_ids = list(dict.fromkeys(defect_ids + required_defect_ids))
    assignment_plan = plan_defect_assignments(
        task.id,
        target_profile,
        batch_size,
        iteration_number,
    )
    submissions: list[SubmissionResult] = []

    for submission_id in range(1, batch_size + 1):
        assigned_defects = _mandatory_category_assignments(
            task, target_profile, submission_id, active_constraints
        )
        submission_specification = build_submission_specification(
            task,
            assigned_defects,
            active_constraints,
        )
        generation_seed = stable_seed(
            task.id,
            iteration_number,
            submission_id,
            "generation",
        )
        attempt_specification = submission_specification
        source = ""
        prompt = submission_specification
        validation = None
        defects: dict[str, bool] = {}
        missing_categories: tuple[str, ...] = ()
        missing_defects: tuple[str, ...] = ()
        attempt_count = 0
        for attempt in range(1, max_repair_attempts + 2):
            attempt_count = attempt
            prompt_builder = getattr(source_provider, "build_prompt", None)
            prompt = (
                prompt_builder(task, attempt_specification)
                if prompt_builder is not None
                else attempt_specification
            )
            attempt_seed = (
                generation_seed
                if attempt == 1
                else stable_seed(
                    task.id,
                    iteration_number,
                    submission_id,
                    "repair",
                    attempt,
                )
            )
            sources = source_provider.generate(
                task,
                1,
                attempt_seed,
                attempt_specification,
            )
            if not sources:
                raise RuntimeError(
                    f"Generation provider returned no source for submission {submission_id}."
                )
            source = sources[0]
            validation = validate_source(source, task)
            defects = (
                _detect_submission_defects(source, detection_ids)
                if validation.status == "PASS"
                else {}
            )
            missing_categories = (
                _missing_defect_categories(required_defect_ids, defects)
                if validation.status == "PASS"
                else ("functional-correctness", "task-independent", "task-dependent")
            )
            missing_defects = tuple(
                defect
                for defect in assigned_defects
                if not defects.get(defect, False)
            )
            if validation.status == "PASS" and not missing_categories:
                break
            if attempt <= max_repair_attempts:
                attempt_specification = _repair_specification(
                    task,
                    assigned_defects,
                    source,
                    validation.failure_message,
                    missing_categories,
                    missing_defects,
                )

        assert validation is not None
        submissions.append(
            SubmissionResult(
                submission_id,
                source,
                validation,
                defects,
                assigned_defects,
                prompt,
                generation_seed,
                attempt_count,
                validation.status == "PASS" and not missing_categories,
                missing_categories,
            )
        )

    observed = observed_profile(submissions, defect_ids)
    counts, valid_denominator = observed_counts(submissions, defect_ids)
    comparison = compare_profiles(
        target_profile,
        observed,
        tolerance,
        observed_denominator=valid_denominator,
        target_standard_errors=target_standard_errors,
        observed_counts_by_defect=counts,
    )
    return IterationResult(
        iteration=iteration_number,
        task_id=task.id,
        task_name=task.name,
        target_profile=dict(target_profile),
        tolerance=tolerance,
        constraints=active_constraints,
        specification=specification,
        submissions=submissions,
        observed_profile=observed,
        comparison=comparison,
        assignment_seed=assignment_plan.seed,
        expected_assignment_counts=assignment_plan.expected_counts,
        planned_assignment_counts=assignment_plan.planned_counts,
        model=model,
        context_length=context_length,
        target_standard_errors=dict(target_standard_errors or {}),
    )
