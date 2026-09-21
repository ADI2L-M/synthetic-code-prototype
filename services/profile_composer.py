from models.types import DefectDefinition, ProgrammingTask

DEFINITIONS = [
    DefectDefinition("non_descriptive_naming", "Non-descriptive naming", "Task-independent", "naming", "Short, vague identifiers such as x or tmp."),
    DefectDefinition("unused_variable", "Unused variable", "Task-independent", "unused_variable", "An assigned local variable is never read."),
    DefectDefinition("redundant_boolean_comparison", "Redundant Boolean comparison", "Task-dependent", "redundant_boolean", "A Boolean expression is compared explicitly with True or False."),
    DefectDefinition("excessive_nesting", "Excessive nesting", "Task-dependent", "nesting", "Control structures are nested beyond the demonstration threshold."),
]


def definitions_by_id() -> dict[str, DefectDefinition]:
    return {definition.id: definition for definition in DEFINITIONS}


def compose_target_profile(task: ProgrammingTask, profiles: dict) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    independent = dict(profiles["task_independent"])
    dependent = dict(profiles["task_dependent"].get(task.id, {}))
    return independent, dependent, {**independent, **dependent}


def applicable_defects(task: ProgrammingTask) -> list[DefectDefinition]:
    return [definition for definition in DEFINITIONS if definition.classification == "Task-independent" or definition.id in {"redundant_boolean_comparison", "excessive_nesting"} and "branching" in task.contexts]
