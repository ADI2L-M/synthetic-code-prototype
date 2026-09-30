"""Run reproducible prompting-condition comparisons and persist summaries."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from statistics import mean
from typing import Any

from models.types import IterationResult
from services.generation.analytics import generation_quality
from services.generation.calibrator import (
    calibration_constraints,
    calibration_is_non_regressive,
)
from services.generation.prototype_tasks import load_prototype_task
from services.generation.workflow import (
    BASELINE_CONDITION,
    GENERATION_CONDITIONS,
    ITERATIVE_CONDITION,
    TASK_AWARE_CONDITION,
    run_iteration,
)
from services.providers.llm import GenerationProvider
from services.providers.ollama import ollama_runtime_provenance

EXPERIMENT_LOG_DIRECTORY = (
    Path(__file__).resolve().parents[2]
    / "research-notes"
    / "synthetic-generation-experiments"
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def experiment_log_path(now: datetime | None = None) -> Path:
    """Return a timestamped JSONL path using local time."""
    timestamp = (now or datetime.now().astimezone()).strftime("%d%m%y%H%M%S")
    return EXPERIMENT_LOG_DIRECTORY / f"experiment-log-{timestamp}.jsonl"


DEFAULT_EXPERIMENT_LOG = experiment_log_path()

ProviderFactory = Callable[[], GenerationProvider]


def runtime_provenance(
    model: str | None = None,
    base_url: str | None = None,
) -> dict[str, object]:
    """Return local runtime and repository provenance for an experiment log."""
    provenance: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": None,
        "git_dirty": None,
    }
    if model:
        provenance["ollama"] = ollama_runtime_provenance(
            model,
            base_url or "http://localhost:11434",
        )
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return provenance
    provenance["git_commit"] = commit.stdout.strip() or None
    provenance["git_dirty"] = bool(dirty.stdout.strip())
    return provenance


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration shared by every prompting condition in an experiment."""

    experiment_id: str
    task_id: str
    target_profile: dict[str, float]
    batch_size: int = 50
    tolerance: float = 0.10
    model: str | None = None
    base_url: str | None = None
    context_length: int | None = None
    temperature: float | None = None
    repetitions: int = 1
    max_iterations: int = 3
    max_repair_attempts: int = 2
    conditions: tuple[str, ...] = (
        BASELINE_CONDITION,
        TASK_AWARE_CONDITION,
        ITERATIVE_CONDITION,
    )
    target_standard_errors: dict[str, float] = field(default_factory=dict)


@dataclass
class ExperimentRun:
    """All in-memory iterations for one condition/repetition pair."""

    run_id: str
    condition: str
    repetition: int
    iterations: list[IterationResult]
    selected_iteration_index: int
    stop_reason: str

    @property
    def final_iteration(self) -> IterationResult:
        return self.iterations[self.selected_iteration_index]


@dataclass
class ExperimentResult:
    """Comparison output for one complete experiment."""

    experiment_id: str
    created_at_utc: str
    config: ExperimentConfig
    runs: list[ExperimentRun]
    condition_summary: dict[str, dict[str, float]]


def _iteration_metrics(iteration: IterationResult) -> dict[str, float | int | None]:
    quality = generation_quality(iteration)
    errors = [abs(row.difference) for row in iteration.comparison]
    squared_errors = [row**2 for row in errors]
    within_tolerance = sum(
        row.status == "Within tolerance" for row in iteration.comparison
    )
    return {
        "functional_pass_rate": float(quality["functional_pass_rate"]),
        "independent_coverage": float(quality["independent_coverage"]),
        "dependent_coverage": float(quality["dependent_coverage"]),
        "category_requirement_rate": (
            float(quality["category_requirement_rate"])
            if iteration.condition != BASELINE_CONDITION
            else None
        ),
        "mean_absolute_profile_error": mean(errors) if errors else 0.0,
        "root_mean_square_profile_error": sqrt(mean(squared_errors))
        if squared_errors
        else 0.0,
        "within_tolerance_rate": (
            within_tolerance / len(iteration.comparison)
            if iteration.comparison
            else 1.0
        ),
        "valid_submissions": int(quality["valid_submissions"]),
        "total_submissions": int(quality["total_submissions"]),
    }


