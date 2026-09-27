"""AST detectors for the conditional-logic defect family."""

from __future__ import annotations

import ast

from models.research import DetectionResult, TaskContext

from detectors.research.common import (
    ast_equal,
    finish,
    is_side_effect_free,
    parse_for_detection,
    source_text,
)


def _direct_boolean_return(body: list[ast.stmt]) -> bool | None:
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return None
    value = body[0].value
    if isinstance(value, ast.Constant) and isinstance(value.value, bool):
        return value.value
    return None


def _line_starts_with(source: str, node: ast.AST, keyword: str) -> bool:
    lines = source.splitlines()
    line_number = getattr(node, "lineno", 0)
    if not 1 <= line_number <= len(lines):
        return False
    return lines[line_number - 1].lstrip().startswith(keyword)


def _if_chain(node: ast.If) -> list[ast.If]:
    chain = [node]
    current = node
    while len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
        current = current.orelse[0]
        chain.append(current)
    return chain


def _comparison_pair(node: ast.expr) -> tuple[ast.expr, ast.cmpop, ast.expr] | None:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1:
        return None
    return node.left, node.ops[0], node.comparators[0]


def _inverse_operator(operator: ast.cmpop) -> type[ast.cmpop] | None:
    inverses: dict[type[ast.cmpop], type[ast.cmpop]] = {
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
        ast.Lt: ast.GtE,
        ast.LtE: ast.Gt,
        ast.Gt: ast.LtE,
        ast.GtE: ast.Lt,
    }
    return inverses.get(type(operator))


def _are_complements(left: ast.expr, right: ast.expr) -> bool:
    left_pair = _comparison_pair(left)
    right_pair = _comparison_pair(right)
    if left_pair is None or right_pair is None:
        return False
    left_value, left_operator, left_bound = left_pair
    right_value, right_operator, right_bound = right_pair
    inverse = _inverse_operator(left_operator)
    return (
        inverse is not None
        and isinstance(right_operator, inverse)
        and ast_equal(left_value, right_value)
        and ast_equal(left_bound, right_bound)
        and is_side_effect_free(left)
        and is_side_effect_free(right)
    )


def detect_redundant_if_else(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "redundant_if_else")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not node.orelse:
            continue
        true_value = _direct_boolean_return(node.body)
        false_value = _direct_boolean_return(node.orelse)
        if true_value is True and false_value is False:
            matches.append(
                (
                    node,
                    {
                        "condition": source_text(node.test),
                        "true_return_line": node.body[0].lineno,
                        "false_return_line": node.orelse[0].lineno,
                        "equivalence": "condition -> True, else -> False",
                    },
                )
            )
    return finish(result, matches)


def detect_redundant_not(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "redundant_not")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.UnaryOp) or not isinstance(node.op, ast.Not):
            continue
        pair = _comparison_pair(node.operand)
        if pair is None:
            continue
        _, operator, _ = pair
        inverse = _inverse_operator(operator)
        if inverse is None:
            continue
        matches.append(
            (
                node,
                {
                    "comparison": source_text(node.operand),
                    "operator": type(operator).__name__,
                    "inverse_operator": inverse.__name__,
                },
            )
        )
    return finish(result, matches)


def detect_duplicate_if(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "duplicate_if")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        chain = _if_chain(node)
        for left, right in zip(chain, chain[1:]):
            if not _line_starts_with(source, right, "elif"):
                continue
            if ast_equal(ast.Module(body=left.body, type_ignores=[]), ast.Module(body=right.body, type_ignores=[])):
                if all(is_side_effect_free(statement) for statement in left.body + right.body):
                    matches.append(
                        (
                            right,
                            {
                                "branch_lines": [left.lineno, right.lineno],
                                "body": ast.dump(
                                    ast.Module(body=left.body, type_ignores=[]),
                                    include_attributes=False,
                                ),
                            },
                        )
                    )
    return finish(result, matches)


def detect_else_if(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "else_if")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or len(node.orelse) != 1:
            continue
        nested = node.orelse[0]
        if isinstance(nested, ast.If) and _line_starts_with(source, nested, "if"):
            matches.append(
                (
                    nested,
                    {
                        "outer_if_line": node.lineno,
                        "nested_if_line": nested.lineno,
                        "suggestion": "replace else: if with elif",
                    },
                )
            )
    return finish(result, matches)


def detect_nested_if(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "nested_if")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or node.orelse or len(node.body) != 1:
            continue
        nested = node.body[0]
        if not isinstance(nested, ast.If) or nested.orelse:
            continue
        if not is_side_effect_free(node.test) or not is_side_effect_free(nested.test):
            continue
        matches.append(
            (
                nested,
                {
                    "outer_if_line": node.lineno,
                    "inner_if_line": nested.lineno,
                    "combined_condition": f"({source_text(node.test)}) and ({source_text(nested.test)})",
                    "safety": "single body, no else branches, side-effect-free conditions",
                },
            )
        )
    return finish(result, matches)


def detect_redundant_elif(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "redundant_elif")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        chain = _if_chain(node)
        for previous, current in zip(chain, chain[1:]):
            if _line_starts_with(source, current, "elif") and _are_complements(
                previous.test, current.test
            ):
                matches.append(
                    (
                        current,
                        {
                            "preceding_condition": source_text(previous.test),
                            "elif_condition": source_text(current.test),
                            "proof": "direct inverse comparison",
                        },
                    )
                )
    return finish(result, matches)


def _only_pass(statements: list[ast.stmt]) -> bool:
    return len(statements) == 1 and isinstance(statements[0], ast.Pass)


def detect_empty_if(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "empty_if")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not node.orelse:
            continue
        if _only_pass(node.body) and not _only_pass(node.orelse):
            matches.append(
                (
                    node.body[0],
                    {"branch": "if", "if_line": node.lineno, "alternative_line": node.orelse[0].lineno},
                )
            )
        elif _only_pass(node.orelse) and not _only_pass(node.body):
            matches.append(
                (
                    node.orelse[0],
                    {"branch": "else", "if_line": node.lineno, "alternative_line": node.body[0].lineno},
                )
            )
    return finish(result, matches)
