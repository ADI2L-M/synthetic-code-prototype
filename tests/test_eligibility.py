import pytest

from services.eligibility import eligibility_for


def test_low_opportunity_remains_eligible():
    eligibility = eligibility_for("T1", "redundant_if_else")

    assert eligibility.status == "eligible"
    assert eligibility.opportunity_level == "low"


def test_not_applicable_is_not_a_negative_observation():
    eligibility = eligibility_for("T2", "redundant_if_else")

    assert eligibility.status == "not_applicable"


def test_t3_redundant_for_is_low_opportunity_but_eligible():
    eligibility = eligibility_for("T3", "redundant_for")

    assert eligibility.status == "eligible"
    assert eligibility.opportunity_level == "low"


def test_unknown_task_fails_loudly():
    with pytest.raises(ValueError, match="Unknown research task"):
        eligibility_for("T9", "magic_number")


def test_unclassified_defect_fails_loudly():
    with pytest.raises(ValueError, match="not classified"):
        eligibility_for("T1", "not_a_real_defect")
