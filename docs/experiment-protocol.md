# Controlled experiment protocol

## Fixed inputs

For a comparison, keep the following constant across conditions:

- prototype task contract and functional evaluator;
- target profile and target standard errors;
- model, context length, and temperature;
- batch size, tolerance, repetitions, and repair budget;
- detector registry and validity rules.

The experiment runner uses a matched repetition seed namespace for the initial
baseline and task-aware batches. This reduces variation from the random draw
when comparing prompting treatments.

## Conditions

### Non-adaptive baseline

The model receives the task description, functional requirements, and
functional test cases. It receives no defect names, examples, assignments,
category requirements, prevalence values, or calibration actions.

### Task-aware non-adaptive

The model receives the task contract plus the applicable defect catalogue,
per-submission assigned styles, construction hints, detector signatures,
short examples, task-specific valid patterns, and the requirement to include
at least one task-independent and one task-dependent defect. Target percentages
are used by the assignment planner and evaluator but are not shown in the
prompt.

### Task-aware iterative

Iteration 1 uses the task-aware non-adaptive prompt. Later iterations append
Increase, Reduce, or Maintain actions derived from the latest comparison. The
runner evaluates all configured iterations unless a batch reaches tolerance,
then retains the best eligible batch subject to the initial quality floor.

## Per-submission evaluation

Each submission receives up to one initial generation and two repair attempts.
The best attempt is selected by functional validity and unresolved repair
requirements. Only functionally valid submissions are passed to the research
detector registry and included in prevalence denominators.

## Primary recorded metrics

- functional pass rate;
- valid submission count;
- task-independent and task-dependent coverage;
- category-requirement rate;
- mean absolute profile error;
- root mean square profile error;
- within-tolerance rate;
- selected iteration and stop reason;
- defects that remain out of tolerance or unobserved.

## Reproducibility record

Every controlled experiment should preserve its experiment ID, task, model,
temperature, context length, batch size, tolerance, repetitions, iteration and
repair limits, target profile, target standard errors, conditions, seed
namespace, prompt/configuration version, detector version, Git commit, and
runtime environment.
