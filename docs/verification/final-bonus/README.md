# Final Bonus submission audit

The adaptive extension and both native classroom references have real execution evidence. Required Parts 1–2 remain independently verified. This audit checks saved results and the current services without retraining models or triggering DAGs.

## Requirement coverage

| Requirement | Verified evidence |
| --- | --- |
| Original scheduled pipeline | dc_bike_weather_daily: two concurrent source branches, daily 06:00 America/New_York, nine tasks; 731 dates loaded idempotently into separate application PostgreSQL |
| Database-fed analysis | Three genuine EDA charts and summaries in [Part 1 evidence](../../../submission/part1/README.md) |
| Original Part 2 graph | PostgreSQL loader, temporal split, Dummy comparison, conditional retry and final selected Ridge: MAE 904.71, RMSE 1202.36, R2 0.5231 |
| Adaptive specialists | Coordinator, data/feature/model/evaluation/recovery roles; bounded attempts and explicit terminal failures |
| Evaluation suite | Nine declared scenarios across three policies; 27 saved executions independently audited for contracts, routes, budgets, selection, timings and final metrics |
| Fixed classroom baseline | Actual solution_baseline_prep / native_prep_01; all seven tasks successful, validation F1 0.050000 |
| Simple classroom baseline | Original native_simple_02; three no-key cycles, best validation F1 0.056604, held-out F1 0.059113 and accuracy 0.5225; target 0.8 unmet |
| Application screenshots | [19 reviewed captures](../../../screenshots/README.md), including all six native images 15–20 |

The two optional extra agent/node-event images are not required. Image 19 shows execution records and per-cycle F1; final metric cards are in 18 and 20. Image 16 shows topology; native success/run identity are supported jointly by 15 and 17.

## Fresh verification

The [test summary](test-summary.json) records **128 final passing tests, no final failures or skips**:

- 39 pipeline unit tests, 19 Part 2 tests and 42 Bonus synthetic tests.
- One real Airflow DAG-import test and one actual read-only PostgreSQL integration test.
- 16 native isolation/evidence tests and 10 reviewer safeguard counterexamples.

[JUnit and logs](./) retain actual outputs. An initial integration diagnostic targeted the artifact-only Bonus dashboard, which intentionally has no database credentials; the same unchanged test passed in the database-connected dashboard. Both records remain. A non-failing upstream LangChain deprecation warning is retained.

The [final reviewer report](audit-final/) covers fresh read-only production and native Airflow API checks, 27 saved-run audits, Python parsing, GitHub-compatible relative file links, strict screenshot/secret ignore rules, private exact-credential scanning, Compose validation and preservation. The [native viewer check](viewer-current.json) verifies actual metric cards, compiled graph and five data tables. [Source pins](source-pins-check.json) verify all 14 unchanged instructor/data files.

The reviewer now permits only explicitly named documentation changes instead of requiring the README to begin with an obsolete historical version. Source, tests, dependencies, Docker logic, production data and frozen evidence remain protected. Counterexample tests reject source changes, changed/missing evidence, timestamp alterations, substituted renamed images and extra screenshot exemptions.

Genuine terminal spaces/blank lines are preserved through narrowly scoped Git attributes. No historical log or score was edited to make whitespace checks pass. Earlier diagnostic whitespace findings remain alongside the [corrected full check](untracked-whitespace-corrected.json).

## Submission inventory

The final report directory contains:

- staging-files.txt: complete Bonus additions/changes relative to verified main, including already committed Bonus files.
- pending-staging-files.txt: existing files needing a new index update.
- staging-deletions.txt: the old tracked policy-chart filename to remove as part of its byte-identical rename.
- file-status.json and changed-files.txt: exact per-file inventory and working-tree changes.

These explicit inventories exclude local environments, passwords, downloaded references, caches, volumes and scratch reports. The old 317-file main manifest and earlier Bonus inventories remain historical records; use this audit's manifests for the final submission.

## Interpretation limits

Native classification and Bike Demand regression are different problems; F1 is not ranked against RMSE. Native DAG validation and graph holdout share the same 400 rows, dependency/preprocessing protocols differ, convergence warnings remain and the LLM-enabled path was not tested. The regression ports are simplified adaptations, not exact classroom replicas. Normal-case predictions match across all three regression policies, so no predictive superiority is claimed. Designed fault cases and single-run timings do not establish general reliability.

The Ridge backtest uses observed weather and retains one negative prediction without clipping. Candidate validation predictions were not saved for independent recalculation; final regression predictions were saved and audited. See the [qualified comparison](../../../bonus/COMPARISON.md).
