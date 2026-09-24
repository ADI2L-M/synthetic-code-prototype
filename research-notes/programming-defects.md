# Task-Independent Defects

| Defect                                    | Operational interpretation                                                                                                  | Why task-independent                                             |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Inappropriate whitespace / formatting** | Irregular spacing around operators, commas, parentheses, indentation, etc.                                                  | Can occur in conditional, list, or iteration code                |
| **One-letter / poor variable name**       | Using names such as `x`, `a`, or `t` where a descriptive name would be clearer                                              | Naming behaviour is not tied to a specific algorithmic construct |
| **Built-in name**                         | Using Python built-in identifiers such as `list`, `sum`, or `str` as variable names                                         | Can occur in any task                                            |
| **Magic number / unexplained literal**    | Using numeric constants directly in code without making their meaning explicit where a named constant would improve clarity | Not inherently tied to conditionals, lists, or loops             |

# Task-Dependent Defects
| Task                      | Defect                             | Why it is task-dependent                                                              |
| ------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------- |
| **T1: Conditional Logic** | Redundant if-else                  | Requires conditional branching                                                        |
|                           | Redundant comparison               | Usually arises when Boolean conditions are explicitly compared with `True` or `False` |
|                           | Redundant not                      | Depends on Boolean-condition formulation                                              |
|                           | Duplicate if                       | Requires multiple conditional branches                                                |
|                           | Else-if instead of `elif`          | Requires chained conditional logic                                                    |
|                           | Nested if                          | Requires branching that can be unnecessarily nested                                   |
|                           | Redundant elif                     | Requires mutually exclusive conditional branches                                      |
|                           | Empty if                           | Requires an unnecessary conditional branch                                            |
| **T2: List Processing**   | For-loop with redundant indexing   | Requires traversal of a sequence/list using indices                                   |
|                           | Misleading iterator name           | Can arise when `i` or `j` is used for elements instead of indices                     |
|                           | Duplicate expression               | Can arise from repeatedly accessing the same list expression                          |
|                           | Augmentable assignment             | Can arise naturally when accumulating the list total                                  |
| **T3: Numeric Iteration** | While-as-for                       | Requires iteration where the number of iterations is known in advance                 |
|                           | Augmentable assignment             | Common when updating a counter or accumulated total                                   |
|                           | Redundant for                      | Requires an unnecessary or effectively single-iteration loop                          |
|                           | Unnecessary loop/counter structure | Depends specifically on how the iterative solution is constructed                     |
