from models.types import ProgrammingTask


def build_generation_specification(task: ProgrammingTask, target: dict[str, float], constraints: dict[str, str] | None = None) -> str:
    constraints = constraints or {key: "include where appropriate" for key in target}
    independent = [f"- {key.replace('_', ' ')} ({value:.0%} target): {constraints.get(key, 'include where appropriate')}" for key, value in target.items() if key in {"non_descriptive_naming", "unused_variable"}]
    dependent = [f"- {key.replace('_', ' ')} ({value:.0%} target): {constraints.get(key, 'include where appropriate')}" for key, value in target.items() if key not in {"non_descriptive_naming", "unused_variable"}]
    return (
        f"PROGRAMMING TASK\n\n{task.description}\n\n"
        "FUNCTIONAL REQUIREMENTS\n\n"
        + "\n".join(f"- {item}" for item in task.functional_requirements)
        + "\n\nTASK-INDEPENDENT CHARACTERISTICS\n\n"
        + "\n".join(independent)
        + "\n\nTASK-DEPENDENT CHARACTERISTICS\n\n"
        + ("\n".join(dependent) or "- No additional task-dependent characteristics selected.")
        + "\n\nIMPORTANT\n\nThe program must remain functionally correct."
    )
