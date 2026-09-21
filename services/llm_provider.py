from typing import Protocol

from models.types import ProgrammingTask


class GenerationProvider(Protocol):
    """Provider contract shared by Demo mode and live LLM adapters."""

    def generate(
        self,
        task: ProgrammingTask,
        batch_size: int,
        iteration: int = 1,
        specification: str | None = None,
    ) -> list[str]: ...
