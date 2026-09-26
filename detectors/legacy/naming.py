import ast

from detectors.core.parsing import parse_source

NON_DESCRIPTIVE_NAMES = {"x", "y", "z", "i", "j", "tmp", "foo", "bar", "a", "b"}


def detect_non_descriptive_naming(source: str) -> bool:
    tree = parse_source(source)
    if tree is None:
        return False
    return any(
        isinstance(node, ast.Name) and node.id in NON_DESCRIPTIVE_NAMES
        for node in ast.walk(tree)
    )
