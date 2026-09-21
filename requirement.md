# Prototype Requirements Specification

## 1. Project Title

**Synthetic Novice Code Generation and Calibration Prototype**

## 2. Prototype Purpose

The prototype demonstrates the technical feasibility of generating functionally correct synthetic novice Python submissions according to a **Context-Aware Target Profile**.

The system must distinguish between:

- **Task-independent defect characteristics**, which can apply across programming tasks.
- **Task-dependent defect characteristics**, which are selected according to the context of the chosen programming task.

The prototype must then use the resulting target profile to construct an LLM generation specification, generate synthetic code, validate functional correctness, detect selected defects, compare the observed defect profile with the target profile, and revise the generation specification when required.

The prototype is a **proof of concept**, not the complete empirical research system. Target profiles may therefore use clearly labelled demonstration values.

---

## 3. System Workflow

The implementation must follow this process:

```text
Programming Task
        ↓
Analyse Task Context
        ↓
Task Context Profile
        ↓
Select Applicable Task-Dependent Defects
        ↓

Task-Independent Defect Profile
        +
Applicable Task-Dependent Defect Profile
        ↓
Context-Aware Target Profile
        ↓

Programming Task
        +
Context-Aware Target Profile
        ↓
Construct Generation Specification
        ↓
Generate Synthetic Code with LLM
        ↓
Functional Validation
        ↓
Functionally Correct?
    ┌───────────────┴───────────────┐
    No                              Yes
    ↓                                ↓
Functional Test Feedback        Detect Defects
    ↓                                ↓
Revise Generation             Observed Synthetic
Specification                  Defect Profile
    │                                ↓
    └──────────────↺          Compare Target and
                               Observed Profiles
                                      ↓
                         Is discrepancy within
                               tolerance?
                         ┌──────────┴──────────┐
                         No                    Yes
                         ↓                      ↓
                  Calibrate Generation      Accept Synthetic
                      Constraints           Submissions
                         ↓
                 Revise Generation
                    Specification
                         │
                         └────────────↺
```

The system must **not modify the Context-Aware Target Profile during calibration**. Calibration changes the generation specification or generation constraints only.

---

## 4. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The system shall allow the user to select a predefined CS1 Python programming task. |
| FR-02 | Each task shall contain a description, functional requirements, test cases, and task-context metadata. |
| FR-03 | The system shall maintain a Task-Independent Defect Profile separately from task-dependent defect information. |
| FR-04 | The system shall maintain a Task-Dependent Defect Repository containing defect categories and the task contexts in which they are applicable. |
| FR-05 | The system shall analyse the selected task context using predefined task metadata. |
| FR-06 | The system shall select applicable task-dependent defects according to the selected task context. |
| FR-07 | The system shall combine the Task-Independent Defect Profile and applicable Task-Dependent Defect Profile into a Context-Aware Target Profile. |
| FR-08 | The system shall display the two profile components separately before displaying the combined target profile. |
| FR-09 | The system shall construct a Generation Specification using both the Programming Task and the Context-Aware Target Profile. |
| FR-10 | The user shall be able to inspect the Generation Specification before generation. |
| FR-11 | The system shall generate a configurable batch of synthetic Python submissions. |
| FR-12 | LLM access shall be implemented through a provider abstraction so the model can later be replaced without changing the rest of the system. |
| FR-13 | The initial implementation may use Google Gemini as the live LLM provider. |
| FR-14 | The prototype shall also provide a Demo/Mock mode so it remains executable without an API key or paid LLM access. |
| FR-15 | Each generated submission shall be evaluated using predefined functional tests. |
| FR-16 | A functionally incorrect submission shall not contribute to the observed defect profile. |
| FR-17 | Functional-test failure information shall be captured and made available to the next Generation Specification. |
| FR-18 | Functionally correct submissions shall be analysed using explicit defect-detection rules. |
| FR-19 | Detected defects shall be aggregated across the valid batch to create an Observed Synthetic Defect Profile. |
| FR-20 | The system shall compare the Observed Synthetic Defect Profile with the Context-Aware Target Profile. |
| FR-21 | The system shall calculate the discrepancy for each defect using \(e_d=T_d-O_d\). |
| FR-22 | The user shall be able to configure or view the accepted discrepancy tolerance. |
| FR-23 | The system shall identify each category as underrepresented, overrepresented, or within tolerance. |
| FR-24 | If all relevant discrepancies are within tolerance, the current batch shall be accepted as Synthetic Python Submissions. |
| FR-25 | If one or more discrepancies exceed tolerance, the system shall produce calibration actions for the corresponding generation constraints. |
| FR-26 | Calibration shall revise the Generation Specification before another generation cycle. |
| FR-27 | The system shall retain iteration history so the user can inspect changes across generation cycles. |

---

## 5. Initial Programming Tasks

For the PoC, implement **two small CS1 tasks** so the context-aware behaviour can be demonstrated.

