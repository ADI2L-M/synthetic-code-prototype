from services.authentic.ingestion import AuthenticSubmission
from services.research.authentic_detector_review import build_authentic_review_records


def test_authentic_review_records_include_detector_output_and_blank_manual_label():
    submissions = [
        AuthenticSubmission(
            "S1",
            1,
            1,
            "T1",
            (
                "def classify_temperature(temp):\n"
                "    if temp < 10:\n"
                "        return 'cold'\n"
                "    elif temp >= 10:\n"
                "        return 'mild'\n"
            ),
            None,
            2,
        )
    ]

    records, summary = build_authentic_review_records(
        submissions,
        per_class=1,
        seed=7,
    )

    assert records
    assert summary["submission_count"] == 1
    assert summary["parseable_submission_count"] == 1
    assert all(record["manual_label"] is None for record in records)
    assert all(record["detector_label"] in (0, 1) for record in records)
    assert all(record["source_code"].startswith("def classify_temperature") for record in records)
    assert all(record["eligibility"] == "eligible" for record in records)


def test_authentic_review_sampling_is_reproducible_and_supports_all_cases():
    source = "def f(value):\n    return value + 10\n"
    submissions = [
        AuthenticSubmission(f"S{index}", 1, 1, "T1", source, None, index)
        for index in range(1, 4)
    ]

    first, first_summary = build_authentic_review_records(
        submissions,
        per_class=1,
        seed=11,
    )
    second, _second_summary = build_authentic_review_records(
        submissions,
        per_class=1,
        seed=11,
    )
    all_records, all_summary = build_authentic_review_records(
        submissions,
        per_class=0,
        seed=11,
    )

    assert first == second
    assert first_summary["selected_case_count"] == len(first)
    assert all_summary["selected_case_count"] >= first_summary["selected_case_count"]
    assert len(all_records) > len(first)
