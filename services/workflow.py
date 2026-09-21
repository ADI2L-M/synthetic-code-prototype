from detectors.registry import detect_defects
from models.types import IterationResult, ProgrammingTask, SubmissionResult
from services.analysis import compare_profiles, observed_profile
from services.demo_provider import DemoProvider
from services.llm_provider import GenerationProvider
from services.prompt_builder import build_generation_specification
from services.validator import validate_source


def run_iteration(
    task: ProgrammingTask,
    target_profile: dict[str, float],
    batch_size: int,
    iteration_number: int,
    tolerance: float,
    constraints: dict[str, str] | None = None,
    provider: GenerationProvider | None = None,
) -> IterationResult:
    """Run one generation and analysis iteration."""
    active_constraints = dict(constraints or {})
    specification = build_generation_specification(
        task, target_profile, active_constraints
    )
    source_provider = provider or DemoProvider()
    sources = source_provider.generate(
        task, batch_size, iteration_number, specification
    )
    defect_ids = list(target_profile)
    submissions: list[SubmissionResult] = []

    for submission_id, source in enumerate(sources, start=1):
        validation = validate_source(source, task)
        defects = (
            detect_defects(source, defect_ids) if validation.status == "PASS" else {}
        )
        submissions.append(SubmissionResult(submission_id, source, validation, defects))

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
    )
