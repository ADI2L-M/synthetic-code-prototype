"""Token-based detector for the fixed formatting subset in the specification."""

from __future__ import annotations

import ast
import io
import tokenize

from models.research import DetectionLocation, DetectionResult, TaskContext


_DELIMITERS = {"(": ")", "[": "]", "{": "}"}
_SPACING_OPERATORS = {
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "//=",
    "%=",
    "**=",
    "==",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
    "+",
    "-",
    "*",
    "/",
    "//",
    "%",
    "**",
    "and",
    "or",
    "in",
    "is",
}
_UNARY_KEYWORDS = {"return", "yield", "if", "elif", "while", "for", "in", "and", "or", "not"}


def _same_line(left: tokenize.TokenInfo, right: tokenize.TokenInfo) -> bool:
    return left.end[0] == right.start[0]


def _spacing(left: tokenize.TokenInfo, right: tokenize.TokenInfo) -> int:
    if not _same_line(left, right):
        return -1
    return right.start[1] - left.end[1]


def _add(result: DetectionResult, token: tokenize.TokenInfo, rule: str, detail: str) -> None:
    result.locations.append(DetectionLocation(token.start[0], token.start[1]))
    result.evidence.append({"rule": rule, "detail": detail, "token": token.string})


def _is_unary(token_index: int, tokens: list[tokenize.TokenInfo]) -> bool:
    if token_index == 0:
        return True
    previous = tokens[token_index - 1]
    if previous.string in _DELIMITERS or previous.string in {",", ":", "="}:
        return True
    return previous.string in _UNARY_KEYWORDS


def _detect_token_spacing(source: str, result: DetectionResult) -> None:
    try:
        all_tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError) as error:
        result.notes = f"Unable to tokenize source: {error}"
        return
    tokens = [
        token
        for token in all_tokens
        if token.type not in {tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT}
    ]
    for index, token in enumerate(tokens):
        if index > 0:
            previous = tokens[index - 1]
            gap = _spacing(previous, token)
            if token.string in {",", ";", ":"} and gap > 0:
                _add(result, token, "whitespace_before_delimiter", "remove whitespace before delimiter")
            if previous.string == "," and gap == 0 and token.string not in {"}", ")", "]"}:
                _add(result, token, "missing_space_after_comma", "add one space after comma")
            if token.string == "(" and previous.type == tokenize.NAME and previous.string not in _UNARY_KEYWORDS and gap > 0:
                _add(result, token, "space_before_call_parenthesis", "remove whitespace before opening parenthesis")
            if token.string == "[" and gap > 0 and previous.string not in {"=", ",", ":"}:
                _add(result, token, "space_before_indexing_bracket", "remove whitespace before indexing bracket")
        if token.string in _DELIMITERS:
            closing = _DELIMITERS[token.string]
            if index + 1 < len(tokens) and tokens[index + 1].string != closing:
                gap = _spacing(token, tokens[index + 1])
                if gap > 0:
                    _add(result, tokens[index + 1], "space_inside_delimiter", "remove whitespace after opening delimiter")
        if token.string in _DELIMITERS.values() and index > 0:
            opening = next((key for key, value in _DELIMITERS.items() if value == token.string), None)
            if opening and tokens[index - 1].string != opening:
                gap = _spacing(tokens[index - 1], token)
                if gap > 0:
                    _add(result, token, "space_inside_delimiter", "remove whitespace before closing delimiter")
        if token.string in _SPACING_OPERATORS:
            if token.string in {"+", "-"} and _is_unary(index, tokens):
                continue
            if index > 0:
                gap = _spacing(tokens[index - 1], token)
                if gap != 1:
                    _add(result, token, "operator_spacing", "use one space before operator")
            if index + 1 < len(tokens):
                gap = _spacing(token, tokens[index + 1])
                if gap != 1:
                    _add(result, token, "operator_spacing", "use one space after operator")
        if token.string == ":" and index + 1 < len(tokens):
            next_token = tokens[index + 1]
            if _same_line(token, next_token) and _spacing(token, next_token) == 0:
                if next_token.string not in {",", ")", "]", "}"}:
                    _add(result, next_token, "missing_space_after_colon", "add one space after ordinary colon")


def _detect_line_formatting(source: str, result: DetectionResult) -> None:
    for line_number, line in enumerate(source.splitlines(), start=1):
        indentation = line[: len(line) - len(line.lstrip(" \t"))]
        if "\t" in indentation:
            result.locations.append(DetectionLocation(line_number, 0))
            result.evidence.append({"rule": "tabs_or_mixed_indentation", "detail": "tab in indentation"})
        if indentation and set(indentation) == {" "} and len(indentation) % 4 != 0:
            result.locations.append(DetectionLocation(line_number, 0))
            result.evidence.append({"rule": "non_standard_indentation", "detail": f"{len(indentation)} spaces"})
        if line.rstrip(" \t") != line:
            result.locations.append(DetectionLocation(line_number, len(line.rstrip(" \t"))))
            result.evidence.append({"rule": "trailing_whitespace", "detail": "trailing whitespace"})


def detect_inappropriate_formatting(
    source: str, context: TaskContext | None = None
) -> DetectionResult:
    del context
    result = DetectionResult(defect="inappropriate_formatting")
    try:
        ast.parse(source)
    except (SyntaxError, ValueError, TypeError, UnicodeError) as error:
        result.notes = f"Formatting detection requires syntactically valid Python: {error}"
        return result
    _detect_token_spacing(source, result)
    _detect_line_formatting(source, result)
    result.count = len(result.locations)
    result.present = result.count > 0
    return result
