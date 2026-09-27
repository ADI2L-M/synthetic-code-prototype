import json
from pathlib import Path

from services.authentic.functional_validation import (
    load_test_plans,
    validate_authentic_source,
)
from services.authentic.ingestion import load_task_submissions


WORKBOOK = Path("research-notes/data-identification/cs1_labs_responses.xlsx")
GROUPING = Path("research-notes/data-identification/cs1_regeneration_task_groups.json")
PLAN_FILE = Path("research-notes/functional-tests/authentic_test_cases.json")


def test_test_plan_covers_all_grouped_authentic_tasks():
    grouping = json.loads(GROUPING.read_text(encoding="utf-8"))
    labels = {
        label
        for definition in grouping.values()
        for group in ("direct", "supporting")
        for label in definition[group]
    }
    assert set(load_test_plans(PLAN_FILE)) == labels


def test_all_right_answers_pass_their_functional_contract():
    plans = load_test_plans(PLAN_FILE)
    grouping = json.loads(GROUPING.read_text(encoding="utf-8"))
    for definition in grouping.values():
        for group in ("direct", "supporting"):
            for label in definition[group]:
                lab, question = label.split(" Q")
                submissions = load_task_submissions(
                    WORKBOOK,
                    GROUPING,
                    int(lab.split()[1]),
                    int(question),
                )
                reference = submissions[0].reference_code
                assert reference
                result = validate_authentic_source(
                    reference,
                    reference,
                    plans[label],
                )
                assert result.status == "PASS", (label, result.failure_message)


def test_structured_answer_is_compared_without_code_execution():
    plan = load_test_plans(PLAN_FILE)["Lab 4 Q11"]
    result = validate_authentic_source(
        '["member == \'yes\'", "current_cart_amount >= 500", '
        '"current_cart_amount >= 300", "current_cart_amount >= 200", '
        '"current_cart_amount >= 100", "current_cart_amount >= 500", '
        '"current_cart_amount >= 300"]',
        '["member == \\"yes\\"", "current_cart_amount >= 500", '
        '"current_cart_amount >= 300", "current_cart_amount >= 200", '
        '"current_cart_amount >= 100", "current_cart_amount >= 500", '
        '"current_cart_amount >= 300"]',
        plan,
    )
    assert result.status == "PASS"
