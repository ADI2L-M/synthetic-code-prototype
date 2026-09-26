import ast
from collections.abc import Iterable

from models.research import DetectionLocation, DetectionResult, TaskContext


_BOOLEAN_COMPARISON_OPERATORS = (
    ast.Eq,
    ast.NotEq,
)


class _BooleanExpressionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.boolean_names: set[str] = set()
        self.matches: list[tuple[ast.Compare, ast.expr, str]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        is_boolean = _is_boolean_expression(node.value, self.boolean_names)
        for target in _assigned_names(node.targets):
            if is_boolean:
                self.boolean_names.add(target)
            else:
                self.boolean_names.discard(target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
            is_boolean = _is_boolean_expression(node.value, self.boolean_names)
            if isinstance(node.target, ast.Name):
                if is_boolean:
                    self.boolean_names.add(node.target.id)
                else:
                    self.boolean_names.discard(node.target.id)

    def visit_Compare(self, node: ast.Compare) -> None:
        if len(node.ops) == 1 and isinstance(node.ops[0], _BOOLEAN_COMPARISON_OPERATORS):
            operands = (node.left, node.comparators[0])
            for operand in operands:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, bool):
                    other = operands[1] if operand is operands[0] else operands[0]
                    if _is_boolean_expression(other, self.boolean_names):
                        self.matches.append((node, other, type(node.ops[0]).__name__))
                        break
        self.generic_visit(node)


def _assigned_names(targets: Iterable[ast.expr]) -> Iterable[str]:
    for target in targets:
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, (ast.Tuple, ast.List)):
            yield from _assigned_names(target.elts)


def _is_boolean_expression(expression: ast.expr, boolean_names: set[str]) -> bool:
    if isinstance(expression, ast.Constant):
        return isinstance(expression.value, bool)
    if isinstance(expression, ast.Name):
        return expression.id in boolean_names
    if isinstance(expression, ast.Compare):
        return True
    if isinstance(expression, ast.UnaryOp):
        return isinstance(expression.op, ast.Not)
    if isinstance(expression, ast.Call):
        return isinstance(expression.func, ast.Name) and expression.func.id == "bool"
    return False


def detect_redundant_comparison_result(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    result = DetectionResult(defect="redundant_comparison")
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as error:
        result.notes = f"Unable to parse source: {error}"
        return result

    visitor = _BooleanExpressionVisitor()
    visitor.visit(tree)
    result.count = len(visitor.matches)
    result.present = result.count > 0
    for node, operand, operator in visitor.matches:
        result.locations.append(DetectionLocation(node.lineno, node.col_offset))
        result.evidence.append(
            {
                "operator": operator,
                "boolean_operand": ast.unparse(operand),
                "boolean_proof": "syntactic_or_local_data_flow",
            }
        )
    return result
