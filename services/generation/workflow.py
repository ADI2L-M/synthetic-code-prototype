from collections.abc import Callable

from detectors.core.registry import detect_defects
from detectors.research.registry import RESEARCH_DETECTORS, detect_research_defects
from models.types import IterationResult, ProgrammingTask, SubmissionResult
from services.generation.analysis import (
    compare_profiles,
    observed_counts,
    observed_profile,
)
from services.generation.assignment import plan_defect_assignments, stable_seed
from services.generation.jobs import GenerationCancelled
from services.generation.prompt_builder import (
    DEFECT_REQUIRED_SIGNATURES,
    GENERATION_AVOIDANCE_HINTS,
    TASK_INDEPENDENT_DEFECTS,
    TASK_SPECIFIC_PATTERNS,
    applicable_defect_names,
    build_baseline_specification,
    build_generation_specification,
    build_submission_specification,
    generation_policy,
)
from services.generation.validator import validate_source
from services.providers.demo import DemoProvider
from services.providers.llm import GenerationProvider

MAX_CATEGORY_REPAIR_ATTEMPTS = 2
MAX_SUBMISSION_ATTEMPTS = MAX_CATEGORY_REPAIR_ATTEMPTS + 1
BASELINE_CONDITION = "non_adaptive_baseline"
TASK_AWARE_CONDITION = "task_aware_non_adaptive"
ITERATIVE_CONDITION = "task_aware_iterative"
GENERATION_CONDITIONS = (
    BASELINE_CONDITION,
    TASK_AWARE_CONDITION,
    ITERATIVE_CONDITION,
)

RELIABLE_DEFECT_ORDER = generation_policy("reliable_defect_order")
TASK_RELIABLE_DEFECT_ORDER = generation_policy("task_reliable_defect_order")


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


def _repair_quality(
    validation,
    missing_categories: tuple[str, ...],
    missing_defects: tuple[str, ...],
    unexpected_defects: tuple[str, ...],
) -> tuple[int, int, int, int, int]:
    """Rank one generation attempt by repair-requirement compliance.

    Functional validity is the first priority. Among attempts with the same
    functional status, fewer unresolved requirements are better. The tuple is
    ordered so that the first acceptable attempt remains preferred when two
    candidates are otherwise tied.
    """
    unresolved = (
        len(missing_categories)
        + len(missing_defects)
        + len(unexpected_defects)
    )
    return (
        int(validation.status == "PASS"),
        -unresolved,
        -len(missing_categories),
        -len(missing_defects),
        -len(unexpected_defects),
    )

