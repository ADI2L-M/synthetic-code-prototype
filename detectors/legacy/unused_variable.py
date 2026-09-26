import ast

from detectors.core.parsing import parse_source


def detect_unused_variable(source: str) -> bool:
    tree = parse_source(source)
    if tree is None:
        return False
    assigned = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    referenced = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return bool(assigned - referenced)
