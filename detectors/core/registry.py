from collections.abc import Callable

from detectors.legacy.naming import detect_non_descriptive_naming
from detectors.legacy.nesting import detect_excessive_nesting
from detectors.legacy.redundant_boolean import detect_redundant_boolean
from detectors.legacy.unused_variable import detect_unused_variable

Detector = Callable[[str], bool]

DETECTORS: dict[str, Detector] = {
    "non_descriptive_naming": detect_non_descriptive_naming,
    "unused_variable": detect_unused_variable,
    "redundant_boolean_comparison": detect_redundant_boolean,
    "excessive_nesting": detect_excessive_nesting,
}


def detect_defects(source: str, defect_ids: list[str]) -> dict[str, bool]:
    unknown = set(defect_ids).difference(DETECTORS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"No detector registered for: {names}")
    return {defect_id: DETECTORS[defect_id](source) for defect_id in defect_ids}
