"""Run and log a controlled comparison of synthetic-generation conditions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "research-notes" / "authentic-submission-outputs" / "empirical-target-profile.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def _profile_inputs(path: Path, task_id: str) -> tuple[dict[str, float], dict[str, float]]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    try:
        task_profile = profile["prototype_tasks"][task_id]
    except KeyError as error:
        raise ValueError(f"No empirical target profile for {task_id}") from error

    target = {
        str(defect): float(value)
        for defect, value in task_profile["target_profile"].items()
    }
    standard_errors: dict[str, float] = {}
    for category in ("task_independent", "task_dependent"):
        for defect, estimate in task_profile.get(category, {}).items():
            eligible_tasks = int(estimate.get("eligible_tasks", 0))
            standard_deviation = estimate.get("standard_deviation")
            if eligible_tasks > 1 and standard_deviation is not None:
                standard_errors[defect] = float(standard_deviation) / eligible_tasks**0.5
    return target, standard_errors


def main() -> None:
    from services.generation.experiment import (
        ExperimentConfig,
        experiment_log_path,
        run_experiment,
    )
    from services.providers.ollama import (
        OLLAMA_CONTEXT_LENGTH,
        OLLAMA_TEMPERATURE,
        OllamaProvider,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("T1", "T2", "T3"), required=True)
    parser.add_argument("--model", default="qwen2.5-coder:1.5b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--tolerance", type=float, default=0.10)
    parser.add_argument("--temperature", type=float, default=OLLAMA_TEMPERATURE)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--max-repair-attempts", type=int, default=2)
    parser.add_argument("--experiment-id")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=[
            "non_adaptive_baseline",
            "task_aware_non_adaptive",
            "task_aware_iterative",
        ],
    )
    args = parser.parse_args()

    target_profile, standard_errors = _profile_inputs(args.profile, args.task)
    log_path = args.log or experiment_log_path()
    experiment_id = args.experiment_id or datetime.now(timezone.utc).strftime(
        "experiment-%Y%m%dT%H%M%SZ"
    )
    config = ExperimentConfig(
        experiment_id=experiment_id,
        task_id=args.task,
        target_profile=target_profile,
        batch_size=args.batch_size,
        tolerance=args.tolerance,
        model=args.model,
        context_length=OLLAMA_CONTEXT_LENGTH,
        temperature=args.temperature,
        repetitions=args.repetitions,
        max_iterations=args.max_iterations,
        max_repair_attempts=args.max_repair_attempts,
        conditions=tuple(args.conditions),
        target_standard_errors=standard_errors,
    )
    result = run_experiment(
        config,
        provider_factory=lambda: OllamaProvider(
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
        ),
        log_path=log_path,
    )
    print(json.dumps({
        "experiment_id": result.experiment_id,
        "log": str(log_path),
        "condition_summary": result.condition_summary,
    }, indent=2))


if __name__ == "__main__":
    main()
