"""AST detectors for numeric-iteration defects."""

from __future__ import annotations

import ast

from models.research import DetectionResult, TaskContext

from detectors.research.common import finish, numeric_literal, parse_for_detection, source_text


def _numeric_update(statement: ast.stmt, variable: str) -> tuple[int | float, str] | None:
    if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
        if statement.target.id != variable or not isinstance(statement.op, (ast.Add, ast.Sub)):
            return None
        value = numeric_literal(statement.value)
        if value is None:
            return None
        return (value if isinstance(statement.op, ast.Add) else -value, "augmented")
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        return None
    target = statement.targets[0]
    if not isinstance(target, ast.Name) or target.id != variable:
        return None
    if not isinstance(statement.value, ast.BinOp) or not isinstance(statement.value.left, ast.Name):
        return None
    if statement.value.left.id != variable or not isinstance(statement.value.op, (ast.Add, ast.Sub)):
        return None
    value = numeric_literal(statement.value.right)
    if value is None:
        return None
    return (value if isinstance(statement.value.op, ast.Add) else -value, "ordinary")


def _contains_unsafe_control(body: list[ast.stmt]) -> bool:
    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                break
            if isinstance(node, (ast.Break, ast.Return, ast.Continue)):
                return True
    return False


def _updates_on_all_paths(body: list[ast.stmt], variable: str) -> tuple[bool, tuple[int | float, str] | None]:
    for statement in body:
        update = _numeric_update(statement, variable)
        if update is not None:
            return True, update
        if isinstance(statement, ast.If):
            if statement.orelse:
                left_ok, left_update = _updates_on_all_paths(statement.body, variable)
                right_ok, right_update = _updates_on_all_paths(statement.orelse, variable)
                if left_ok and right_ok and left_update == right_update:
                    return True, left_update
                return False, None
            return False, None
        if isinstance(statement, (ast.For, ast.While, ast.Try, ast.Match)):
            return False, None
    return False, None


def _while_control(node: ast.While) -> tuple[str, ast.cmpop, ast.expr] | None:
    if not isinstance(node.test, ast.Compare) or len(node.test.ops) != 1:
        return None
    if isinstance(node.test.left, ast.Name):
        return node.test.left.id, node.test.ops[0], node.test.comparators[0]
    return None


def _test_assignments(body: list[ast.stmt]) -> set[str]:
    assigned: set[str] = set()
    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                assigned.add(node.id)
    return assigned


def detect_while_as_for(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "while_as_for")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        control = _while_control(node)
        if control is None:
            continue
        variable, operator, bound = control
        if not isinstance(operator, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
            continue
        if _contains_unsafe_control(node.body):
            continue
        updated, update = _updates_on_all_paths(node.body, variable)
        if not updated or update is None or update[0] == 0:
            continue
        assigned = _test_assignments(node.body)
        bound_names = {
            child.id
            for child in ast.walk(bound)
            if isinstance(child, ast.Name)
        }
        if (assigned - {variable}) & bound_names:
            continue
        step = update[0]
        if isinstance(operator, (ast.Lt, ast.LtE)) and step <= 0:
            continue
        if isinstance(operator, (ast.Gt, ast.GtE)) and step >= 0:
            continue
        matches.append(
            (
                node,
                {
                    "control_variable": variable,
                    "test": source_text(node.test),
                    "bound": source_text(bound),
                    "constant_step": step,
                    "update_form": update[1],
                    "path_safety": "constant update occurs on every executable path",
                },
            )
        )
    return finish(result, matches)


def _static_int(node: ast.expr) -> int | None:
    value = numeric_literal(node)
    if value is not None and int(value) == value:
        return int(value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
        left = _static_int(node.left)
        right = _static_int(node.right)
        if left is not None and right is not None:
            return {
                ast.Add: left + right,
                ast.Sub: left - right,
                ast.Mult: left * right,
            }[type(node.op)]
    return None


def _static_range_length(call: ast.Call) -> int | None:
    if not isinstance(call.func, ast.Name) or call.func.id != "range":
        return None
    values = [_static_int(argument) for argument in call.args]
    if any(value is None for value in values) or not 1 <= len(values) <= 3:
        return None
    try:
        if len(values) == 1:
            return len(range(values[0]))
        if len(values) == 2:
            return len(range(values[0], values[1]))
        return len(range(values[0], values[1], values[2]))
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def _static_cardinality(node: ast.expr) -> int | None:
    if isinstance(node, ast.Call):
        return _static_range_length(node)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        if all(not any(isinstance(child, ast.Call) for child in ast.walk(element)) for element in node.elts):
            return len(node.elts)
    return None


def detect_redundant_for(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    tree, result = parse_for_detection(source, "redundant_for")
    if tree is None:
        return result
    matches: list[tuple[ast.AST, dict[str, object]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        cardinality = _static_cardinality(node.iter)
        if cardinality is None or cardinality > 1:
            continue
        matches.append(
            (
                node,
                {
                    "iterable": source_text(node.iter),
                    "static_cardinality": cardinality,
                    "proof": "statically evaluable iterable",
                },
            )
        )
    return finish(result, matches)
