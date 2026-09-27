"""Home view for the research prototype application."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_home(data: dict[str, Any]) -> None:
    """Render the application landing view and prototype research summary."""
    st.caption("RESEARCH PROTOTYPE · SYNTHETIC CODE STUDY")
    st.title("Synthetic code research prototype")
    st.write(
        "This prototype generates functionally correct Python submissions for "
        "three programming-task families and evaluates how closely their observed "
        "defect prevalence resembles the authentic-student baseline. The Home page "
        "summarises the evidence, workflow, and current research scope. The framing "
        "is grounded in the project introduction and artefact-design notes [A1, A3, A4]."
    )
    st.caption(
        "Citation keys used on this page: [A1] introduction · [A2] literature review · "
        "[A3] artefact conceptualisation · [A4] system design"
    )
    st.info(
        "Authentic submissions provide the empirical reference distribution. The "
        "generation page uses the resulting target profile to guide an LLM, validates "
        "each generated submission, and measures defects with the same detector "
        "service used for the authentic analysis."
    )

    with st.container(horizontal=True, horizontal_alignment="distribute"):
        st.page_link(
            "app_pages/generation.py",
            label="Open generation",
            icon=":material/auto_awesome:",
            width="stretch",
        )
        st.page_link(
            "app_pages/defect_detection.py",
            label="Open defect detection",
            icon=":material/analytics:",
            width="stretch",
        )

    prototype_tasks = data["prototype_tasks"]
    total_authentic_tasks = sum(
        task["authentic_task_count"] for task in prototype_tasks.values()
    )
    total_correct_submissions = sum(
        task["functionally_correct_count"] for task in prototype_tasks.values()
    )
    metrics = [
        ("Prototype tasks", len(prototype_tasks)),
        ("Mapped authentic tasks", total_authentic_tasks),
        ("Functionally correct submissions", f"{total_correct_submissions:,}"),
        ("Shared AST detectors", data["detector_count"]),
    ]
    columns = st.columns(len(metrics), gap="small")
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value, border=True)

    st.subheader("Prototype at a glance")
    workflow = pd.DataFrame(
        [
            {
                "Stage": "1 · Authentic baseline",
                "What the prototype does": "Filters authentic submissions by functional correctness and maps lab questions to T1, T2, or T3.",
                "Output": "Functionally correct task collections",
            },
            {
                "Stage": "2 · Defect profile",
                "What the prototype does": "Runs the shared AST detector registry on eligible authentic submissions.",
                "Output": "Task-level and prototype-level prevalence targets",
            },
            {
                "Stage": "3 · Synthetic generation",
                "What the prototype does": "Guides an Ollama model with the task contract and assigned defect styles, then retries failed outputs.",
                "Output": "Functionally validated synthetic submissions",
            },
            {
                "Stage": "4 · Comparison",
                "What the prototype does": "Measures synthetic defect prevalence and compares it with the authentic target using sampling-aware uncertainty.",
                "Output": "Per-iteration analytics and exported code",
            },
        ]
    )
    st.dataframe(workflow, hide_index=True, width="stretch", height=250)

    st.subheader("Authentic reference scope")
    scope = pd.DataFrame(
        [
            {
                "Prototype task": task["label"],
                "Task family": task["task_family"],
                "Mapped lab questions": task["authentic_task_count"],
                "Functionally correct submissions": task["functionally_correct_count"],
                "Defect targets": len(task["target_rows"]),
            }
            for task in prototype_tasks.values()
        ]
    )
    st.dataframe(scope, hide_index=True, width="stretch")
    st.caption(
        "Table 1. Authentic reference scope used by the prototype. Counts are derived "
        "from the mapped task reports and functional-validation outputs [A1, A2]."
    )

    st.subheader("Authentic baseline by prototype task")
    baseline_figure = scope.set_index("Prototype task")[[
        "Functionally correct submissions"
    ]]
    st.bar_chart(baseline_figure, horizontal=True)
    st.caption(
        "Figure 1. Functionally correct authentic submissions available for each "
        "prototype task. This is an original figure generated from the project data; "
        "the literature references support the research framing, not the numeric values [A1, A2, A4]."
    )

    st.subheader("How performance is judged")
    st.markdown(
        "The prototype does not attempt to reproduce an individual student submission. "
        "It compares distributions: for each defect, the observed synthetic prevalence "
        "is compared with the authentic target prevalence among functionally correct, "
        "eligible submissions. The result is reported per task and per generation "
        "iteration so that functional correctness and defect coverage remain visible "
        "alongside prevalence. This distribution-oriented evaluation is part of the "
        "prototype design and evaluation framing [A2, A3, A4]."
    )
    with st.container(border=True):
        st.markdown("**Primary prototype question**")
        st.write(
            "Can guided LLM generation produce functionally correct submissions whose "
            "defect profile is sufficiently close to the authentic-student reference?"
        )
        st.caption(
            "The authentic profile is an empirical target, not a quota for individual "
            "submissions. Small synthetic batches are interpreted with sampling uncertainty."
        )

    st.subheader("Current scope and evidence status")
    scope_status = pd.DataFrame(
        [
            {
                "Area": "Included in this prototype",
                "Status": "Implemented",
                "Detail": "T1/T2/T3 generation, functional validation, shared AST detection, calibration, comparison, analytics, and code export.",
            },
            {
                "Area": "Authentic prevalence",
                "Status": "Available",
                "Detail": "Target profile is derived from mapped authentic lab tasks using the configured eligibility matrix.",
            },
            {
                "Area": "Detector validity",
                "Status": "Preliminary",
                "Detail": "Raw detector estimates are available; manual precision/recall and false-positive review remain future validation work.",
            },
            {
                "Area": "Final synthetic benchmark",
                "Status": "Pending",
                "Detail": "A larger fixed-configuration run is still needed before making final model or prevalence claims.",
            },
        ]
    )
    st.dataframe(scope_status, hide_index=True, width="stretch")

    st.subheader("Research basis and citation notes")
    st.markdown(
        "The following project literature notes are cited explicitly in the summary. "
        "Replace each key with the author–year format from the source document before "
        "using this text in the final report."
    )
    references = pd.DataFrame(
        [
            {
                "Key": "[A1]",
                "Project reference": "research-notes/research-literatures/A1-introduction.pdf",
                "Use in the prototype summary": "Problem framing, motivation, and research objective.",
                "Report citation placeholder": "[Author(s), year]",
            },
            {
                "Key": "[A2]",
                "Project reference": "research-notes/research-literatures/A2-literature-review.pdf",
                "Use in the prototype summary": "Literature-grounded context and identification of the research gap.",
                "Report citation placeholder": "[Author(s), year]",
            },
            {
                "Key": "[A3]",
                "Project reference": "research-notes/research-literatures/A3-conceptualize-artefacts.pdf",
                "Use in the prototype summary": "Conceptualisation of the generation and evaluation artefact.",
                "Report citation placeholder": "[Author(s), year]",
            },
            {
                "Key": "[A4]",
                "Project reference": "research-notes/research-literatures/A4-designing-system.pdf",
                "Use in the prototype summary": "System design, implementation stages, and prototype evaluation framing.",
                "Report citation placeholder": "[Author(s), year]",
            },
        ]
    )
    st.dataframe(references, hide_index=True, width="stretch")
    st.caption(
        "The four files are project literature notes currently stored in "
        "research-notes/research-literatures; the application does not infer author or "
        "publication metadata from their filenames."
    )
    st.warning(
        "External citation placeholders for the final report: cite the original source "
        "for the design-science/artefact evaluation method discussed in [A3]/[A4], and "
        "cite the original source for LLM-generated-code evaluation or synthetic-data "
        "validity discussed in [A2]. Add the author–year references before publication."
    )
