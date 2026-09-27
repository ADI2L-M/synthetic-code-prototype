You are implementing the empirical defect-detection and validation component of a Design Science Research project on task-aware generation of synthetic novice Python code.

PROJECT OBJECTIVE
The broader research investigates whether synthetic CS1 Python code can reproduce the defect tendencies found in authentic novice submissions. The current task is to build a rigorous analysis pipeline that:

1. detects predefined code-quality defects in authentic CS1 submissions;
2. validates those detections;
3. determines whether each detection is eligible for use under the relevant programming task;
4. computes defect prevalence first at individual-task level and then at task-family level;
5. provides the empirical defect profiles that will later be used as targets for synthetic-code generation.

IMPORTANT RESEARCH PRINCIPLE
Do not invent, broaden, narrow, rename, or reinterpret the defect definitions or task definitions without evidence from the supplied project files.

The supplied files are authoritative.

You must understand each definition as a whole rather than treating individual YAML/JSON fields as isolated keywords.

A task family represents the computational structure, programming situation, and defect opportunities expressed by the complete target-task definition.

A defect definition represents the exact behaviour that should be detected.

If a definition is ambiguous or cannot be implemented reliably, report the ambiguity rather than silently making up a rule.

INPUTS

The project will provide:

1. Defect definition file(s)
   - Contains the authoritative definitions of all defects.
   - Use these definitions to design detection rules.

2. Target task definitions:
   - T1_conditional_logic.yaml
   - T2_list_processing.yaml
   - T3_numeric_iteration.yaml

3. Task-family grouping:
   - cs1_regeneration_task_groups.json

4. Authentic CS1 Python submissions
   - Each submission should be associated with its original Lab and Question identifier.

5. Where available, task requirements and/or original functional tests.

TARGET TASKS

T1: Temperature Classification
Family: conditional_logic

The task represents decision-making through comparison expressions and conditional branching. The complete YAML definition, including task-dependent defects, functional requirements, and characteristics, must be used when determining relevant opportunities.

T2: Total Scores
Family: list_processing

The task represents collection processing through iteration and progressive result/state accumulation. Its complete YAML definition must be used when assessing similarity and defect opportunities.

T3: Sum to N
Family: numeric_iteration

The task represents numeric iteration over a known progression/range while maintaining numeric state or accumulation. Its complete YAML definition must be used when determining relevant opportunities.

Do not reduce these definitions to simple labels such as "has an if", "uses a list", or "contains a loop".

==================================================
CORE ARCHITECTURAL PRINCIPLE
==================================================

Keep the following concerns separate:

A. RAW DEFECT DETECTION
Determine whether a structural/style pattern exists in the source code.

B. TASK ELIGIBILITY / OPPORTUNITY
Determine whether that detection should legitimately contribute to prevalence for the specific task.

C. FUNCTIONAL CORRECTNESS
Determine whether the submission satisfies the functional requirements.

D. PREVALENCE ANALYSIS
Aggregate validated binary defect observations.

A detector must not suppress a pattern merely because the task requires it.

For example:

detected = true
eligible = false

must be a valid result.

This distinction is necessary because a structure may physically exist in the code but be required by the programming task, meaning that it should not be interpreted as a novice defect for that task.

==================================================
PHASE 1 — INSPECT AND FORMALISE DEFECT DEFINITIONS
==================================================

Before implementing detectors:

1. Read every supplied defect definition.
2. Create a machine-oriented specification for every defect.
3. For each defect document:

   - defect name
   - authoritative definition
   - relevant AST/source-code structures
   - positive detection condition
   - explicit exclusions
   - likely false-positive situations
   - whether task context is required
   - whether source text/token analysis is needed
   - whether AST analysis is sufficient
   - expected output information

Do not implement a detector until its specification is documented.

Create a file such as:

config/defect_specifications.json

or an equivalent structured representation.

If the supplied definitions do not support a particular implementation decision, mark it as:

"requires_review": true

and explain why.

==================================================
PHASE 2 — DETECTOR ARCHITECTURE
==================================================

Use Python's ast module as the primary structural-analysis mechanism.

Use tokenize and/or controlled source-text analysis only when a defect depends on information that AST does not preserve, such as formatting.

Avoid regular expressions for structural Python analysis unless there is a clear justified reason.

Implement one detector per defect.

Recommended structure:

src/
    detectors/
        base.py
        formatting.py
        naming.py
        conditionals.py
        iteration.py
        collections.py
        assignments.py
        ...

Each detector should expose a consistent interface.

For example:

def detect(source_code, tree, context) -> DetectionResult:
    ...

DetectionResult should include at least:

{
    "defect": "...",
    "present": true,
    "count": 2,
    "locations": [
        {"line": 10, "column": 4},
        {"line": 17, "column": 8}
    ],
    "evidence": [...],
    "notes": null
}

The "present" field is the value later used for prevalence.

"count" is retained as secondary information.

Do not equate defect frequency with prevalence.

