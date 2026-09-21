from typing import Protocol

from models.types import ProgrammingTask


class GenerationProvider(Protocol):
    """Provider contract shared by Demo mode and a future live LLM adapter."""

    def generate(
        self, task: ProgrammingTask, batch_size: int, iteration: int = 1
    ) -> list[str]: ...
