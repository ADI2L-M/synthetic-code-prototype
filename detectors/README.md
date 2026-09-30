# Detector-module navigation

The detector layer is responsible for source-code defect detection only. It
must not decide whether an authentic submission is functionally correct.

## Current modules

| Module | Responsibility |
|---|---|
| `core/parsing.py` | Shared AST parsing and source-location helpers |
| `core/registry.py` | Detector registry and dispatch |
| `legacy/naming.py` | Existing naming heuristic |
| `legacy/nesting.py` | Existing nesting heuristic |
| `legacy/redundant_boolean.py` | Existing boolean-comparison heuristic |
| `legacy/unused_variable.py` | Existing unused-variable heuristic |
| `research/redundant_comparison.py` | Research-stage redundant-comparison detector |

The existing legacy heuristics are retained under `legacy/`, while the
research detectors are rebuilt against the authoritative defect definitions.
New research detectors should be added as focused modules, covered by
`tests/unit/detectors/`, and registered only after their definition-level
tests pass.

## Detection boundary

1. Functional tests in `services/` filter the authentic submissions.
2. Detector modules inspect only the functionally correct source code.
3. Prevalence services aggregate task-level detector results.

Authoritative defect IDs and rules are in
`research-notes/defect_definitions_yaml/` and
`research-notes/programming-defects.md`.