If one submission contains a defect five times:

count = 5

but:

present = true

and the submission contributes only one positive observation to prevalence.

==================================================
PHASE 3 — TASK CONTEXT AND OPPORTUNITY MODEL
==================================================

Create a task-context layer.

Each submission should be analysed with information such as:

{
    "lab": 12,
    "question": 2,
    "task_family": "T2",
    "task_requirements": "...",
    "required_constructs": [...],
    "restricted_constructs": [...],
    "relevant_defects": [...]
}

Create an explicit defect-opportunity/confound matrix.

For every task-defect combination classify it as:

1. eligible
   The task provides a legitimate opportunity for the defect.

2. not_applicable
   The programming situation does not meaningfully expose the defect.

3. instruction_confounded
   The task explicitly requires a structure that would otherwise be classified as that defect.

Do not classify task eligibility simply by checking whether a construct occurs in student solutions.

Eligibility must be determined from:
- the task requirements;
- the complete target-family concept;
- the defect definition.

Example:

If a task explicitly requires a while loop, and "while_as_for" is being measured as a defect, that task may be instruction-confounded for that defect.

Likewise, if a task explicitly requires nested conditions and "nested_if" is treated as a defect, that task may be instruction-confounded for that defect.

Store this separately from raw detection.

==================================================
PHASE 4 — UNIT TESTS FOR EVERY DETECTOR
==================================================

Use pytest.

Every defect detector must have:

1. clear positive cases;
2. clear negative cases;
3. important boundary cases;
4. cases representing likely false positives;
5. where relevant, task-context cases.

Example pattern:

def test_augmentable_assignment_positive():
    ...

def test_augmentable_assignment_negative():
    ...

def test_augmentable_assignment_different_variable():
    ...

def test_augmentable_assignment_task_context():
    ...

Positive and negative examples must come from the supplied defect definition.

Do not invent semantic extensions to make testing easier.

The tests should verify:
- present;
- count;
- reported source locations where practical.

==================================================
PHASE 5 — VALIDATION AGAINST AUTHENTIC CODE
==================================================

Unit tests validate implementation behaviour but are not sufficient evidence of real-world detector accuracy.

Support manual validation using authentic student submissions.

Create functionality that allows a researcher to manually label a validation sample.

Recommended fields:

submission_id
task_id
defect
manual_label
detector_label

Use:

1 = defect present
0 = defect absent

Then calculate, per defect:

true positives
false positives
true negatives
false negatives
precision
recall
F1

Use:

Precision = TP / (TP + FP)

Recall = TP / (TP + FN)

F1 = 2 * Precision * Recall / (Precision + Recall)

Handle zero denominators safely.

Produce a validation report such as:

outputs/detector_validation.csv

with columns similar to:

defect
TP
FP
TN
FN
precision
recall
f1
validation_n

Do not invent an acceptable threshold unless the research specification provides one.

Instead, expose the results so the researcher can evaluate detector reliability.

==================================================
PHASE 6 — FUNCTIONAL CORRECTNESS
==================================================

Keep functional testing completely separate from defect detection.

For authentic lab submissions:

- use original course tests when available;
- if submissions are already known to be accepted/correct, preserve that status;
- do not invent missing original tests and claim they represent the course marking process.

For the three regeneration target tasks, derive functional tests from the supplied YAML functional requirements.

Test:
- normal cases;
- boundary cases;
- empty/minimal cases where permitted;
- return type;
- prohibited printing where relevant;
- explicitly restricted implementation features.

For example:

T2 forbids built-in sum().

T3 forbids:
- built-in sum();
- direct mathematical summation formula.

Implementation-constraint testing should use AST analysis where appropriate.

A generated program is considered suitable for synthetic-profile analysis only when:

functional_correctness == true

AND

constraint_compliance == true

Defect presence must NOT automatically make the program functionally incorrect.

The research specifically concerns functionally correct code that may contain stylistic or structural defects.

==================================================
PHASE 7 — SUBMISSION ANALYSIS OUTPUT
==================================================

Produce one structured record per analysed submission.

Recommended format:

{
    "submission_id": "S001",
    "task_id": "Lab_12_Q2",
    "task_family": "T2",
    "parse_success": true,
    "functional_correct": true,
    "constraint_compliant": true,
    "defects": {
        "augmentable_assignment": {
            "present": true,
            "count": 1,
            "eligibility": "eligible",
            "locations": [7]
        },
        "redundant_indexing": {
            "present": false,
            "count": 0,
            "eligibility": "eligible",
            "locations": []
        }
    }
}

Preserve raw detections even when eligibility is not_applicable or instruction_confounded.

==================================================
PHASE 8 — PREVALENCE CALCULATION
==================================================

Use one student submission for one programming task as the unit of analysis.

For task q and defect d:

task prevalence:

p(q,d) =
number of valid eligible submissions for q containing d
/
number of valid eligible submissions for q

