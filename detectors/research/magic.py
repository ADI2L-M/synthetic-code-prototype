"""Conservative detector for researcher-operationalised magic numbers."""

from __future__ import annotations

import ast

from models.research import DetectionResult, TaskContext

from detectors.research.common import finish, numeric_literal, parse_for_detection, source_text


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _inside_context(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.Compare):
            return "comparison decision"
        if isinstance(current, ast.BinOp):
            return "domain computation"
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Name):
            if current.func.id == "range":
                return None
        if isinstance(current, (ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Subscript)):
            return None
        current = parents.get(current)
    return None


def _minus_one_is_conventional(
    node: ast.UnaryOp, parents: dict[ast.AST, ast.AST]
) -> bool:
    parent = parents.get(node)
    if isinstance(parent, ast.Subscript):
        return True
    if isinstance(parent, ast.Compare):
        for child in ast.walk(parent):
            if isinstance(child, ast.Name) and child.id.lower() in {
                "index",
                "idx",
                "position",
                "pos",
            }:
                return True
    return False


def detect_magic_number(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "magic_number")
    if tree is None:
        return result
    parents = _parent_map(tree)
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Constant, ast.UnaryOp)):
            continue
        value = numeric_literal(node)
        if value is None or value in {0, 1}:
            continue
        if isinstance(node, ast.UnaryOp) and value == -1 and _minus_one_is_conventional(node, parents):
            continue
        if isinstance(node, ast.Constant):
            parent = parents.get(node)
            if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, (ast.USub, ast.UAdd)):
                continue
        context_name = _inside_context(node, parents)
        if context_name is None:
            continue
        matches.append(
            (
                node,
                {
                    "value": value,
                    "context": context_name,
                    "exemption": "none; not 0 or 1 and not a conventional -1",
                    "expression": source_text(node),
                },
            )
        )
    return finish(result, matches)
