"""AST detectors for identifier naming defects."""

from __future__ import annotations

import ast
import builtins

from models.research import DetectionResult, TaskContext

from detectors.research.common import finish, parse_for_detection, task_allows


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _load_uses(tree: ast.AST, name: str) -> list[ast.Name]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == name
        and isinstance(node.ctx, ast.Load)
    ]


def _role_appropriate_one_letter(
    name: str,
    binding: ast.AST,
    tree: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> str | None:
    if name in {"i", "j", "k"}:
        parent = parents.get(binding)
        if isinstance(parent, ast.For) and parent.target is binding:
            if isinstance(parent.iter, ast.Call) and isinstance(parent.iter.func, ast.Name):
                if parent.iter.func.id == "range":
                    return "numeric index or counter"
            return None
        for use in _load_uses(tree, name):
            parent = parents.get(use)
            if isinstance(parent, ast.Subscript) and parent.slice is use:
                return "numeric index or counter"
        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                if node.target.id == name and isinstance(node.op, (ast.Add, ast.Sub)):
                    return "numeric index or counter"
        return None
    if name in {"n", "m"}:
        for use in _load_uses(tree, name):
            parent = parents.get(use)
            if isinstance(parent, ast.Compare):
                return "numeric size, count, or bound"
            if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name):
                if parent.func.id == "range":
                    return "numeric size, count, or bound"
        return None
    if name in {"x", "y", "z"}:
        for use in _load_uses(tree, name):
            parent = parents.get(use)
            if isinstance(parent, (ast.BinOp, ast.UnaryOp, ast.Compare)):
                return "mathematical or coordinate variable"
        return None
    return None


def detect_one_letter_name(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    tree, result = parse_for_detection(source, "one_letter_name")
    if tree is None:
        return result
    parents = _parents(tree)
    bindings: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            bindings.append((node.arg, node))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bindings.append((node.id, node))
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    seen: set[tuple[str, int, int]] = set()
    for name, node in bindings:
        if len(name) != 1 or name == "_":
            continue
        key = (name, getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if key in seen:
            continue
        seen.add(key)
        if task_allows(context, name):
            continue
        role = _role_appropriate_one_letter(name, node, tree, parents)
        if role is not None:
            continue
        matches.append(
            (
                node,
                {
                    "identifier": name,
                    "role": "unclear or non-descriptive",
                    "exemption": "none",
                },
            )
        )
    return finish(result, matches)


def _binding_candidates(tree: ast.AST) -> list[tuple[str, ast.AST]]:
    bindings: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            bindings.append((node.arg, node))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bindings.append((node.id, node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bindings.append((node.name, node))
        elif isinstance(node, ast.alias):
            bindings.append((node.asname or node.name.split(".")[0], node))
    return bindings


def detect_built_in_name(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "built_in_name")
    if tree is None:
        return result
    builtin_names = set(dir(builtins))
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    seen: set[tuple[str, int, int]] = set()
    for name, node in _binding_candidates(tree):
        key = (name, getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if name not in builtin_names or key in seen:
            continue
        seen.add(key)
        matches.append(
            (
                node,
                {
                    "identifier": name,
                    "shadowed_builtin": name,
                    "binding_kind": type(node).__name__,
                },
            )
        )
    return finish(result, matches)
