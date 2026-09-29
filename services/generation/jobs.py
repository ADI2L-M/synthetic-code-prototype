"""Background generation jobs for the interactive Streamlit workflow."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event
from typing import Any


class GenerationCancelled(RuntimeError):
    """Raised when the user cancels a generation job."""


@dataclass(frozen=True)
class GenerationProgress:
    message: str
    completed: int
    total: int


ProgressCallback = Callable[[str, int, int], None]
JobWorker = Callable[[ProgressCallback, Callable[[], bool]], Any]

_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="generation")


class GenerationJob:
    """Run one generation request outside the Streamlit script thread."""

    def __init__(self, worker: JobWorker) -> None:
        self._cancel_event = Event()
        self._events: Queue[GenerationProgress] = Queue()
        self._latest = GenerationProgress("Preparing generation...", 0, 1)
        self._future: Future[Any] = _EXECUTOR.submit(self._run, worker)

    def _run(self, worker: JobWorker) -> Any:
        return worker(self.publish_progress, self.cancel_requested)

    def publish_progress(self, message: str, completed: int, total: int) -> None:
        if self.cancel_requested():
            raise GenerationCancelled("Generation cancelled by user.")
        event = GenerationProgress(message, completed, total)
        self._latest = event
        self._events.put(event)

    def cancel(self) -> None:
        """Request cancellation; the worker stops at its next safe checkpoint."""
        self._cancel_event.set()
        self._latest = GenerationProgress("Cancellation requested...", 0, 1)

    def cancel_requested(self) -> bool:
        return self._cancel_event.is_set()

    @property
    def done(self) -> bool:
        return self._future.done()

    @property
    def latest_progress(self) -> GenerationProgress:
        cancelled = self.cancel_requested()
        try:
            while True:
                self._latest = self._events.get_nowait()
        except Empty:
            if cancelled:
                return GenerationProgress("Cancellation requested...", 0, 1)
            return self._latest

    def result(self) -> Any:
        return self._future.result()