### Task A — Conditional Validation

Example purpose:

```text
Write a function that accepts a score and returns
the corresponding grade classification.
```

Suggested task contexts:

```text
branching
boolean_condition
validation
```

### Task B — List Processing

Example purpose:

```text
Write a function that processes a list of numbers
and returns a required summary or filtered result.
```

Suggested task contexts:

```text
iteration
list_processing
collection
```

The two tasks should share task-independent characteristics but have different applicable task-dependent characteristics.

---

## 6. Initial Defect Categories

For the prototype, implement only a small set of defects that can be detected reproducibly.

Recommended initial set:

| Defect | Classification | Initial detection approach |
|---|---|---|
| Non-descriptive naming | Task-independent | AST identifier inspection using a documented naming heuristic |
| Unused variable | Task-independent | Compare assigned identifiers against subsequent references |
| Redundant Boolean comparison | Task-dependent | Detect forms such as `x == True` or `x == False` |
| Excessive nesting | Task-dependent | Calculate AST control-structure nesting depth |

The implementation must keep defect detection modular so new categories can be added later.

Do not claim that these demonstration classifications or prevalence values are empirical research findings.

---

## 7. Demonstration Profiles

Store demonstration profiles separately from application logic.

Example:

```json
{
  "task_independent": {
    "non_descriptive_naming": 0.40,
    "unused_variable": 0.25
  }
}
```

Example task-dependent profile:

```json
{
  "conditional_validation": {
    "redundant_boolean_comparison": 0.30,
    "excessive_nesting": 0.20
  }
}
```

The Streamlit interface must clearly display:

> **Demonstration Profile**

so these values cannot be mistaken for results derived from authentic student data.

---

## 8. Generation Specification

The Generation Specification should be generated programmatically rather than stored as one large hard-coded prompt.

It should contain three conceptual sections:

```text
1. Functional Task Requirements

2. Task-Independent Characteristics

3. Applicable Task-Dependent Characteristics
```

Example:

```text
PROGRAMMING TASK

Write a Python function that classifies a numerical
score according to the provided requirements.


FUNCTIONAL REQUIREMENTS

The function must satisfy all specified test cases.


TASK-INDEPENDENT CHARACTERISTICS

Generate the solution in a manner consistent with
selected novice-code characteristics.

Target characteristics:
- non-descriptive naming
- unused variable


TASK-DEPENDENT CHARACTERISTICS

For this conditional-validation task, incorporate
the selected contextual characteristics where appropriate:

- redundant Boolean comparison
- excessive conditional nesting


IMPORTANT

The program must remain functionally correct.
```

The constructed specification must be visible in the prototype.

---

## 9. Functional Validation

Generated Python code must **not be executed directly with unrestricted `exec()` inside the Streamlit process**.

Use a separate Python subprocess with:

```text
execution timeout
temporary working directory
predefined test cases
captured stdout/stderr
```

The validation result should include:

```text
PASS / FAIL
tests passed
tests failed
failure message
execution timeout/error if applicable
```

For the PoC, production-grade sandboxing is not required, but the implementation should clearly isolate execution from the main Streamlit process.

---

## 10. Defect Detection Architecture

Create one detector per defect.

Suggested interface:

```python
class DefectDetector:
    def detect(self, source_code: str) -> bool:
        ...
```

Or equivalent function-based modules:

```python
detect_poor_naming(code)
detect_unused_variables(code)
detect_redundant_boolean(code)
detect_excessive_nesting(code)
```

A submission result should resemble:

```python
{
    "submission_id": 1,
    "functionally_correct": True,
    "defects": {
        "non_descriptive_naming": True,
        "unused_variable": False,
        "redundant_boolean_comparison": True,
        "excessive_nesting": False
    }
}
```

---

## 11. Profile Aggregation

For each defect:

\[
O_d=
\frac{\text{valid submissions containing defect }d}
{\text{number of functionally valid submissions}}
\]

Example:

```text
Functionally correct submissions = 10

Poor naming detected = 4

Observed prevalence = 4 / 10 = 0.40
```

Failed submissions must not be included in this denominator.

---

## 12. Calibration Logic

For each defect:

\[
e_d=T_d-O_d
\]

Interpretation:

```text
e > tolerance
    Underrepresented

e < -tolerance
    Overrepresented

|e| <= tolerance
    Within tolerance
```

Example default tolerance:

```text
±0.10
```

The system should initially use simple transparent calibration actions:

```text
UNDERREPRESENTED
→ strengthen generation constraint

OVERREPRESENTED
→ reduce generation constraint

WITHIN TOLERANCE
→ maintain generation constraint
```

Calibration must create a revised Generation Specification.

The target value must remain unchanged.

---

## 13. Streamlit Interface Requirements

Implement a **single-page application with four sections or tabs**:

