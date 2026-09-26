import pytest

from detectors.legacy.naming import detect_non_descriptive_naming
from detectors.legacy.nesting import detect_excessive_nesting
from detectors.legacy.redundant_boolean import detect_redundant_boolean
from detectors.core.registry import detect_defects
from detectors.legacy.unused_variable import detect_unused_variable


def test_naming_detector_uses_documented_vague_name_heuristic():
    assert detect_non_descriptive_naming(
        "def total(values):\n    x = sum(values)\n    return x"
    )
    assert not detect_non_descriptive_naming(
        "def total(values):\n    result = sum(values)\n    return result"
    )


def test_unused_variable_detector_compares_assignments_and_references():
    assert detect_unused_variable("def f():\n    unused = 1\n    return 2")
    assert not detect_unused_variable("def f():\n    value = 1\n    return value")


def test_redundant_boolean_detector_finds_explicit_comparison():
    assert detect_redundant_boolean("def f(value):\n    return value == True")
    assert not detect_redundant_boolean("def f(value):\n    return bool(value)")


def test_nesting_detector_uses_control_structure_depth():
    source = "def f(x):\n    if x:\n        for value in x:\n            if value:\n                return value"
    assert detect_excessive_nesting(source)


def test_registry_rejects_unknown_detector_ids():
    with pytest.raises(ValueError, match="No detector registered"):
        detect_defects("pass", ["not_configured"])
