# Mathematical verification of the iterative calibration framework

## Scope, notation, and classification

This verifies the **current CLI experiment path**, using the [implementation audit](calibration_implementation_audit.md), executable source, focused tests, and aggregate historical JSONL records. No generation experiment or authentic submission was executed. Historical records use schema 1 or 2; the current writer emits schema 3. Consequently, recorded actions can be checked arithmetically against the current comparison function, while current LLM convergence is **Not Verifiable from Logs** ([`experiment.py` lines 277–309](../services/generation/experiment.py#L277)).

Let $t\in\{T1,T2,T3\}$ denote a prototype task, $k\geq1$ a **batch-level calibration iteration**, and $d$ an **individual defect identifier**, not a defect category. Let $D_t=\operatorname{keys}(T_t)$ be the keys of the target profile supplied for task $t$; the code does not derive this set afresh from the eligibility matrix during generation. Let $S_{t,k}$ be the retained submission slots in iteration $k$, $V_{t,k}=\{s\in S_{t,k}:\operatorname{validation}(s)=\mathrm{PASS}\}$, $n_{t,k}=|V_{t,k}|$, and $x_{t,d,k}=\sum_{s\in V_{t,k}}\mathbf1\{d\text{ detected in }s\}$. Prevalence, discrepancies, and margins are fractions on the 0–1 scale; multiplication by 100 is only a presentation choice. The assignment planner validates targets in $[0,1]$, and empirical target values are loaded as floats ([`assignment.py` lines 45–50](../services/generation/assignment.py#L45); [`run_generation_experiment.py` lines 17–35](../scripts/run_generation_experiment.py#L17)).

The labels below mean: **Exact implementation** is a direct expression of the code; **Faithful mathematical abstraction** summarizes a multi-step implementation without adding behavior; **Conceptual proposal only** is an idea not used as the claimed control rule; **Incorrect or unsupported** conflicts with, or is not established by, this implementation.

## 1. Observed prevalence and signed discrepancy

**Exact implementation.** For each target-profile key,

$$
O_{t,d,k}=\begin{cases}x_{t,d,k}/n_{t,k},&n_{t,k}>0,\\0,&n_{t,k}=0,\end{cases}
\qquad e_{t,d,k}=T_{t,d}-O_{t,d,k}.
$$

`observed_profile` filters on functional `PASS` and divides detected counts by the number of such submissions; it returns zero when there are none. `compare_profiles` performs the subtraction in this exact order ([`analysis.py` lines 8–18, 21–32, 75–77](../services/generation/analysis.py#L8); [`workflow.py` lines 475–485](../services/generation/workflow.py#L475)). Thus $e>0$ denotes an observed deficit and $e<0$ an observed excess, subject to the decision margin below. A passing submission enters the denominator even if assigned styles, category requirements, or unassigned-style checks fail; a failing one does not ([`workflow.py` lines 381–403, 451–485](../services/generation/workflow.py#L381)). **Exact implementation** applies to the proposed signed equation after correcting $d$ to mean a defect, rather than a category.

**Exact implementation.** The same `config.target_profile` is passed to every iteration, and `run_iteration` copies it into its result. Calibration does not mutate this empirical target ([`experiment.py` lines 382–389](../services/generation/experiment.py#L382); [`workflow.py` lines 487–504](../services/generation/workflow.py#L487)). The CLI loads task-specific empirical values and optional target standard errors from a profile file ([`run_generation_experiment.py` lines 17–35, 78–98](../scripts/run_generation_experiment.py#L17)).

## 2. Distributional metric and its denominator

**Exact implementation for reporting and ranking, not acceptance.** The reported mean absolute profile error is

$$
\operatorname{MAE}_{t,k}=\begin{cases}
\displaystyle\frac{1}{|D_t|}\sum_{d\in D_t}|T_{t,d}-O_{t,d,k}|,&|D_t|>0,\\
0,&|D_t|=0.
\end{cases}
$$

The denominator is the **number of target-profile defect keys**, not the batch size, the number of passing submissions, the number of categories, or necessarily every defect marked eligible in configuration. Each included key has equal weight. The per-defect $O$ denominator is separately $n_{t,k}$. The code calculates MAE over comparison rows and also reports root mean square profile error and the fraction of rows within tolerance. An unaccepted, quality-eligible candidate is ranked lexicographically with **lower MAE first**, followed by higher within-tolerance rate and quality measures ([`experiment.py` lines 142–169, 256–274, 418–422](../services/generation/experiment.py#L142)). **Conceptual proposal only** if MAE is presented as the sole distributional comparison or the success criterion: per-defect margins determine actions and acceptance ([`analysis.py` lines 89–125](../services/generation/analysis.py#L89); [`types.py` lines 95–97](../models/types.py#L95)).

**Part of the exact metric definition.** Every key in `target_profile` enters MAE and per-defect comparison, including a zero-prevalence key. For $T_{t,d}=0$, its target-relative tolerance floor is zero, but with $n>0$ the sampling margin can be positive. If $n=0$, the implementation sets every observed prevalence to zero and uses only the target-relative floor for comparison; it does not mark the batch statistically indeterminate. An empty target mapping yields MAE $0$, no comparison rows, and vacuous `accepted=True` ([`analysis.py` lines 11–17, 39–40, 75–108](../services/generation/analysis.py#L11); [`experiment.py` lines 158–165, 258–265](../services/generation/experiment.py#L158); [`types.py` lines 95–97](../models/types.py#L95)).

**Faithful mathematical abstraction, conditional on profile construction.** Upstream profile export omits defects with unavailable prevalence, and catalog metadata supplies task applicability. The CLI reads those exported task-specific target keys. Yet `run_iteration` does not call `eligibility_for` or validate every target key against `applicable_tasks`; an externally supplied inapplicable key can still be planned and compared. Therefore $D_t$ should be defined as **the supplied target keys**, not unconditionally as “all eligible defects” ([`target_profile.py` lines 25–58](../services/research/target_profile.py#L25); [`eligibility.py` lines 17–46](../services/research/eligibility.py#L17); [`configuration.py` lines 76–83](../services/generation/configuration.py#L76); [`workflow.py` lines 252–270, 477–485](../services/generation/workflow.py#L252)). The same mapping of keys is passed to every iteration of one `run_experiment`; therefore the MAE denominator is fixed within that experiment ([`experiment.py` lines 382–389](../services/generation/experiment.py#L382)).

## 3. Exact per-defect tolerance decision

The CLI supplies a **single global relative tolerance** $\tau$ (`--tolerance`, default 0.10); it does not supply a defect-specific $\tau_d$ ([`run_generation_experiment.py` lines 50–59, 83–98](../scripts/run_generation_experiment.py#L50); [`experiment.py` lines 95–112](../services/generation/experiment.py#L95)). For $n=n_{t,k}>0$, set $\hat p=x_{t,d,k}/n$, $z=1.96$, and calculate the Wilson endpoints as the code does:

$$
c=\frac{\hat p+z^2/(2n)}{1+z^2/n},\qquad
r=\frac{z\sqrt{\hat p(1-\hat p)/n+z^2/(4n^2)}}{1+z^2/n},\qquad
L=\max(0,c-r),\quad U=\min(1,c+r).
$$

Let $s^T_{t,d}$ be the target standard error loaded from the empirical profile, defaulting to zero when absent. The observed standard-error proxy is $s^O_{t,d,k}=(U-L)/(2z)$. The **exact implemented decision margin** is

$$
m_{t,d,k}=\begin{cases}
\max\!\left(|T_{t,d}|\tau,\;z\sqrt{(s^T_{t,d})^2+(s^O_{t,d,k})^2}\right),&n_{t,k}>0,\\
|T_{t,d}|\tau,&n_{t,k}=0.
\end{cases}
$$

The margin and action are calculated for **each** target key, using the same configured $\tau$, but with potentially different target values, standard errors, and observed counts ([`analysis.py` lines 5, 35–52, 71–108](../services/generation/analysis.py#L5)). The target standard error is computed by the CLI as empirical task-level standard deviation divided by the square root of the eligible-task count when that count exceeds one ([`run_generation_experiment.py` lines 28–35](../scripts/run_generation_experiment.py#L28)). No inverse-variance or other weights are applied to MAE.

**Exact implementation.** The decision is

$$
a_{t,d,k}=\begin{cases}
\mathrm{Increase},&e_{t,d,k}>m_{t,d,k}\quad(\mathrm{Underrepresented}),\\
\mathrm{Reduce},&e_{t,d,k}<-m_{t,d,k}\quad(\mathrm{Overrepresented}),\\
\mathrm{Maintain},&|e_{t,d,k}|\leq m_{t,d,k}\quad(\mathrm{Within\ tolerance}).
\end{cases}
$$

The proposed `|e_{t,d,k}|\leq\tau_d` is **Incorrect or unsupported** as the prototype rule: $\tau$ is global and relative to target prevalence; when valid submissions exist, the larger uncertainty-based margin can control the decision. At equality, a row is within tolerance. The iteration's profile acceptance condition is **all** comparison rows within their margins, rather than an MAE cutoff ([`analysis.py` lines 89–125](../services/generation/analysis.py#L89); [`types.py` lines 95–97](../models/types.py#L95)). No minimum $n_{t,k}$ is required before this test ([`workflow.py` lines 475–485](../services/generation/workflow.py#L475); [`experiment.py` lines 400–432](../services/generation/experiment.py#L400)).

## 4. Implemented calibration update

**Exact implementation.** After an iteration that does not end the iterative run, `calibration_constraints` overwrites the next constraint mapping from the **latest** comparison rows:

$$
C_{t,d,k+1}=f(a_{t,d,k}),\qquad
f(\mathrm{Increase})=\text{“strengthen the generation constraint”},\quad
f(\mathrm{Reduce})=\text{“reduce the generation constraint”},\quad
f(\mathrm{Maintain})=\text{“maintain the generation constraint”}.
$$

Initial constraints are empty. This is a replacement mapping keyed by defect, not a numerical update of the previous constraint by error magnitude. There is **no gain, step size, clipping rule, or probability adjustment** ([`calibrator.py` lines 4–12](../services/generation/calibrator.py#L4); [`experiment.py` lines 375–389, 424–426](../services/generation/experiment.py#L375)). A formula such as $C_{k+1,d}=C_{k,d}+\eta e_{k,d}$ is **Conceptual proposal only** and must not be attributed to the prototype.

**Faithful mathematical abstraction.** In the next batch, $C_{t,d,k+1}$ has two effects: it is inserted into the guided per-submission prompt's `CALIBRATION ADJUSTMENTS` text, and its strengthen/maintain/reduce label affects the sort priority used to select one mandatory defect from each task category. The remainder of that sort includes configured reliable order, target prevalence, and name, then cycles by submission ID. This priority change can displace another defect from a mandatory assignment. Repairs retain the assigned styles but their revised specification does not directly repeat the calibration section ([`prompt_builder.py` lines 48–60, 101–105, 223–230](../services/generation/prompt_builder.py#L48); [`workflow.py` lines 106–180, 183–218, 285–299, 431–441](../services/generation/workflow.py#L106)).

**Exact implementation.** Quota planning still uses the original $T_{t,d}$: for batch size $B$, its expected count is $BT_{t,d}$ and its integer quota is stochastically rounded with a seed that changes with $k$. The iteration can therefore receive different planned assignments without any change in defect-assignment probabilities or the target. The mandatory overlay can add assignments beyond those quotas and beyond the planner's three-defect cap ([`assignment.py` lines 23–65, 70–115](../services/generation/assignment.py#L23); [`workflow.py` lines 183–218, 264–292](../services/generation/workflow.py#L183)). There is no general pairwise incompatibility solver. Prompt guidance tells the model to include assigned styles and avoid unassigned ones, so a `reduce` action can coexist with a mandatory assigned style; the code does not mathematically reconcile that conflict ([`prompt_builder.py` lines 154–193, 223–245](../services/generation/prompt_builder.py#L154)).

## 5. Stopping, rejection, and selection

**Faithful mathematical abstraction of the stopping test.** For the iterative condition, define

$$
\operatorname{profile\_accepted}_{t,k}
=\bigwedge_{d\in D_t}\left(|e_{t,d,k}|\leq m_{t,d,k}\right).
$$

If this predicate first holds at iteration $k$, the run stops and selects $k$. Otherwise it stops after $K_{\max}$ batches and selects the best eligible batch. For an unaccepted candidate $k>1$, eligibility for best-result selection requires $Q_{t,k,j}\geq Q_{t,1,j}$ for **each** of the four quality dimensions $j$ listed below. This componentwise gate is separate from profile acceptance.

**Exact implementation.** In the iterative condition, each $k\in\{1,\dots,K_{\max}\}$ produces a full `run_iteration` result unless generation aborts. If every defect row is within its margin, `iteration.accepted` is true, that iteration is selected immediately, and the stop reason is `within_tolerance`. If no iteration meets that profile criterion, the loop runs through $K_{\max}$ and records `maximum_iterations`; that is **termination without demonstrated convergence**. The baseline and task-aware non-adaptive conditions run only once and record `single_iteration` ([`types.py` lines 95–97](../models/types.py#L95); [`experiment.py` lines 364–369, 400–432](../services/generation/experiment.py#L364)). The default $K_{\max}=3$ is set in the CLI and `ExperimentConfig`, and invalid values below one are rejected ([`run_generation_experiment.py` lines 57–59](../scripts/run_generation_experiment.py#L57); [`experiment.py` lines 104–106, 350–357](../services/generation/experiment.py#L104)).

**Exact implementation.** A later **unaccepted** candidate is eligible to replace the selected result only if four batch-quality metrics are each no lower than the **first** iteration's value: functional pass rate, task-independent coverage, task-dependent coverage, and category-requirement rate. Among eligible candidates, the lexicographic key is lower MAE, then higher within-tolerance rate, category-requirement rate, dependent coverage, independent coverage, and functional pass rate. The initial result always remains an available fallback. A failed non-regression check prevents **selection**, not further iterations: even an unselected candidate supplies the next constraints. An accepted candidate bypasses this quality gate and stops immediately ([`calibrator.py` lines 15–37](../services/generation/calibrator.py#L15); [`experiment.py` lines 256–274, 405–426](../services/generation/experiment.py#L256)). Thus “tolerance **and** functional-quality threshold” is **Incorrect or unsupported** as an exact stopping rule: functional testing filters the prevalence denominator, but there is no separate minimum pass-rate or category-coverage threshold for profile acceptance ([`analytics.py` lines 66–103](../services/generation/analytics.py#L66); [`types.py` lines 95–97](../models/types.py#L95)).

**Exact implementation.** Each submission slot allows one initial generation attempt and at most `max_repair_attempts` revisions (CLI default two). Perfect functional and style compliance ends retries early; otherwise the best generated attempt is retained, possibly a functional failure. An empty provider response, invalid configuration, impossible planner capacity, detector error, or cancellation aborts rather than producing a smaller accepted batch. Zero passing submissions do **not** abort comparison ([`workflow.py` lines 317–465, 475–485](../services/generation/workflow.py#L317); [`experiment.py` lines 350–362](../services/generation/experiment.py#L350)).

## 6. Historical log verification

The following are **recorded schema-2** iterative runs, repetition 1, from three separate files. Each selected run contains three iterations, `max_iterations=3`, global `tolerance=0.10`, and 20 functionally passing submissions per iteration. Targets, observations, discrepancies, and decision margins are **proportions** rounded to four decimal places for display; actions were checked using unrounded records. “Continue” means the row belongs to a nonfinal iteration of a run with at least one defect still out of tolerance. The final stop reason applies to the **whole profile**, not solely the example defect.

| Task and representative defect | Iteration | Target $T$ | Observed $O$ | Discrepancy $T-O$ | Margin $m$ | Calibration action | Stop/continue reason |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| T1 · inappropriate_formatting | 1 | 0.5501 | 0.2000 | +0.3501 | 0.1970 | Increase | Continue; profile not within tolerance |
| T1 · inappropriate_formatting | 2 | 0.5501 | 0.2000 | +0.3501 | 0.1970 | Increase | Continue; profile not within tolerance |
| T1 · inappropriate_formatting | 3 | 0.5501 | 0.1500 | +0.4001 | 0.1855 | Increase | Maximum iterations; iteration 1 selected |
| T2 · duplicate_expression | 1 | 0.1463 | 0.5000 | −0.3537 | 0.2202 | Reduce | Continue; profile not within tolerance |
| T2 · duplicate_expression | 2 | 0.1463 | 0.4000 | −0.2537 | 0.2171 | Reduce | Continue; profile not within tolerance |
| T2 · duplicate_expression | 3 | 0.1463 | 0.4500 | −0.3037 | 0.2194 | Reduce | Maximum iterations; iteration 1 selected |
| T3 · magic_number | 1 | 0.4093 | 0.0000 | +0.4093 | 0.3022 | Increase | Continue; profile not within tolerance |
| T3 · magic_number | 2 | 0.4093 | 0.0000 | +0.4093 | 0.3022 | Increase | Continue; profile not within tolerance |
| T3 · magic_number | 3 | 0.4093 | 0.0000 | +0.4093 | 0.3022 | Increase | Maximum iterations; iteration 3 selected |

The T1 sequence is from [`experiment-log-300926161821.jsonl` line 1](../research-notes/synthetic-generation-experiments/experiment-log-300926161821.jsonl#L1), T2 from [`experiment-log-300926173214.jsonl` line 1](../research-notes/synthetic-generation-experiments/experiment-log-300926173214.jsonl#L1), and T3 from [`experiment-log-300926190447.jsonl` line 1](../research-notes/synthetic-generation-experiments/experiment-log-300926190447.jsonl#L1). Their MAE denominators are respectively 12, 8, and 6 target-profile defect keys. In T2, later MAE fell from about 0.1480 to 0.1119, but independent/dependent/category coverage fell below the initial iteration, explaining why an unaccepted later batch could not displace iteration 1 under the **current** non-regression selection rule. In T3, the selected iteration 3 had lower MAE than iteration 1 while meeting that quality gate. These are arithmetic/selection checks on historical summaries, not evidence that current LLM calibration converges.

**Exact arithmetic check against current comparison code; historical observation only.** For all 78 defect rows across these nine recorded iterations, recomputing `compare_profiles` from the logged target, observed value, count, valid denominator, tolerance, and target standard errors yielded **zero action mismatches**. The logs store comparison summaries, not generated source and prompts, so actual per-submission defect detection and causal effects of prompt changes are **Not Verifiable from Logs**. No schema-3 experiment record was present in the inspected log set. A separate historical T2 schema-2 record shows an early `within_tolerance` stop at iteration 1 with 5/5 functional passes but category-requirement rate 0.20; it illustrates that logged profile convergence and full category compliance are different measures ([`experiment-log-300926155342.jsonl` line 1](../research-notes/synthetic-generation-experiments/experiment-log-300926155342.jsonl#L1)).

## Equation verdicts for Section 5.4

| Proposed or publishable statement | Verdict | Required wording |
| --- | --- | --- |
| $e_{t,d,k}=T_{t,d}-O_{t,d,k}$ | **Exact implementation** | $d$ is an individual target-profile defect; $O$ uses functionally passing submissions and is zero for an empty passing set. |
| $\operatorname{MAE}_{t,k}=|D_t|^{-1}\sum_{d\in D_t}|e_{t,d,k}|$ | **Exact implementation** when `|D_t|>0`; **Faithful mathematical abstraction** for the full experiment | $D_t$ is the supplied target-profile key set. MAE reports/ranks candidates; it is not the convergence test. Define MAE as zero when $D_t$ is empty. |
| Equal weighting of all *eligible* defects | **Incorrect or unsupported** as stated | Equal weighting applies to all **supplied target keys**. Generation does not independently enforce target-key eligibility. |
| `|e_{t,d,k}|<=tau[d]` with fixed per-defect absolute tolerances | **Incorrect or unsupported** | Use the global relative $\tau$ and the defect-specific, iteration-specific margin $m_{t,d,k}$ above. |
| All defect rows within margin ⇒ successful profile acceptance | **Exact implementation** | State this as profile acceptance, not as proof of universal functional correctness or full category compliance. |
| $C_{t,d,k+1}=f(a_{t,d,k})$ with literal action strings | **Exact implementation** | State both prompt insertion and mandatory-category ordering effects. |
| A proportional update to defect probabilities/weights | **Conceptual proposal only** | No numerical feedback gain or adjusted sampling probability is implemented. |
| Stop on tolerance or maximum iterations | **Faithful mathematical abstraction** | Add single-iteration controls, selection/non-regression details, repair and abort behavior; maximum iterations does not imply convergence. |

### Verification method

The report uses code inspection and the prior audit for implementation claims. For the log check, only aggregate JSONL comparison rows and quality metrics were read, and `compare_profiles` was invoked on those numeric fields. No stored or authentic student source was read or executed, and no model request was made.
