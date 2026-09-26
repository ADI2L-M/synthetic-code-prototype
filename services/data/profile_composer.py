from models.types import DefectDefinition, ProgrammingTask
from services.data.loader import load_defect_definitions


def definitions_by_id() -> dict[str, DefectDefinition]:
    return {definition.id: definition for definition in load_defect_definitions()}


def compose_target_profile(
    task: ProgrammingTask, profiles: dict
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    independent = dict(profiles["task_independent"])
    applicable_ids = {
        definition.id
        for definition in applicable_defects(task)
        if definition.classification == "Task-dependent"
    }
    dependent = {
        defect_id: value
        for defect_id, value in profiles["task_dependent"].get(task.id, {}).items()
        if defect_id in applicable_ids
    }
    return independent, dependent, {**independent, **dependent}


def applicable_defects(task: ProgrammingTask) -> list[DefectDefinition]:
    contexts = set(task.contexts)
    return [
        definition
        for definition in load_defect_definitions()
        if definition.classification == "Task-independent"
        or bool(contexts.intersection(definition.applicable_contexts))
    ]
