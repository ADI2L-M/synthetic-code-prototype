import ast


def _tree(source: str):
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def detect_non_descriptive_naming(source: str) -> bool:
    tree = _tree(source)
    if not tree:
        return False
    return any(isinstance(node, ast.Name) and node.id in {"x", "y", "z", "i", "j", "tmp", "foo", "bar", "a", "b"} for node in ast.walk(tree))


def detect_unused_variable(source: str) -> bool:
    tree = _tree(source)
    if not tree:
        return False
    assigned = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
    referenced = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    return bool(assigned - referenced)


def detect_redundant_boolean(source: str) -> bool:
    tree = _tree(source)
    return bool(tree and any(isinstance(node, ast.Compare) and any(isinstance(value, ast.Constant) and isinstance(value.value, bool) for value in node.comparators) for node in ast.walk(tree)))


def detect_excessive_nesting(source: str, threshold: int = 2) -> bool:
    tree = _tree(source)
    if not tree:
        return False
    control = (ast.If, ast.For, ast.While, ast.Try, ast.With)
    def depth(node, current=0):
        next_depth = current + 1 if isinstance(node, control) else current
        return max([next_depth] + [depth(child, next_depth) for child in ast.iter_child_nodes(node)])
    return depth(tree) > threshold


DETECTORS = {
    "non_descriptive_naming": detect_non_descriptive_naming,
    "unused_variable": detect_unused_variable,
    "redundant_boolean_comparison": detect_redundant_boolean,
    "excessive_nesting": detect_excessive_nesting,
}


def detect_defects(source: str, defect_ids: list[str]) -> dict[str, bool]:
    return {defect_id: DETECTORS[defect_id](source) for defect_id in defect_ids}
