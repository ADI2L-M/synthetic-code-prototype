from detectors.core.registry import detect_defects
from detectors.research.registry import RESEARCH_DETECTORS, detect_research_defects
from models.types import IterationResult, ProgrammingTask, SubmissionResult
from services.generation.assignment import plan_defect_assignments, stable_seed
from services.generation.analysis import compare_profiles, observed_profile
from services.generation.prompt_builder import (
    build_generation_specification,
    build_submission_specification,
)
from services.providers.demo import DemoProvider
from services.providers.llm import GenerationProvider
from services.generation.validator import validate_source


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
) -> IterationResult:
    """Run one generation and analysis iteration."""
    active_constraints = dict(constraints or {})
    specification = build_generation_specification(
        task, target_profile, active_constraints
    )
    source_provider = provider or DemoProvider()
    defect_ids = list(target_profile)
    assignment_plan = plan_defect_assignments(
        task.id,
        target_profile,
        batch_size,
        iteration_number,
    )
    submissions: list[SubmissionResult] = []

    for submission_id in range(1, batch_size + 1):
        assigned_defects = assignment_plan.by_submission[submission_id]
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
        sources = source_provider.generate(
            task,
            1,
            generation_seed,
            submission_specification,
        )
        if not sources:
            raise RuntimeError(
                f"Generation provider returned no source for submission {submission_id}."
            )
        source = sources[0]
        prompt_builder = getattr(source_provider, "build_prompt", None)
        prompt = (
            prompt_builder(task, submission_specification)
            if prompt_builder is not None
            else submission_specification
        )
        validation = validate_source(source, task)
        defects = (
            _detect_submission_defects(source, defect_ids)
            if validation.status == "PASS"
            else {}
        )
        submissions.append(
            SubmissionResult(
                submission_id,
                source,
                validation,
                defects,
                assigned_defects,
                prompt,
                generation_seed,
            )
        )

    observed = observed_profile(submissions, defect_ids)
    comparison = compare_profiles(target_profile, observed, tolerance)
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
    )
