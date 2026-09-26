from services.research.target_profile import (
    build_empirical_target_profile,
    load_empirical_target_values,
)


def _summary() -> dict:
    return {
        "prototype_tasks": {
            "T1": {
                "task_family": "conditional_logic",
                "defects": {
                    "magic_number": {
                        "task_mean_prevalence": 0.25,
                        "eligible_task_count": 2,
                        "valid_submission_count": 10,
                        "affected_submission_count": 3,
                        "pooled_prevalence": 0.3,
                        "minimum_task_prevalence": 0.2,
                        "maximum_task_prevalence": 0.3,
                        "standard_deviation": 0.05,
                    },
                    "redundant_for": {
                        "task_mean_prevalence": None,
                        "eligible_task_count": 0,
                        "valid_submission_count": 0,
                        "affected_submission_count": 0,
                        "pooled_prevalence": None,
                        "minimum_task_prevalence": None,
                        "maximum_task_prevalence": None,
                        "standard_deviation": None,
                    },
                },
            }
        }
    }


def test_profile_uses_task_mean_and_omits_non_applicable_defects():
    profile = build_empirical_target_profile(
        _summary(),
        {"defects": [{"name": "magic_number", "category": "task_independent"}]},
    )

    task_profile = profile["prototype_tasks"]["T1"]
    assert task_profile["target_profile"] == {"magic_number": 0.25}
    assert task_profile["task_independent"]["magic_number"]["pooled_prevalence"] == 0.3
    assert task_profile["omitted_not_applicable"] == ["redundant_for"]


def test_load_empirical_target_values_reads_flat_generation_profile(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(
        '{"prototype_tasks": {"T2": {"target_profile": {"magic_number": 0.1}}}}',
        encoding="utf-8",
    )

    assert load_empirical_target_values(path, "T2") == {"magic_number": 0.1}