Count each submission only once for prevalence, regardless of the number of instances of the defect.

Calculate prevalence for every authentic task first.

Do NOT immediately pool all submissions across a family.

Then compute family-level prevalence from task-level prevalence.

Primary family estimate:

P(F,d) =
mean of p(q,d) across eligible tasks q in family F

This provides equal weighting to each programming task and prevents tasks with larger submission counts from dominating the empirical target.

Also calculate pooled prevalence as a secondary statistic:

pooled(F,d) =
total affected eligible submissions
/
total eligible submissions

Report both, clearly distinguishing them.

For every family-defect result output:

task_family
defect
eligible_task_count
valid_submission_count
task_mean_prevalence
pooled_prevalence
minimum_task_prevalence
maximum_task_prevalence
standard_deviation

Where appropriate, preserve the individual task-level prevalences so they can be inspected.

==================================================
PHASE 9 — TASK-INDEPENDENT AND TASK-DEPENDENT PROFILES
==================================================

Do not assume that a defect is empirically task-independent simply because it is currently labelled that way in a design file.

First calculate its prevalence separately across T1, T2, and T3.

Preserve:

P(d | T1)
P(d | T2)
P(d | T3)

This evidence will later support evaluation of whether its prevalence is sufficiently stable across task families.

For task-dependent defects, calculate the profile within the relevant family using only eligible tasks.

Do not calculate zeros for tasks where the defect is not applicable.

A non-applicable observation is missing/not eligible, not a negative observation.

==================================================
PHASE 10 — TARGET PROFILE EXPORT
==================================================

Create machine-readable empirical profiles suitable for the later prompt-calibration prototype.

Example:

{
    "task_id": "T2",
    "task_family": "list_processing",
    "profile_source": "authentic_cs1_submissions",
    "task_independent": {
        "poor_variable_name": {
            "prevalence": 0.27,
            "eligible_tasks": 18
        }
    },
    "task_dependent": {
        "redundant_indexing": {
            "prevalence": 0.31,
            "eligible_tasks": 14
        },
        "augmentable_assignment": {
            "prevalence": 0.37,
            "eligible_tasks": 19
        }
    }
}

Do not hard-code example values.

All values must be derived from authentic data.

==================================================
ENGINEERING REQUIREMENTS
==================================================

Use:
- Python 3.11+ where possible
- ast
- tokenize where necessary
- pytest
- pathlib
- dataclasses or typed models where useful
- type hints
- docstrings
- clear modular structure

Prefer standard-library functionality unless an external dependency provides a clear advantage.

Avoid unnecessary dependencies.

Use deterministic processing.

Do not execute untrusted student code during defect detection.

Functional testing of student/generated code must be isolated from the analysis process and should use an appropriate timeout/sandbox strategy.

Never use eval() or exec() directly in the main analysis process for arbitrary submissions.

Handle:
- syntax errors;
- empty files;
- malformed submissions;
- encoding issues;
- unexpected AST forms;

without crashing the entire dataset analysis.

Log failures and continue processing.

==================================================
REPRODUCIBILITY
==================================================

All analysis decisions must be traceable.

Record:
- detector version;
- defect-definition version;
- task-family configuration;
- date/run identifier;
- excluded submissions and reasons;
- instruction-confounded task-defect combinations.

Do not silently discard data.

==================================================
IMPLEMENTATION ORDER
==================================================

Do not attempt to build everything at once.

Proceed in this order:

1. inspect repository and input files;
2. document understanding of file structure;
3. formalise defect specifications;
4. design project architecture;
5. implement common AST infrastructure;
6. implement one defect detector at a time;
7. add unit tests immediately for each detector;
8. implement task opportunity/confound model;
9. implement submission-level analysis;
10. implement validation metrics;
11. implement functional testing for T1/T2/T3;
12. implement prevalence calculation;
13. export empirical target profiles;
14. run the complete test suite;
15. produce a short technical report explaining:
    - architecture;
    - assumptions;
    - unresolved ambiguities;
    - tests passed;
    - remaining limitations.

==================================================
IMPORTANT BEHAVIOURAL RULES
==================================================

Before making a design decision, inspect the relevant source definition.

Do not redefine the research concepts from generic programming knowledge when the project files already provide their meaning.

Reason from the complete supplied knowledge.

Do not infer that two tasks belong to the same family merely because they share syntax.

Do not infer that a defect is applicable merely because its syntax could theoretically occur.

Do not treat absence of opportunity as absence of a defect.

Do not treat multiple occurrences in one submission as multiple prevalence observations.

Do not modify research definitions merely to make implementation easier.

When something is genuinely ambiguous, stop at that specific ambiguity, document it clearly, propose possible interpretations, and wait for researcher confirmation before encoding the decision.

Start by inspecting the supplied files and summarising your understanding of:
1. the defect definitions;
2. T1, T2, and T3;
3. the authentic submission structure;
4. the grouped lab-task configuration.

Do not begin detector implementation until that understanding has been established.