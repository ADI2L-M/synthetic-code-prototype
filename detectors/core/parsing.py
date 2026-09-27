import ast


def parse_source(source: str) -> ast.AST | None:
    """Parse source code once per detector and tolerate invalid submissions."""
    try:
        return ast.parse(source)
    except SyntaxError:
        return None
