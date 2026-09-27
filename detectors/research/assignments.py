"""AST detector for self-referential assignments replaceable by ``+=``-style updates."""

from __future__ import annotations

import ast

from models.research import DetectionResult, TaskContext

from detectors.research.common import finish, parse_for_detection, source_text


_AUGMENTABLE_OPERATORS: tuple[type[ast.operator], ...] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)


def detect_augmentable_assignment(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "augmentable_assignment")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if not isinstance(node.value, ast.BinOp) or not isinstance(
            node.value.op, _AUGMENTABLE_OPERATORS
        ):
            continue
        if not isinstance(node.value.left, ast.Name) or target.id != node.value.left.id:
            continue
        occurrences = [
            child
            for child in ast.walk(node.value)
            if isinstance(child, ast.Name) and child.id == target.id
        ]
        if len(occurrences) != 1:
            continue
        matches.append(
            (
                node,
                {
                    "target": target.id,
                    "operator": type(node.value.op).__name__,
                    "matching_operand": source_text(node.value.left),
                    "rewrite": f"{target.id} {type(node.value.op).__name__}= ...",
                    "equivalence": "simple-name target with one left operand match",
                },
            )
        )
    return finish(result, matches)