def _repair_specification(
    task: ProgrammingTask,
    assigned_defects: tuple[str, ...],
    source: str,
    validation_message: str,
    missing_categories: tuple[str, ...],
    missing_defects: tuple[str, ...],
    unexpected_defects: tuple[str, ...],
    condition: str = TASK_AWARE_CONDITION,
) -> str:
    missing_text = ", ".join(missing_categories) or "none"
    assigned_text = ", ".join(
        defect.replace("_", " ") for defect in assigned_defects
    ) or "no intentional defect style; repair functional correctness only"
    missing_defect_text = ", ".join(
        defect.replace("_", " ") for defect in missing_defects
    ) or "none"
    unexpected_defect_text = ", ".join(
        defect.replace("_", " ") for defect in unexpected_defects
    ) or "none"
    task_patterns = []
    for defect in missing_defects or assigned_defects:
        pattern = TASK_SPECIFIC_PATTERNS.get((task.id, defect))
        if pattern:
            task_patterns.append(
                f"{defect.replace('_', ' ')}:\n{pattern}"
            )
    pattern_text = "\n\n".join(task_patterns) or (
        "Repair the functional contract without adding intentional defect styles."
    )
    signature_text = "\n".join(
        f"- {defect.replace('_', ' ')}: {DEFECT_REQUIRED_SIGNATURES[defect]}"
        for defect in missing_defects
        if defect in DEFECT_REQUIRED_SIGNATURES
    )
    if signature_text:
        pattern_text += "\n\nREQUIRED OBSERVABLE SIGNATURES\n" + signature_text
    avoidance_text = "\n".join(
        f"- {defect.replace('_', ' ')}: "
        + GENERATION_AVOIDANCE_HINTS.get(
            defect, "remove this unassigned style from the source."
        )
        for defect in unexpected_defects
    ) or "- none"
    baseline_marker = (
        "PROMPTING CONDITION: NON-ADAPTIVE BASELINE\n\n"
        if condition == BASELINE_CONDITION
        else ""
    )
    return (
        baseline_marker
        + "REVISION REQUEST\n\n"
        f"Implement {task.function_name}(...) for this task: {task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\nFAILED VALIDATION\n"
        + (validation_message or "The previous source was not accepted.")
        + f"\nMissing categories: {missing_text}\n"
        + f"Missing selected defect styles: {missing_defect_text}\n"
        + f"Unassigned detected styles to remove: {unexpected_defect_text}\n"
        + f"Required selected styles: {assigned_text}\n\n"
        + "ADAPT THIS STYLE PATTERN INSIDE THE FUNCTION\n"
        + pattern_text
        + "\n\nPREVIOUS SOURCE\n"
        + source
        + "\n\nREPAIR RULES\n"
        "- Keep every required behavior and add all missing return paths.\n"
        "- Add every missing selected defect style listed above; do not omit it.\n"
        "- Remove every unassigned detected style listed above.\n"
        "- Use the style pattern inside the required function; do not copy it as a separate example.\n"
        + "\nUNASSIGNED STYLE REMOVAL GUIDANCE\n"
        + avoidance_text
        + "\n"
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
    temperature: float | None = None,
    max_repair_attempts: int = 0,
    target_standard_errors: dict[str, float] | None = None,
    condition: str = TASK_AWARE_CONDITION,
    seed_namespace: str = "",
    progress_callback: Callable[[str, int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> IterationResult:
    """Run one generation and analysis iteration."""
    active_constraints = dict(constraints or {})
    if max_repair_attempts < 0:
        raise ValueError("max_repair_attempts cannot be negative")
    if condition not in GENERATION_CONDITIONS:
        raise ValueError(f"Unknown generation condition: {condition}")
    guided = condition != BASELINE_CONDITION
    specification = (
        build_generation_specification(task, target_profile, active_constraints)
        if guided
        else build_baseline_specification(task)
    )
    source_provider = provider or DemoProvider()
    defect_ids = list(target_profile)
    required_defect_ids = (
        list(
            dict.fromkeys(
                applicable_defect_names(task, "task_independent")
                + applicable_defect_names(task, "task_dependent")
            )
        )
        if guided
        else []
    )
    detection_ids = list(dict.fromkeys(defect_ids + required_defect_ids))
    assignment_plan = plan_defect_assignments(
        task.id,
        target_profile if guided else {},
        batch_size,
        iteration_number,
        seed_namespace=seed_namespace,
    )
    submissions: list[SubmissionResult] = []

    def check_cancelled() -> None:
        if cancel_check is not None and cancel_check():
            raise GenerationCancelled("Generation cancelled by user.")

    for submission_id in range(1, batch_size + 1):
        check_cancelled()
        if progress_callback is not None:
            progress_callback(
                f"Preparing submission {submission_id} of {batch_size}",
                submission_id - 1,
                batch_size,
            )
        if guided:
            mandatory_defects = _mandatory_category_assignments(
                task, target_profile, submission_id, active_constraints
            )
            planned_defects = assignment_plan.by_submission.get(submission_id, ())
            assigned_defects = tuple(
                dict.fromkeys(planned_defects + mandatory_defects)
            )
        else:
            assigned_defects = ()
        submission_specification = (
            build_submission_specification(task, assigned_defects, active_constraints)
            if guided
            else specification
        )
        generation_parts = (
            (seed_namespace, task.id, iteration_number, submission_id, "generation")
            if seed_namespace
            else (task.id, iteration_number, submission_id, "generation")
        )
        generation_seed = stable_seed(*generation_parts)
        attempt_specification = submission_specification
        source = ""
        prompt = submission_specification
        validation = None
        defects: dict[str, bool] = {}
        missing_categories: tuple[str, ...] = ()
        missing_defects: tuple[str, ...] = ()
        unexpected_defects: tuple[str, ...] = ()
        attempt_count = 0
        best_attempt = None
        best_quality = None
        for attempt in range(1, max_repair_attempts + 2):
            check_cancelled()
            attempt_count = attempt
            if progress_callback is not None:
                progress_callback(
                    f"Generating submission {submission_id} of {batch_size} "
                    f"(attempt {attempt}/{max_repair_attempts + 1})",
                    submission_id - 1,
                    batch_size,
                )
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
                    *(
                        (
                            seed_namespace,
                            task.id,
                            iteration_number,
                            submission_id,
                            "repair",
                            attempt,
                        )
                        if seed_namespace
                        else (
                            task.id,
                            iteration_number,
                            submission_id,
                            "repair",
                            attempt,
                        )
                    )
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
            check_cancelled()
            validation = validate_source(source, task)
            if progress_callback is not None:
                progress_callback(
                    f"Validating submission {submission_id} of {batch_size}",
                    submission_id - 1,
                    batch_size,
                )
            defects = (
                _detect_submission_defects(source, detection_ids)
                if validation.status == "PASS"
                else {}
            )
            missing_categories = (
                _missing_defect_categories(required_defect_ids, defects)
                if validation.status == "PASS"
                else (
                    ("functional-correctness",)
                    if not guided
                    else (
                        "functional-correctness",
                        "task-independent",
                        "task-dependent",
                    )
                )
            )
            missing_defects = tuple(
                defect
                for defect in assigned_defects
                if not defects.get(defect, False)
            )
            unexpected_defects = tuple(
                defect
                for defect, present in defects.items()
                if guided and present and defect not in assigned_defects
            )

            candidate_quality = _repair_quality(
                validation,
                missing_categories,
                missing_defects,
                unexpected_defects,
            )
            if best_quality is None or candidate_quality > best_quality:
                best_quality = candidate_quality
                best_attempt = {
                    "source": source,
                    "prompt": prompt,
                    "validation": validation,
                    "defects": dict(defects),
                    "missing_categories": missing_categories,
                    "missing_defects": missing_defects,
                    "unexpected_defects": unexpected_defects,
                }

            if candidate_quality == (
                1,
                0,
                0,
                0,
                0,
            ):
                break
            if attempt <= max_repair_attempts:
                attempt_specification = _repair_specification(
                    task,
                    assigned_defects,
                    source,
                    validation.failure_message,
                    missing_categories,
                    missing_defects,
                    unexpected_defects,
                    condition=condition,
                )

        assert best_attempt is not None
        source = best_attempt["source"]
        prompt = best_attempt["prompt"]
        validation = best_attempt["validation"]
        defects = best_attempt["defects"]
        missing_categories = best_attempt["missing_categories"]
        missing_defects = best_attempt["missing_defects"]
        unexpected_defects = best_attempt["unexpected_defects"]
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
                validation.status == "PASS"
                and not missing_categories
                and not missing_defects
                and not unexpected_defects,
                missing_categories,
            )
        )
        if progress_callback is not None:
            progress_callback(
                f"Completed submission {submission_id} of {batch_size}",
                submission_id,
                batch_size,
            )

    if progress_callback is not None:
        progress_callback("Calculating prevalence and profile alignment", batch_size, batch_size)
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
        temperature=temperature,
        target_standard_errors=dict(target_standard_errors or {}),
        condition=condition,
    )
