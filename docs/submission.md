# Submission and reproducibility evidence

Required Parts 1 and 2 are completed and runtime-verified on [GitHub main](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/main). The optional adaptive extension is published on [bonus/adaptive-multi-agent](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/bonus/adaptive-multi-agent). The [root README](../README.md) is the primary project and setup guide.

## Requirement coverage

| Requirement | Implementation / evidence |
| --- | --- |
| Original scheduled, parallel pipeline | [Airflow DAG](../dags/dc_bike_weather.py), [successful runs](../screenshots/01_airflow_dag_success.png), [DAG graph](../screenshots/02_airflow_graph.png) |
| Two real sources, separate cleaning and merge | UCI day.csv and Open-Meteo ERA5; [source verification](verification/sources.md), [merge validation](../submission/part1/validation/merged.json) |
| Database persistence and rerun idempotence | Separate application PostgreSQL, 731 unique dates, 3,292,679 rentals; [SQL report](../submission/part1/postgres_report.md) |
| Database-fed analysis | [Three EDA charts and summaries](../submission/part1/README.md) |
| Original agent graph and bounded loop | [Part 2 graph](../src/bike_demand_ml/graph.py), [execution](../screenshots/06_langgraph_live_execution.png), [retry](../screenshots/07_langgraph_conditional_retry.png) |
| Appropriate evaluation | [Ridge/Dummy report](verification/phase-c/runs/ml_main_01/report.json), [held-out metrics](../screenshots/08_regression_evaluation.png) |
| Container setup and instructions | [Compose](../compose.yaml), Dockerfiles, pinned requirements, [operating guide](running.md) |
| Optional adaptive coordination and evaluation | [Bonus guide](../bonus/README.md), [27-case results](verification/bonus/runtime/evaluations/bonus_suite_01/results.json), [screenshots](../screenshots/README.md) |
| Strict two-native-classroom-baseline comparison | Native seven-task DAG and original LangGraph executed separately; same-problem regression ports remain adaptations. [Details](../bonus/COMPARISON.md) |

## Recorded verification

The original recorded combined suite passed **102 tests**: 39 pipeline unit tests, 19 Part 2 tests, 43 Bonus tests including read-only PostgreSQL integration, and one real Airflow DAG-import test. [Bonus verification](verification/bonus/review/README.md) links the original JUnit/log records. These counts describe the saved test run, not automatic reruns when reading this document.

Frozen evidence includes:

- [Part 1 runtime results](verification/phase-b/runtime-results.json), SQL/idempotence reports, source/merge validation and actual EDA PNGs.
- [Part 2 run ml_main_01](verification/phase-c/runs/ml_main_01/report.json): database provenance, features/splits, trials, routes, metrics, held-out predictions and selected model.
- [Bonus run bonus_main_01](verification/bonus/runtime/runs/bonus_main_01/report.json): compiled topology, real events, agent metrics and final predictions.
- [Regression suite](verification/bonus/runtime/evaluations/bonus_suite_01/summary.json), [native classification probes](verification/bonus/runtime/classroom/classroom_probe_01/summary.json), and [independent artifact audit](verification/bonus/review/evaluation-audit.json).
- [Current documentation checks](verification/documentation-checks.json): recorded screenshot-rename cleanup, syntax and preservation.
- [Actual native classroom reproduction](verification/bonus/native-classroom/results.md): native task/run metrics, fresh regression tests, UI evidence and qualifications.

Historical reports retain their original filenames, timestamps and scope. Their recorded Git status/file counts are snapshots, not current repository inventories.

## Repository contents

Source lives in src/, dags/, agents/, dashboard/ and sql/. requirements/, scripts/ and tests/ supply pinned dependencies and reproducibility checks. bonus/ and compose.bonus.yaml contain the optional extension. assignment/ records the supplied rubric and clarifications. docs/, submission/ and screenshots/ contain documentation and genuine evidence.

The [final audit and explicit inventory](verification/final-bonus/README.md) record current verification and submission files relative to the verified main baseline. The older [317-file Parts 1-2 manifest](../submission/commit-files.txt) remains a historical publication inventory.

Only nineteen reviewed PNGs are allowlisted. Local .env files, credentials, virtual environments, caches, raw downloads, regenerated artifacts, Docker storage/database dumps and build products remain ignored. The small frozen selected_model.joblib is retained as hashed reproducibility evidence; other generated models are excluded.

The six reviewed native captures are linked in the [screenshot index](../screenshots/README.md). Image 19 shows execution records; final native metrics are in 18 and 20. Optional extra agent-event images are not required.

## Findings and limits

Selected Ridge alpha=10 achieved held-out MAE 904.71, RMSE 1,202.36 and R2 0.5231. One of 184 predictions is negative and remains unclipped. This is a retrospective observed-weather backtest; demand trends, one temporal split and weather day-boundary differences limit generalization.

Adaptive and both regression-port normal runs have equal test metrics. Expected-failure passes are distinct from completion. Designed fault cases, unsaved candidate validation predictions, adapted regression ports and no-key-only native execution constrain Bonus conclusions. Native classification stages share their 400 evaluation rows.
