"""Authoritative runtime configuration for synthetic generation.

Research-note YAML files document the empirical analysis.  This module keeps
runtime generation configuration in the versioned JSON files under ``config``
so the generator does not silently read a different task contract or prompt
policy from a Python constant.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GENERATION_CONFIGURATION_PATH = ROOT / "config" / "generation_configuration.json"
DEFECT_SPECIFICATION_PATH = ROOT / "config" / "defect_specifications.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_generation_configuration() -> dict[str, Any]:
    """Load the immutable task and generation policy configuration."""
    return _load_json(GENERATION_CONFIGURATION_PATH)


@lru_cache(maxsize=1)
def load_defect_specification() -> dict[str, Any]:
    """Load the detector and empirical eligibility catalogue."""
    return _load_json(DEFECT_SPECIFICATION_PATH)


@lru_cache(maxsize=1)
def load_defect_catalog() -> dict[str, dict[str, Any]]:
    """Return the defect catalogue indexed by its stable name."""
    return {
        item["name"]: item
        for item in load_defect_specification().get("defects", [])
        if "name" in item
    }


def generation_policy(name: str) -> dict[str, Any]:
    """Return one named generation policy mapping."""
    policy = load_generation_configuration().get("generation", {}).get(name, {})
    if not isinstance(policy, dict):
        raise TypeError(f"Generation policy is not a mapping: {name}")
    return policy


def task_configuration(task_id: str) -> dict[str, Any]:
    """Return one configured prototype task or raise a useful error."""
    tasks = load_generation_configuration().get("prototype_tasks", {})
    try:
        task = tasks[task_id]
    except KeyError as error:
        raise ValueError(f"Unknown prototype task: {task_id}") from error
    if not isinstance(task, dict):
        raise TypeError(f"Prototype task is not a mapping: {task_id}")
    return task


def defect_names_by_category(category: str) -> frozenset[str]:
    """Return the catalogue's authoritative defect names for one category."""
    return frozenset(
        name
        for name, item in load_defect_catalog().items()
        if item.get("category") == category
    )


def applicable_defect_names(task_id: str, category: str) -> tuple[str, ...]:
    """Return catalogue defects applicable to a task and category."""
    return tuple(
        name
        for name, item in load_defect_catalog().items()
        if item.get("category") == category
        and task_id in item.get("applicable_tasks", [])
    )