def _run_record(run: ExperimentRun) -> dict[str, Any]:
    def comparison_records(iteration: IterationResult) -> list[dict[str, Any]]:
        return [
            {
                "defect": row.defect,
                "target": row.target,
                "observed": row.observed,
                "difference": row.difference,
                "allowed_difference": row.allowed_difference,
                "observed_count": row.observed_count,
                "observed_denominator": row.observed_denominator,
                "status": row.status,
                "action": row.action,
            }
            for row in iteration.comparison
        ]

    return {
        "run_id": run.run_id,
        "condition": run.condition,
        "repetition": run.repetition,
        "selected_iteration": run.final_iteration.iteration,
        "iteration_count": len(run.iterations),
        "stop_reason": run.stop_reason,
        "selected_out_of_tolerance": [
            row.defect
            for row in run.final_iteration.comparison
            if row.status != "Within tolerance"
        ],
        "selected_zero_observed": [
            row.defect
            for row in run.final_iteration.comparison
            if row.target > 0 and row.observed_count == 0
        ],
        "iterations": [
            {
                "iteration": iteration.iteration,
                "constraints": iteration.constraints,
                "metrics": _iteration_metrics(iteration),
                "profile_comparison": comparison_records(iteration),
                "out_of_tolerance": [
                    row.defect
                    for row in iteration.comparison
                    if row.status != "Within tolerance"
                ],
                "zero_observed": [
                    row.defect
                    for row in iteration.comparison
                    if row.target > 0 and row.observed_count == 0
                ],
                "accepted": iteration.accepted,
            }
            for iteration in run.iterations
        ],
    }


def _condition_summary(runs: list[ExperimentRun]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, float | int | None]]] = {}
    for run in runs:
        grouped.setdefault(run.condition, []).append(
            _iteration_metrics(run.final_iteration)
        )
    summary: dict[str, dict[str, float]] = {}
    for condition, metrics_rows in grouped.items():
        metrics: dict[str, float] = {}
        keys = {
            key
            for row in metrics_rows
            for key, value in row.items()
            if isinstance(value, (float, int))
        }
        for key in sorted(keys):
            values = [
                float(row[key])
                for row in metrics_rows
                if isinstance(row.get(key), (float, int))
            ]
            if values:
                metrics[key] = mean(values)
        summary[condition] = metrics
    return summary


def _profile_selection_key(iteration: IterationResult) -> tuple[float, ...]:
    """Rank eligible iterations by profile alignment and quality coverage."""
    errors = [abs(row.difference) for row in iteration.comparison]
    mean_absolute_error = mean(errors) if errors else 0.0
    within_tolerance = (
        sum(row.status == "Within tolerance" for row in iteration.comparison)
        / len(iteration.comparison)
        if iteration.comparison
        else 1.0
    )
    quality = generation_quality(iteration)
    return (
        -mean_absolute_error,
        within_tolerance,
        float(quality["category_requirement_rate"]),
        float(quality["dependent_coverage"]),
        float(quality["independent_coverage"]),
        float(quality["functional_pass_rate"]),
    )


