from models.types import ProgrammingTask
from services.data_loader import load_demo_submissions
from services.llm_provider import GenerationProvider


class DemoProvider(GenerationProvider):
    """Deterministic provider used until a live LLM is explicitly integrated."""

    def generate(
        self,
        task: ProgrammingTask,
        batch_size: int,
        iteration: int = 1,
        specification: str | None = None,
    ) -> list[str]:
        try:
            variants = load_demo_submissions()[task.id]
        except KeyError as exc:
            raise ValueError(
                f"No demonstration submissions configured for task: {task.id}"
            ) from exc
        return [
            variants[(index + iteration - 1) % len(variants)]
            for index in range(batch_size)
        ]
