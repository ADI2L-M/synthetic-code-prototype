"""AST detectors for collection-processing defects."""

from __future__ import annotations

import ast
from collections import defaultdict

from models.research import DetectionResult, TaskContext

from detectors.research.common import (
    ast_equal,
    finish,
    is_side_effect_free,
    parse_for_detection,
    source_text,
)


def _range_len_argument(node: ast.expr) -> ast.expr | None:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if node.func.id != "range" or len(node.args) != 1:
        return None
    argument = node.args[0]
    if (
        isinstance(argument, ast.Call)
        and isinstance(argument.func, ast.Name)
        and argument.func.id == "len"
        and len(argument.args) == 1
    ):
        return argument.args[0]
    return None


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _inside_nested_scope(node: ast.AST, parents: dict[ast.AST, ast.AST], root: ast.For) -> bool:
    current = parents.get(node)
    while current is not None and current is not root:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return True
        current = parents.get(current)
    return False


def detect_redundant_indexing(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "redundant_indexing")
    if tree is None:
        return result
    parents = _parent_map(tree)
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        sequence = _range_len_argument(node.iter)
        if sequence is None:
            continue
        index_name = node.target.id
        valid_reads = 0
        invalid_use = False
        for statement in node.body:
            candidates = ast.walk(statement)
            for candidate in candidates:
                if not isinstance(candidate, ast.Name) or candidate.id != index_name:
                    continue
                if _inside_nested_scope(candidate, parents, node):
                    invalid_use = True
                    break
                if not isinstance(candidate.ctx, ast.Load):
                    invalid_use = True
                    break
                parent = parents.get(candidate)
                matching_read = (
                    isinstance(parent, ast.Subscript)
                    and isinstance(parent.slice, ast.Name)
                    and parent.slice is candidate
                    and ast_equal(parent.value, sequence)
                    and isinstance(parent.ctx, ast.Load)
                )
                if not matching_read:
                    invalid_use = True
                    break
                valid_reads += 1
            if invalid_use:
                break
        if invalid_use or valid_reads == 0:
            continue
        if any(
            isinstance(child, ast.Subscript)
            and ast_equal(child.value, sequence)
            and isinstance(child.ctx, (ast.Store, ast.Del))
            for child in ast.walk(node)
        ):
            continue
        matches.append(
            (
                node,
                {
                    "index_name": index_name,
                    "sequence": source_text(sequence),
                    "matching_reads": valid_reads,
                    "reason": "index is only used to read the current element",
                },
            )
        )
    return finish(result, matches)


def detect_misleading_iterator_name(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "misleading_iterator_name")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    index_style_names = {"i", "j", "k"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id not in index_style_names:
            continue
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range":
                continue
        matches.append(
            (
                node.target,
                {
                    "iterator_name": node.target.id,
                    "iterable": source_text(node.iter),
                    "role": "direct collection element",
                },
            )
        )
    return finish(result, matches)


def _candidate_expression(node: ast.AST) -> bool:
    if isinstance(node, (ast.Constant, ast.Name)):
        return False
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id in {"len", "abs"}
    return isinstance(node, (ast.BinOp, ast.BoolOp, ast.Compare, ast.Subscript, ast.UnaryOp))


def _expression_is_pure(node: ast.AST) -> bool:
    if not is_side_effect_free(node):
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if not isinstance(child.func, ast.Name) or child.func.id not in {"len", "abs"}:
                return False
    return True


def _weighted_complexity(node: ast.AST) -> int:
    score = 0
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            score += 2
        elif isinstance(child, ast.Constant):
            score += 1
        elif isinstance(child, ast.Subscript):
            score += 4
        elif isinstance(child, (ast.BinOp, ast.BoolOp, ast.Compare, ast.UnaryOp)):
            score += 2
        elif isinstance(child, ast.Call):
            score += 2
        elif not isinstance(child, (ast.Load, ast.Store, ast.Del, ast.operator, ast.boolop, ast.cmpop)):
            score += 1
    return score


def _region_for(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.For, ast.While)):
            return current
        current = parents.get(current)
    return node


def detect_duplicate_expression(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "duplicate_expression")
    if tree is None:
        return result
    parents = _parent_map(tree)
    groups: dict[tuple[int, str], list[ast.expr]] = defaultdict(list)
    for node in ast.walk(tree):
        if not isinstance(node, ast.expr) or not _candidate_expression(node):
            continue
        if not _expression_is_pure(node) or _weighted_complexity(node) < 8:
            continue
        region = _region_for(node, parents)
        groups[(id(region), ast.dump(node, include_attributes=False))].append(node)

    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for expressions in groups.values():
        if len(expressions) < 2:
            continue
        line_numbers = [getattr(expression, "lineno", 0) for expression in expressions]
        if max(line_numbers) - min(line_numbers) > 20:
            continue
        first = expressions[0]
        matches.append(
            (
                first,
                {
                    "occurrence_lines": line_numbers,
                    "expression": source_text(first),
                    "weighted_complexity": _weighted_complexity(first),
                    "purity": "allowlisted pure expression",
                },
            )
        )
    return finish(result, matches)
