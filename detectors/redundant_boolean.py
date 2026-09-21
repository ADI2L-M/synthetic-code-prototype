import ast

from detectors.parsing import parse_source


def detect_redundant_boolean(source: str) -> bool:
    tree = parse_source(source)
    return bool(
        tree
        and any(
            isinstance(node, ast.Compare)
            and any(
                isinstance(value, ast.Constant) and isinstance(value.value, bool)
                for value in node.comparators
            )
            for node in ast.walk(tree)
        )
    )
