from models.types import ProgrammingTask
from services.llm_provider import GenerationProvider


class DemoProvider(GenerationProvider):
    """Deterministic provider used until a live LLM is explicitly integrated."""

    def generate(self, task: ProgrammingTask, batch_size: int, iteration: int = 1) -> list[str]:
        if task.id == "conditional_validation":
            variants = [
                "def classify_score(score):\n    temp = 0\n    if score < 0 or score > 100:\n        raise ValueError('score out of range')\n    if score >= 80:\n        return 'A'\n    elif score >= 60:\n        return 'B'\n    elif score >= 50:\n        return 'C'\n    return 'F'",
                "def classify_score(score):\n    if score < 0 or score > 100:\n        raise ValueError('score out of range')\n    valid = score >= 0\n    if valid == True:\n        if score >= 80:\n            return 'A'\n        elif score >= 60:\n            return 'B'\n        elif score >= 50:\n            return 'C'\n        else:\n            return 'F'",
                "def classify_score(score):\n    if score < 0 or score > 100:\n        raise ValueError('score out of range')\n    if score >= 80: return 'A'\n    if score >= 60: return 'B'\n    if score >= 50: return 'C'\n    return 'F'",
                "def classify_score(score):\n    if score < 0 or score > 100:\n        raise ValueError('score out of range')\n    if score >= 80:\n        if score <= 100:\n            return 'A'\n    if score >= 60:\n        return 'B'\n    if score >= 50:\n        return 'C'\n    return 'F'",
            ]
        else:
            variants = [
                "def summarise_numbers(numbers):\n    unused = 1\n    total = 0\n    for number in numbers:\n        total += number\n    count = len(numbers)\n    average = total / count if count else 0\n    return {'count': count, 'total': total, 'average': average}",
                "def summarise_numbers(numbers):\n    total = sum(numbers)\n    count = len(numbers)\n    average = total / count if count else 0\n    return {'count': count, 'total': total, 'average': average}",
                "def summarise_numbers(numbers):\n    total = 0\n    count = 0\n    for number in numbers:\n        if number == 0 == True:\n            total += number\n        else:\n            total += number\n        count += 1\n    return {'count': count, 'total': total, 'average': total / count if count else 0}",
            ]
        return [variants[(index + iteration - 1) % len(variants)] for index in range(batch_size)]
