from services.research.dashboard import load_dashboard_data


def test_empirical_dashboard_loads_all_prototype_tasks():
    data = load_dashboard_data()

    assert set(data["prototype_tasks"]) == {"T1", "T2", "T3"}
    assert data["detector_count"] == 18
    assert data["prototype_tasks"]["T1"]["authentic_task_count"] == 20
    assert data["prototype_tasks"]["T2"]["authentic_task_count"] == 19
    assert data["prototype_tasks"]["T3"]["authentic_task_count"] == 7


def test_dashboard_keeps_zero_prevalence_targets_and_omits_not_applicable_defects():
    data = load_dashboard_data()
    t3 = data["prototype_tasks"]["T3"]

    redundant_for = next(
        row for row in t3["target_rows"] if row["defect"] == "redundant_for"
    )
    assert redundant_for["target_prevalence"] == 0.0
    assert "redundant_comparison" in t3["omitted_not_applicable"]


def test_dashboard_task_rows_include_mapping_role_and_report_path():
    data = load_dashboard_data()
    t2 = data["prototype_tasks"]["T2"]
    lab_12_q2 = next(
        row for row in t2["authentic_tasks"] if row["authentic_task"] == "Lab 12 Q2"
    )

    assert lab_12_q2["mapping_role"] == "direct"
    assert lab_12_q2["report_path"].endswith("Lab_12_Q2.json")
    assert lab_12_q2["functionally_correct"] == 539
