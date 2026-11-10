# Native classroom baseline verification

The missing native Airflow execution was reproduced in a separate Docker project, ids706-classroom-native-v1. Original instructor task/node/model code at a294145ea9aa4225908ce701c06160c33213335d remained byte-identical. No Bike Demand workflow or production model was rerun.

## Observed execution

| Item | Actual result |
| --- | --- |
| Native Airflow | 2.10.4 / Python 3.11, LocalExecutor |
| DAG / run | solution_baseline_prep / native_prep_01 |
| Run interval | 2026-11-10 00:52:23.599141 to 00:52:54.075809 UTC (November 9 evening, America/New_York) |
| Task states | All seven success; genuine attempt=1 logs retained |
| Source data | 1,000 customers and 10,000 transactions from the pinned classroom CSVs |
| Merge / publication | 10,000 merged rows; 2,000 published rows, including 60 fraud cases |
| Native DAG metric | Validation F1 0.050000; 1,600 training / 400 validation rows |
| Native DAG held-out / accuracy | Not emitted by the original DAG; no values invented |
| Native graph / run | Completed original solution/langgraph/graph.py / native_simple_02 |
| Native graph behavior | Three cycles; two memory/context revisions; zero observed fit repairs; one final holdout stage |
| Native graph selection | LogisticRegression C=0.25, max_iter=300; best validation F1 0.056604 |
| Native graph held-out | F1 0.059113; accuracy 0.5225; 400 rows |
| Quality target | 0.8 validation F1 not met; native stop_reason=finalize |
| LLM behavior | Original documented heuristic fallback; used_llm=False throughout; worker network disabled |

Publication SHA-256: **0d41b894cba0ee45619075f629c242ef2b4c2e1c5e928464737de2fc305f9e68**. The actual graph consumed these exact published bytes. Both native workflows emitted iteration-limit convergence warnings; original parameters were not changed to improve the reported outcome.

## Real seven-task states

| Task | State |
| --- | --- |
| validate_customers | success |
| validate_transactions | success |
| merge_csvs | success |
| make_subset | success |
| profile_light | success |
| train_baseline | success |
| publish_merged | success |

[Actual DAG report](runtime/native_classroom_01/artifacts/native_prep_01/report.json), [task states](runtime/native_classroom_01/artifacts/native_prep_01/task-states.json), [XCom returns](runtime/native_classroom_01/artifacts/native_prep_01/xcom.json), and [native graph report](runtime/native_classroom_01/artifacts/native_simple_02/report.json) provide the recorded values. The task log directory retains the actual seven attempt=1 logs.

## Qualification and limitations

The native DAG uses numeric-only preprocessing and an 80/20 split. The graph uses its own preprocessing and 60/20/20 selection protocol, then refits on the non-holdout 80%. A [derived split check](runtime/native_classroom_01/native-split-comparison.json), using both actual dependency environments without model fitting, found **400/400 shared evaluation indices**: DAG validation and graph holdout are the same population. No independent evaluation cohorts are claimed.

DAG and graph package versions differ and timings cover different work. Native graph wall time was 0.6311 seconds excluding import/container startup; the DAG's 30.48 seconds includes scheduling and tasks. These are not a speed ranking. Classification scores are actual emitted values, checked against records; classifiers were not refit merely to independently recompute their scores.

The [comparison](../../../../bonus/COMPARISON.md) separates native fraud classification from the preserved Bike Demand regression adaptations. A [paired regression check](runtime/native_classroom_01/paired-regression-prediction-check.json) aligned 184 saved test dates and found exactly identical predictions for adaptive, fixed_port and simple_port. F1 cannot be ranked against RMSE. Full Bonus credit and exact same-problem equivalence are not implied.

## Isolation and environment adaptations

- Separate metadata database, bridge network, credentials and four new named volumes; no production volume/network attached.
- Reused the existing ML image and the already-built native Airflow image. No image rebuild was needed for execution.
- One native LocalExecutor slot, one parser, 300-second reparse intervals and --skip-serve-logs; task logs remain in a new shared volume.
- Native webserver stayed off during training. The new scheduler was stopped after its manual run for serial ML/tests; the original project scheduler remains running.
- Windows RAM gate remained **2.5 GiB**. Low-memory attempts were refused before training. Native Windows memory queries avoid an extra PowerShell process.
- New evidence root has group-only write permissions (2775), supporting UID 50000 and UID 10001 without world-write.
- Instructor DAG, LangGraph and loop_runtime files have no source patches. Exact pins, attribution, image identity, versions and resource observations are recorded.

The original student stubs were not executed. solution_baseline_and_trigger retains an explicit stub trigger and is not claimed as a working Airflow-to-graph integration.

## Tests and corrected harness failures

- **100 original regression tests passed**: 39 pipeline, 19 Part 2 and 42 Bonus synthetic tests, with one upstream warning.
- **One real original Airflow DAG-import test passed**.
- **16 new lightweight isolation/evidence tests passed**.
- The original Bonus read-only database integration function passed its two real snapshots.
- Native artifact consistency validation passed, and Streamlit AppTest verified actual metrics, five data tables and compiled graph with no application exceptions.
- Live native Airflow API confirmed native_prep_01 success and all seven successful tasks; the native viewer health endpoint returned ok.

The first new native graph observer attempt, native_simple_01, failed **before fitting** because its import wrapper omitted module registration for annotation resolution. Its error remains in the export. Registering the module fixed only the wrapper; native_simple_02 is the single completed native graph experiment.

An initial AppTest worker lacked the viewer's read-only regression-summary mount. The missing table caused an assertion failure; matching the real viewer mounts fixed it. Both failed and successful diagnostic logs remain. Native DAG/model outcomes were not replaced or rerun to improve scores.

See [fresh regression JUnit](runtime/native_classroom_01/verification-artifacts/tests/bike-regression.xml), [real DAG JUnit](runtime/native_classroom_01/original-dag-regression.xml), [read-only integration](runtime/native_classroom_01/original-readonly-db-integration.json), [viewer AppTest](runtime/native_classroom_01/verification-artifacts/viewer-apptest.json) and [native artifact validation](runtime/native_classroom_01/native-verification.json).

## Submission evidence

All nineteen genuine screenshots are indexed in the [screenshot documentation](../../../../screenshots/README.md), including six native captures. The [evidence guide](capture-guide.md) states exactly what each native image shows. The optional extra agent/node-event captures are not required.

Frozen earlier reports retain their original timestamps and pre-reproduction scope. The [final audit](../../final-bonus/README.md) supersedes the old reviewer's obsolete documentation rules without changing source/evidence preservation requirements.
