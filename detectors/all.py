"""Backward-compatible detector imports.

New code should import the individual detector modules or ``registry``.
"""

from detectors.naming import detect_non_descriptive_naming
from detectors.nesting import detect_excessive_nesting
from detectors.redundant_boolean import detect_redundant_boolean
from detectors.registry import DETECTORS, detect_defects
from detectors.unused_variable import detect_unused_variable

__all__ = [
    "DETECTORS",
    "detect_defects",
    "detect_excessive_nesting",
    "detect_non_descriptive_naming",
    "detect_redundant_boolean",
    "detect_unused_variable",
]
