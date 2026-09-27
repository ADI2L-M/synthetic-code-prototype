"""Shared helpers for the definition-driven research detectors."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from typing import Any

from models.research import DetectionLocation, DetectionResult, TaskContext


def parse_for_detection(source: str, defect: str) -> tuple[ast.AST | None, DetectionResult]:
    """Parse source and return a result that safely records parse failures."""
    result = DetectionResult(defect=defect)
    try:
        return ast.parse(source), result
    except (SyntaxError, ValueError, TypeError, UnicodeError) as error:
        result.notes = f"Unable to parse source: {error}"
        return None, result


def location(node: ast.AST) -> DetectionLocation:
    return DetectionLocation(
        line=getattr(node, "lineno", 0),
        column=getattr(node, "col_offset", 0),
    )


def finish(
    result: DetectionResult,
    matches: Iterable[tuple[ast.AST, dict[str, Any]]],
) -> DetectionResult:
    """Populate the common result fields from detector matches."""
    for node, evidence in matches:
        result.locations.append(location(node))
        result.evidence.append(evidence)
    result.count = len(result.locations)
    result.present = result.count > 0
    return result


def ast_equal(left: ast.AST, right: ast.AST) -> bool:
    return ast.dump(left, include_attributes=False) == ast.dump(
        right, include_attributes=False
    )


def source_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except (AttributeError, TypeError):
        return ast.dump(node, include_attributes=False)


def is_side_effect_free(node: ast.AST) -> bool:
    """Conservative expression purity used by rewrite-style detectors."""
    for child in ast.walk(node):
        if isinstance(child, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom)):
            return False
        if isinstance(child, ast.Attribute):
            return False
        if isinstance(child, ast.NamedExpr):
            return False
    return True


def task_allows(context: TaskContext | None, name: str) -> bool:
    """Return whether a task context explicitly requires a binding name."""
    return context is not None and name in context.required_names


def numeric_literal(node: ast.AST) -> int | float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = numeric_literal(node.operand)
        if value is not None:
            return -value if isinstance(node.op, ast.USub) else value
    return None


def bound_names(node: ast.AST) -> set[str]:
    """Collect simple names bound by an AST node."""
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
            names.add(child.id)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
    return names


def context_for_task(task_id: str, task_family: str, required_names: tuple[str, ...] = ()) -> TaskContext:
    return TaskContext(
        task_id=task_id,
        task_family=task_family,
        required_names=required_names,
    )