| UI Area | Content |
|---|---|
| Configure | Programming task, number of submissions, target profiles, tolerance |
| Generate | Context-aware profile and constructed Generation Specification |
| Results | Generated code, functional status, detected defects |
| Analyse & Calibrate | Target/observed profile comparison, discrepancy, calibration actions |

This layout should produce the screenshots required for the assignment.

---

## 14. Figure 4 Prototype Screen

The configuration screen should display:

```text
Programming Task

Task Context

Task-Independent Defect Profile

Applicable Task-Dependent Defect Profile

Context-Aware Target Profile

Number of submissions

Tolerance

Generate button
```

This becomes:

> **Figure 4. Prototype interface for task selection, context-aware target-profile configuration, and synthetic-code generation.**

---

## 15. Figure 5 Prototype Screen

The results screen should contain:

```text
Generation Results — Iteration 1

Generated: 10
Functionally Correct: 8
Failed: 2
```

Then:

| Submission | Functional Status | Detected Defects |
|---|---|---|
| #01 | PASS | Non-descriptive naming |
| #02 | PASS | Redundant Boolean |
| #03 | FAIL | Not analysed |
| #04 | PASS | Unused variable |

The user should be able to expand a row to inspect its generated Python code.

This becomes:

> **Figure 5. Prototype output showing functional-validation results and detected defect characteristics.**

---

## 16. Figure 6 Prototype Screen

The Analyse & Calibrate screen should show a grouped bar chart:

```text
Target vs Observed Defect Profile
```

and a comparison table:

| Defect | Target | Observed | Difference | Status | Action |
|---|---:|---:|---:|---|---|
| Naming | 40% | 20% | +20 pp | Under | Increase |
| Unused variable | 25% | 20% | +5 pp | Within | Maintain |
| Redundant Boolean | 30% | 10% | +20 pp | Under | Increase |

The screen should also display:

```text
Tolerance: ±10 percentage points
```

and:

```text
Apply Calibration and Regenerate
```

This becomes:

> **Figure 6. Target–observed defect-profile comparison and resulting calibration actions.**

---

## 17. Recommended Project Structure

```text
synthetic-novice-code-prototype/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
│
├── data/
│   ├── tasks.json
│   └── demonstration_profiles.json
│
├── models/
│   ├── task.py
│   ├── profile.py
│   └── results.py
│
├── services/
│   ├── context_analyser.py
│   ├── profile_composer.py
│   ├── prompt_builder.py
│   ├── llm_provider.py
│   ├── validator.py
│   ├── profile_analyser.py
│   └── calibrator.py
│
├── detectors/
│   ├── naming.py
│   ├── unused_variable.py
│   ├── redundant_boolean.py
│   └── nesting.py
│
├── tests/
│   ├── test_context_analyser.py
│   ├── test_profile_composer.py
│   ├── test_detectors.py
│   └── test_calibrator.py
│
└── generated/
```

---

## 18. Non-Functional Requirements

| Requirement | Meaning |
|---|---|
| Modular | LLM, testing, defect detection, and calibration should be separate modules |
| Reproducible | Demonstration tasks and profiles stored in version-controlled files |
| Transparent | Target, observed values, discrepancy, and calibration actions visible |
| Provider-independent | LLM adapter prevents business logic depending directly on Gemini |
| Executable without API | Demo mode must allow the complete UI workflow without external services |
| Safe enough for PoC | Generated code executed in isolated subprocess with timeout |
| Extensible | New tasks and defect detectors can be added without changing core workflow |
| Academically traceable | UI terminology should match the terminology used in the paper |

---

## 19. `requirements.txt`

Start with:

```txt
streamlit
pandas
matplotlib
pytest
python-dotenv
google-genai
ruff
```

Most AST functionality comes from Python's standard library, so there is no separate AST dependency.

---

## 20. Definition of Done

For A4, the prototype is complete when the following scenario works from beginning to end:

```text
1. User selects a programming task.

2. System identifies its task context.

3. System displays:
   - task-independent profile
   - applicable task-dependent profile
   - context-aware target profile

4. System constructs and displays a Generation Specification.

5. User generates a batch of submissions.

6. System performs functional validation.

7. Valid submissions undergo defect detection.

8. System constructs an observed defect profile.

9. Target and observed profiles are visualised.

10. System determines whether each discrepancy is within tolerance.

11. System proposes calibration actions.

12. User can apply calibration and initiate another iteration.

13. Figures 4, 5, and 6 can be captured directly from the running Streamlit application.
```

## 21. Recommended Codex Instruction

Use the following instruction when starting implementation in VS Code:

> Read `REQUIREMENTS.md` completely before coding. Implement the prototype incrementally and do not change the specified system workflow or terminology. Start with the Streamlit UI and Demo mode. Do not integrate the live LLM until the context-profile, generation-specification, validation-result, defect-analysis, and calibration workflow works end-to-end with deterministic demonstration data.
