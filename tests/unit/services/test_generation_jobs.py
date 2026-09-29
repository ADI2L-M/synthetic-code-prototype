from threading import Event
from time import sleep

import pytest

from services.generation.jobs import GenerationCancelled, GenerationJob


def test_generation_job_reports_progress_and_returns_worker_result():
    def worker(progress, cancel_check):
        assert not cancel_check()
        progress("Generating submission 1 of 1", 0, 1)
        progress("Completed submission 1 of 1", 1, 1)
        return "finished"

    job = GenerationJob(worker)

    while not job.done:
        sleep(0.001)

    assert job.result() == "finished"
    assert job.latest_progress.message == "Completed submission 1 of 1"


def test_generation_job_cancel_stops_worker_at_checkpoint():
    started = Event()

    def worker(progress, cancel_check):
        started.set()
        while not cancel_check():
            sleep(0.001)
        raise GenerationCancelled("Generation cancelled by user.")

    job = GenerationJob(worker)
    assert started.wait(timeout=1)
    job.cancel()

    while not job.done:
        sleep(0.001)

    with pytest.raises(GenerationCancelled, match="cancelled"):
        job.result()
    assert job.latest_progress.message == "Cancellation requested..."
