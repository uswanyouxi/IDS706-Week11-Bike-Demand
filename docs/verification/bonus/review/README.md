# Bonus verification evidence

The adaptive PostgreSQL-fed workflow, 27 isolated evaluation executions and native reference probes have recorded runtime results. This index separates verified behavior from baseline-comparison limitations.

## Requirement coverage

| Requirement | Result |
| --- | --- |
| Original specialists and graph | Compiled coordinator/specialist topology with real node events and role metrics |
| Adaptive routing and model selection | Intermediate diagnostics, validation metrics and explicit destination reasons |
| Bounded retries and terminal failures | Scenario-specific fault types, exact load/fit/recovery budgets and failure reports |
| Intermediate/final quality | Snapshot contract/hash, temporal split, allowed features, selected identity and independently recomputed held-out metrics |
| Explicit evaluation cases | Nine cases x three policies, each with input, expected outcome, criteria and threshold; 27/27 expected-behavior passes |
| Native classroom comparison | Native Airflow DAG and completed LangGraph reproduced; regression ports are still adaptations. [Native evidence](../native-classroom/results.md) |
| Application evidence | [Seven genuine Bonus captures](../screenshot-guide.md); policy-level chart accurately labeled |

## Results and tests

The selected Ridge alpha=10 achieved MAE **904.71**, RMSE **1,202.36** and R2 **0.5231** on 184 held-out dates. One prediction was negative. All three normal regression policies have equal scores; adaptivity did not improve predictive performance.

The original recorded combined tests passed **102**, with zero failures or skips:

| Test group | Passed | Record |
| --- | ---: | --- |
| Bonus and Part 2 | 62 (43 + 19) | [JUnit](submission-bonus-ml.xml), [log](submission-bonus-ml.log) |
| Pipeline unit | 39 | [JUnit](submission-pipeline.xml), [log](submission-pipeline.log) |
| Real DAG import | 1 | [JUnit](submission-dag.xml), [log](submission-dag.log) |

Logs retain non-failing upstream LangChain and temporary-harness marker warnings. Earlier diagnostic logs retain their original scope and timestamps.

## Reproducibility records

- [Actual adaptive run](../runtime/runs/bonus_main_01/report.json), events and predictions in the same directory.
- [Regression suite results](../runtime/evaluations/bonus_suite_01/results.json) and [summary](../runtime/evaluations/bonus_suite_01/summary.json).
- [Native classification probes](../runtime/classroom/classroom_probe_01/summary.json).
- [Independent audit of 27 saved executions](evaluation-audit.json).
- [Recorded read-only production snapshot](production-readonly.json).
- [Historical combined checks](checks.json) and [evidence integrity](submission-preparation.md).
- [Recorded documentation validation](../../documentation-checks.json).
- [New native classroom execution/verification](../native-classroom/results.md).
- [Final audit and current submission inventory](../../final-bonus/README.md).

The independent audit reads saved topology, events, snapshots and predictions. It checks nonempty ordered traces, route/reason consistency, exact scenario counters, feature/model identity, role timings and recomputed selected/Dummy final metrics. Every applicable check must pass (score 1.0; numerical tolerance 1e-10). Counterexample tests reject altered records.

Candidate validation predictions were not saved, so logged validation scores cannot be independently recomputed without refitting. Nine designed fault cases are not a general reliability estimate. Single-run graph timings exclude startup and do not establish native-classroom speed superiority. See [the comparison](../../../../bonus/COMPARISON.md) for native classification results and the remaining comparability limits.

The updated reviewer permits explicit final-documentation edits while continuing to protect original source, tests, dependencies, database contents and frozen evidence. New audit reports are stored separately in the [final audit](../../final-bonus/README.md); historical check outputs are never overwritten.