def append_experiment_log(
    result: ExperimentResult,
    path: Path | None = None,
) -> None:
    """Append a compact experiment summary without storing source code."""
    path = path or DEFAULT_EXPERIMENT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "record_type": "synthetic_generation_experiment",
        "schema_version": 3,
        "experiment_id": result.experiment_id,
        "created_at_utc": result.created_at_utc,
        "provenance": runtime_provenance(
            result.config.model,
            result.config.base_url,
        ),
        "config": {
            "task_id": result.config.task_id,
            "batch_size": result.config.batch_size,
            "tolerance": result.config.tolerance,
            "model": result.config.model,
            "base_url": result.config.base_url,
            "context_length": result.config.context_length,
            "temperature": result.config.temperature,
            "repetitions": result.config.repetitions,
            "max_iterations": result.config.max_iterations,
            "max_repair_attempts": result.config.max_repair_attempts,
            "conditions": list(result.config.conditions),
            "target_profile": result.config.target_profile,
            "target_standard_errors": result.config.target_standard_errors,
        },
        "condition_summary": result.condition_summary,
        "runs": [_run_record(run) for run in result.runs],
    }
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_experiment_logs(
    directory: Path | None = None,
) -> list[dict[str, Any]]:
    """Load valid experiment records for the Streamlit history browser."""
    directory = directory or EXPERIMENT_LOG_DIRECTORY
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("experiment-log*.jsonl")):
        with path.open(encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("record_type") != "synthetic_generation_experiment":
                    continue
                records.append(
                    {
                        **record,
                        "_log_file": path.name,
                        "_line_number": line_number,
                    }
                )
    return records


def run_experiment(
    config: ExperimentConfig,
    provider_factory: ProviderFactory,
    log_path: Path | None = DEFAULT_EXPERIMENT_LOG,
) -> ExperimentResult:
    """Run baseline, task-aware, and/or iterative conditions automatically."""
    if config.batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if config.repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    if config.max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if config.max_repair_attempts < 0:
        raise ValueError("max_repair_attempts cannot be negative")
    if config.temperature is not None and config.temperature < 0:
        raise ValueError("temperature cannot be negative")
    unknown = set(config.conditions).difference(GENERATION_CONDITIONS)
    if unknown:
        raise ValueError(f"Unknown experiment conditions: {sorted(unknown)}")

    runs: list[ExperimentRun] = []
    for condition in config.conditions:
        iteration_limit = (
            config.max_iterations if condition == ITERATIVE_CONDITION else 1
        )
        for repetition in range(1, config.repetitions + 1):
            run_id = f"{config.experiment_id}:{condition}:{repetition}"
            # Match the initial random draw across task-aware conditions so
            # iterative calibration is compared with non-adaptive prompting
            # from the same starting batch.
            seed_namespace = f"{config.experiment_id}:repetition:{repetition}"
            constraints: dict[str, str] = {}
            iterations: list[IterationResult] = []
            selected_iteration_index = 0
            stop_reason = "single_iteration"
            initial_iteration: IterationResult | None = None
            best_selection_key: tuple[float, ...] | None = None

            for iteration_number in range(1, iteration_limit + 1):
                iteration = run_iteration(
                    task=load_prototype_task(config.task_id),
                    target_profile=config.target_profile,
                    batch_size=config.batch_size,
                    iteration_number=iteration_number,
                    tolerance=config.tolerance,
                    constraints=constraints,
                    provider=provider_factory(),
                    model=config.model,
                    context_length=config.context_length,
                    temperature=config.temperature,
                    max_repair_attempts=config.max_repair_attempts,
                    target_standard_errors=config.target_standard_errors,
                    condition=condition,
                    seed_namespace=seed_namespace,
                )
                iterations.append(iteration)

                if condition != ITERATIVE_CONDITION:
                    stop_reason = "single_iteration"
                    break

                if initial_iteration is None:
                    initial_iteration = iteration
                    selected_iteration_index = 0
                    best_selection_key = _profile_selection_key(iteration)
                    if iteration.accepted:
                        stop_reason = "within_tolerance"
                        break
                elif iteration.accepted:
                    # A batch that reaches the prevalence objective is
                    # accepted immediately; no further calibration is needed.
                    selected_iteration_index = len(iterations) - 1
                    stop_reason = "within_tolerance"
                    break
                elif calibration_is_non_regressive(initial_iteration, iteration):
                    candidate_key = _profile_selection_key(iteration)
                    if best_selection_key is None or candidate_key > best_selection_key:
                        selected_iteration_index = len(iterations) - 1
                        best_selection_key = candidate_key

                # Calibrate the next iteration from the latest observed batch,
                # even when its profile is worse than the previous batch.
                constraints = calibration_constraints(iteration.comparison)

            if (
                condition == ITERATIVE_CONDITION
                and stop_reason != "within_tolerance"
            ):
                stop_reason = "maximum_iterations"

            runs.append(
                ExperimentRun(
                    run_id=run_id,
                    condition=condition,
                    repetition=repetition,
                    iterations=iterations,
                    selected_iteration_index=selected_iteration_index,
                    stop_reason=stop_reason,
                )
            )

    result = ExperimentResult(
        experiment_id=config.experiment_id,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        config=config,
        runs=runs,
        condition_summary=_condition_summary(runs),
    )
    if log_path is not None:
        append_experiment_log(result, log_path)
    return result


__all__ = [
    "BASELINE_CONDITION",
    "DEFAULT_EXPERIMENT_LOG",
    "EXPERIMENT_LOG_DIRECTORY",
    "ITERATIVE_CONDITION",
    "TASK_AWARE_CONDITION",
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentRun",
    "append_experiment_log",
    "experiment_log_path",
    "load_experiment_logs",
    "run_experiment",
    "runtime_provenance",
]
