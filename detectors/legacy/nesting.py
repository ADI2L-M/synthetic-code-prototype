import ast

from detectors.core.parsing import parse_source

CONTROL_NODES = (ast.If, ast.For, ast.While, ast.Try, ast.With)


def _nesting_depth(node: ast.AST, current: int = 0) -> int:
    next_depth = current + 1 if isinstance(node, CONTROL_NODES) else current
    return max(
        [next_depth]
        + [_nesting_depth(child, next_depth) for child in ast.iter_child_nodes(node)]
    )


def detect_excessive_nesting(source: str, threshold: int = 2) -> bool:
    tree = parse_source(source)
    return bool(tree and _nesting_depth(tree) > threshold)
