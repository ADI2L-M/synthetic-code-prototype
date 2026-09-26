import pytest

from detectors.research.assignments import detect_augmentable_assignment
from detectors.research.collections import (
    detect_duplicate_expression,
    detect_misleading_iterator_name,
    detect_redundant_indexing,
)
from detectors.research.conditionals import (
    detect_duplicate_if,
    detect_else_if,
    detect_empty_if,
    detect_nested_if,
    detect_redundant_elif,
    detect_redundant_if_else,
    detect_redundant_not,
)
from detectors.research.formatting import detect_inappropriate_formatting
from detectors.research.iteration import detect_redundant_for, detect_while_as_for
from detectors.research.magic import detect_magic_number
from detectors.research.names import detect_built_in_name, detect_one_letter_name
from detectors.research.registry import RESEARCH_DETECTORS, detect_research_defects
from detectors.research.redundant_comparison import detect_redundant_comparison_result


def test_research_registry_covers_all_catalog_defects():
    expected = {
        "redundant_if_else",
        "redundant_comparison",
        "redundant_not",
        "duplicate_if",
        "else_if",
        "nested_if",
        "redundant_elif",
        "empty_if",
        "redundant_indexing",
        "misleading_iterator_name",
        "duplicate_expression",
        "while_as_for",
        "redundant_for",
        "augmentable_assignment",
        "inappropriate_formatting",
        "magic_number",
        "one_letter_name",
        "built_in_name",
    }
    assert set(RESEARCH_DETECTORS) == expected


@pytest.mark.parametrize(
    ("detector", "source"),
    [
        (
            detect_redundant_if_else,
            "if condition:\n    return True\nelse:\n    return False\n",
        ),
        (
            detect_redundant_comparison_result,
            "if (temp < 10) == True:\n    return 'cold'\n",
        ),
        (
            detect_redundant_not,
            "if not temp >= 10:\n    return 'cold'\n",
        ),
        (
            detect_duplicate_if,
            "if temp < 0:\n    return 'cold'\nelif temp < 10:\n    return 'cold'\n",
        ),
        (
            detect_else_if,
            "if temp < 10:\n    return 'cold'\nelse:\n    if temp < 25:\n        return 'mild'\n",
        ),
        (
            detect_nested_if,
            "if temp >= 10:\n    if temp < 25:\n        return 'mild'\n",
        ),
        (
            detect_redundant_elif,
            "if temp < 10:\n    return 'cold'\nelif temp >= 10:\n    return 'mild'\n",
        ),
        (
            detect_empty_if,
            "if temp >= 10:\n    pass\nelse:\n    return 'cold'\n",
        ),
        (
            detect_redundant_indexing,
            "total = 0\nfor i in range(len(scores)):\n    total += scores[i]\n",
        ),
        (
            detect_misleading_iterator_name,
            "for i in scores:\n    total += i\n",
        ),
        (
            detect_duplicate_expression,
            "for i in range(len(scores)):\n    if scores[i] > 0:\n        total += scores[i]\n",
        ),
        (
            detect_while_as_for,
            "i = 1\ntotal = 0\nwhile i <= n:\n    total += i\n    i += 1\n",
        ),
        (
            detect_redundant_for,
            "for i in range(1):\n    return n\n",
        ),
        (
            detect_augmentable_assignment,
            "total = total + score\n",
        ),
        (detect_inappropriate_formatting, "total=0\n"),
        (detect_magic_number, "if temp < 10:\n    return 'cold'\n"),
        (detect_one_letter_name, "x = 0\nreturn_value = x\n"),
        (detect_built_in_name, "sum = 0\n"),
    ],
)
def test_catalog_detector_positive_cases(detector, source):
    result = detector(source)

    assert result.present is True
    assert result.count >= 1
    assert result.locations
    assert result.evidence


@pytest.mark.parametrize(
    ("detector", "source"),
    [
        (detect_redundant_if_else, "return condition\n"),
        (detect_redundant_comparison_result, "if value < 10:\n    return True\n"),
        (detect_redundant_not, "if value in values:\n    return True\n"),
        (
            detect_duplicate_if,
            "if temp < 0:\n    return 'cold'\nelif temp < 10:\n    return 'mild'\n",
        ),
        (
            detect_else_if,
            "if temp < 10:\n    return 'cold'\nelif temp < 25:\n    return 'mild'\n",
        ),
        (
            detect_nested_if,
            "if temp >= 10:\n    log('entered')\n    if temp < 25:\n        return 'mild'\n",
        ),
        (
            detect_redundant_elif,
            "if temp < 10:\n    return 'cold'\nelif temp < 25:\n    return 'mild'\n",
        ),
        (detect_empty_if, "if temp >= 10:\n    pass\n"),
        (
            detect_redundant_indexing,
            "for i in range(len(scores)):\n    total += scores[i]\n    print(i)\n",
        ),
        (detect_misleading_iterator_name, "for i in range(len(scores)):\n    total += scores[i]\n"),
        (
            detect_duplicate_expression,
            "if scores[i] > 0:\n    total += scores[j]\n",
        ),
        (detect_while_as_for, "while input('continue?'):\n    pass\n"),
        (detect_redundant_for, "for item in items:\n    use(item)\n"),
        (detect_augmentable_assignment, "total = score + total\n"),
        (detect_inappropriate_formatting, "total = 0\n"),
        (detect_magic_number, "total = 0\nfor i in range(1):\n    total += i\n"),
        (detect_one_letter_name, "for i in range(n):\n    total += i\n"),
        (detect_built_in_name, "total = 0\n"),
    ],
)
def test_catalog_detector_negative_cases(detector, source):
    result = detector(source)

    assert result.present is False
    assert result.count == 0
    assert result.locations == []


def test_registry_runs_selected_detectors_without_changing_raw_results():
    results = detect_research_defects(
        "if (temp < 10) == True:\n    return 'cold'\n",
        ["redundant_comparison", "magic_number"],
    )

    assert results["redundant_comparison"].present is True
    assert results["magic_number"].present is True


def test_parse_failure_is_recorded_for_every_research_detector():
    results = detect_research_defects("def broken(:")

    assert len(results) == 18
    assert all(not result.present for result in results.values())
    assert all(result.notes for result in results.values())
