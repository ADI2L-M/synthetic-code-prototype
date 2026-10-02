"""Research overview view for the prototype home page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
IMAGE_ASSETS = ROOT / "research-notes" / "image-assets"


def _asset(name: str) -> str:
    return str(IMAGE_ASSETS / name)


def _research_question_card(label: str, title: str, description: str) -> None:
    with st.container(border=True, height="stretch"):
        st.caption(label)
        st.markdown(f"**{title}**")
        st.write(description)


def render_home(data: dict[str, Any]) -> None:
    """Render the research overview, evidence summary, and prototype entry points."""
    st.caption("RESEARCH PROTOTYPE · SYNTHETIC CODE STUDY")
    st.title("Synthetic code research prototype", icon=":material/science:")

    hero_copy, hero_figure = st.columns([1.25, 1], vertical_alignment="center")
    with hero_copy:
        st.badge("Research prototype", icon=":material/experiment:", color="blue")
        st.markdown(
            """
            This project investigates whether authentic CS1 Python submissions can
            provide an empirical target for generating **functionally correct
            synthetic programs** with comparable observable defect distributions.

            The prototype connects authentic-submission analysis, task-aware LLM
            prompting, functional validation, structural defect detection, and
            distribution-based evaluation in one traceable workflow.
            """
        )
        st.caption(
            "The focus is on observable source-code characteristics, not on "
            "reproducing the complete cognitive behaviour of an individual novice."
        )
        with st.container(horizontal=True, horizontal_alignment="left"):
            st.page_link(
                "app_pages/generation.py",
                label="Open generation",
                icon=":material/auto_awesome:",
                width="content",
            )
            st.page_link(
                "app_pages/defect_detection.py",
                label="Inspect authentic evidence",
                icon=":material/analytics:",
                width="content",
            )
    with hero_figure:
        st.image(
            _asset("disrm.png"),
            caption=(
                "Research logic: data observation provides the grounding for "
                "contextual profiling and synthetic representation."
            ),
            width="stretch",
        )

    with st.container(border=True):
        st.subheader("The central research question", icon=":material/help:")
        st.markdown(
            "Can guided, empirically informed LLM generation produce functionally "
            "correct submissions whose **defect profile is sufficiently close to an "
            "authentic-student reference**?"
        )
        st.caption(
            "A synthetic batch is treated as a sample from a target distribution. "
            "Exact defect-by-defect equality is not required; sampling uncertainty "
            "remains part of the interpretation."
        )

    st.header("Why this research matters", icon=":material/lightbulb:")
    problem, gap = st.columns(2, vertical_alignment="top")
    with problem:
        with st.container(border=True, height="stretch"):
            st.subheader("The problem", icon=":material/priority_high:")
            st.write(
                "LLMs can solve introductory programming tasks, and prior work has "
                "studied prompting, code quality, and synthetic programming data. "
                "However, code that merely looks novice-like is not the same as code "
                "that represents empirically observed novice characteristics."
            )
            st.caption(
                "Authentic novice-code characteristics and LLM generation are useful "
                "separately, but their integration is the focus here."
            )
    with gap:
        with st.container(border=True, height="stretch"):
            st.subheader("The research gap", icon=":material/compare_arrows:")
            st.write(
                "The project integrates five capabilities that are commonly treated "
                "as separate: authentic-code profiling, defect-informed generation, "
                "functional validation, structural detection, and comparison against "
                "an empirical target distribution."
            )
            st.caption(
                "This makes the representation traceable from observed student code to "
                "generation constraints and evaluation evidence."
            )

    st.header("Research questions", icon=":material/quiz:")
    question_columns = st.columns(3, gap="small")
    questions = [
        (
            "RQ1 · Defect classification",
            "What observable characteristics should be represented?",
            "Identify and classify task-relevant structural characteristics in authentic CS1 submissions.",
        ),
        (
            "RQ2 · Defect-informed generation",
            "Can the characteristics guide generation?",
            "Translate task-aware empirical profiles into constraints for generating functionally correct Python code.",
        ),
        (
            "RQ3 · Distribution alignment",
            "Does iterative control improve similarity?",
            "Compare synthetic prevalence with the authentic target while monitoring functional correctness separately.",
        ),
    ]
    for column, (label, title, description) in zip(question_columns, questions):
        with column:
            _research_question_card(label, title, description)

    st.header("From authentic evidence to synthetic code", icon=":material/account_tree:")
    profile_text, profile_figure = st.columns([1, 1.1], vertical_alignment="center")
    with profile_text:
        st.markdown(
            """
            The prototype first observes authentic submissions and analyses their
            context. It separates context-dependent characteristics from
            context-independent characteristics, then combines them into a
            **context-aware target profile**.

            That profile informs task-specific prompts. Generated programs are
            functionally validated before the shared detector registry measures the
            same characteristics in both authentic and synthetic code.
            """
        )
        st.caption(
            "Related artefact: context-aware classification and profiling framework."
        )
    with profile_figure:
        st.image(
            _asset("context-aware-synthetic.png"),
            caption=(
                "The conceptual pipeline from data observation and contextual "
                "profiling to iteratively calibrated synthetic generation."
            ),
            width="stretch",
        )

    st.subheader("Prototype at a glance", icon=":material/route:")
    workflow_text, workflow_figure = st.columns([1.05, 1], vertical_alignment="center")
    with workflow_text:
        workflow = pd.DataFrame(
            [
                {
                    "Stage": "1 · Authentic baseline",
                    "Prototype action": "Filter authentic submissions by functional correctness and map lab questions to T1, T2, or T3.",
                    "Evidence": "Eligible task collections",
                },
                {
                    "Stage": "2 · Defect profile",
                    "Prototype action": "Run the shared AST detector registry on eligible authentic submissions.",
                    "Evidence": "Task-level prevalence targets",
                },
                {
                    "Stage": "3 · Synthetic generation",
                    "Prototype action": "Guide an Ollama model with the task contract and assigned defect styles, then retry failed outputs.",
                    "Evidence": "Functionally validated code",
                },
                {
                    "Stage": "4 · Comparison",
                    "Prototype action": "Compare synthetic prevalence with the authentic target using sampling-aware uncertainty.",
                    "Evidence": "Iteration-level analytics",
                },
            ]
        )
        st.dataframe(workflow, hide_index=True, width="stretch", height=260)
    with workflow_figure:
        st.image(
            _asset("synthetic-novice-code-gen-cal-proto.png"),
            caption=(
                "Generation, validation, defect detection, profile comparison, and "
                "calibration form a repeatable experimental loop."
            ),
            width="stretch",
        )

    st.header("Current prototype evidence", icon=":material/monitoring:")
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

    st.subheader("Authentic reference scope", icon=":material/dataset:")
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
        "Counts are derived from the mapped authentic task reports and functional-validation outputs."
    )

    st.subheader("Authentic baseline by prototype task", icon=":material/bar_chart:")
    baseline_figure = scope.set_index("Prototype task")[[
        "Functionally correct submissions"
    ]]
    st.bar_chart(baseline_figure, horizontal=True)
    st.caption(
        "Original figure generated from the project data; the research literature supports the framing, not these numeric values."
    )

    st.header("How performance is judged", icon=":material/assessment:")
    correctness, alignment = st.columns(2, vertical_alignment="top")
    with correctness:
        with st.container(border=True, height="stretch"):
            st.subheader("Functional correctness", icon=":material/check_circle:")
            st.write(
                "Generated submissions must continue to satisfy the original task "
                "contract. The prototype records generated submissions, functional "
                "pass rate, and repair or retry behaviour."
            )
    with alignment:
        with st.container(border=True, height="stretch"):
            st.subheader("Defect-profile alignment", icon=":material/insights:")
            st.write(
                "For each defect and task, the observed synthetic prevalence is "
                "compared with the authentic target. The comparison is reported by "
                "iteration so calibration effects remain visible."
            )

    calibration_text, calibration_figure = st.columns([1, 1.05], vertical_alignment="center")
    with calibration_text:
        st.subheader("Iterative refinement", icon=":material/replay:")
        st.write(
            "The experimental loop is deliberately adaptive: target profile → prompt "
            "→ generation → validation → detection → comparison → refinement. A "
            "non-adaptive condition provides a baseline for assessing whether this "
            "feedback loop improves distribution alignment without sacrificing correctness."
        )
    with calibration_figure:
        st.image(
            _asset("iteratively-calibrated-framework.png"),
            caption="Iterative calibration connects evaluation results back to generation constraints.",
            width="stretch",
        )

    st.header("Current scope and evidence status", icon=":material/fact_check:")
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
