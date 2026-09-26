"""Run empirical prototype generation through the shared generation workflow."""

from __future__ import annotations

from models.types import IterationResult
from services.generation.prototype_tasks import load_prototype_task
from services.generation.workflow import run_iteration
from services.providers.ollama import OLLAMA_CONTEXT_LENGTH, OllamaProvider


def run_prototype_iteration(
    task_id: str,
    target_profile: dict[str, float],
    batch_size: int,
    iteration_number: int,
    tolerance: float,
    model: str,
    base_url: str,
) -> IterationResult:
    """Generate and validate one synthetic batch for T1, T2, or T3."""
    task = load_prototype_task(task_id)
    return run_iteration(
        task=task,
        target_profile=target_profile,
        batch_size=batch_size,
        iteration_number=iteration_number,
        tolerance=tolerance,
        provider=OllamaProvider(model=model, base_url=base_url),
        model=model,
        context_length=OLLAMA_CONTEXT_LENGTH,
    )
