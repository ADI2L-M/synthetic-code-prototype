from detectors.research.redundant_comparison import detect_redundant_comparison_result


def test_redundant_comparison_detects_boolean_comparison():
    result = detect_redundant_comparison_result(
        "def classify(temp):\n"
        "    if (temp < 10) == True:\n"
        "        return 'cold'\n"
    )

    assert result.present
    assert result.count == 1
    assert result.locations[0].line == 2


def test_redundant_comparison_detects_locally_proven_boolean_name():
    result = detect_redundant_comparison_result(
        "def classify(score):\n"
        "    valid = score >= 0\n"
        "    return valid == True\n"
    )

    assert result.present
    assert result.count == 1
    assert result.evidence[0]["boolean_operand"] == "valid"


def test_redundant_comparison_rejects_arbitrary_truthy_name():
    result = detect_redundant_comparison_result(
        "def classify(value):\n"
        "    return value == True\n"
    )

    assert not result.present
    assert result.count == 0
    assert result.locations == []


def test_redundant_comparison_does_not_treat_chained_comparison_as_target_pattern():
    result = detect_redundant_comparison_result(
        "def classify(value):\n"
        "    return value > 3 == True\n"
    )

    assert not result.present


def test_redundant_comparison_detects_not_expression_comparison():
    result = detect_redundant_comparison_result(
        "def classify(value):\n"
        "    return (not value) == False\n"
    )

    assert result.present
    assert result.count == 1
