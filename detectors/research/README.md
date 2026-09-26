# Research detector catalogue

`registry.py` exposes the 18 defect names from
`research-notes/defect_definitions_yaml/`. Each detector returns a
`DetectionResult` containing raw presence, instance count, locations, and
evidence. Eligibility is applied later by `services/research/eligibility.py`;
a detector never suppresses a structurally present defect because a task marks
it not applicable.

## Detector modules

| Module | Defects |
|---|---|
| `conditionals.py` | `redundant_if_else`, `redundant_not`, `duplicate_if`, `else_if`, `nested_if`, `redundant_elif`, `empty_if` |
| `redundant_comparison.py` | `redundant_comparison` |
| `collections.py` | `redundant_indexing`, `misleading_iterator_name`, `duplicate_expression` |
| `iteration.py` | `while_as_for`, `redundant_for` |
| `assignments.py` | `augmentable_assignment` |
| `formatting.py` | `inappropriate_formatting` |
| `magic.py` | `magic_number` |
| `names.py` | `one_letter_name`, `built_in_name` |

## Conservative implementation decisions

- `duplicate_if`, `nested_if`, `redundant_elif`, and
  `augmentable_assignment` only report simple structurally safe cases. They
  retain evidence describing the rewrite rationale because the catalog marks
  these rules for review.
- `duplicate_expression` uses the configured weighted-complexity threshold of
  8, a 20-line local region, and only AST expressions proven pure or using the
  `len`/`abs` allow-list.
- `while_as_for` requires a simple comparison, a constant monotonic update on
  every path, and no `break`, `return`, or `continue` control escape.
- `inappropriate_formatting` uses `tokenize` plus line inspection for only the
  fixed formatting rules listed in `config/defect_specifications.json`.
- `magic_number` excludes `0` and `1` and reports non-structural literals in
  comparisons or arithmetic logic. `-1` is exempt only when it has a clear
  index/sentinel role.

These are operational detector rules, not replacements for manual validation.
The validation workflow should sample detections by defect and record
precision, recall, and F1 before prevalence results are treated as empirical
findings.
