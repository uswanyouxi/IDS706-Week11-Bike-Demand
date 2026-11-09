# Optional Part 3 — Adaptive Bike-Demand Specialists

Branch: bonus/adaptive-multi-agent, created from verified main d3a4465. Required Parts 1–2 remain unchanged. This is an original deterministic LangGraph system, with no paid API dependency.

## Original adaptive graph

Data loader → Coordinator → Data Quality → Coordinator → Feature Analysis → Coordinator → Model Selection → Coordinator → Training → Coordinator → Validation Evaluation → Coordinator.

The coordinator can select Feature Refinement, another Model Selection/Training attempt, bounded Failure Recovery, Final Test, or Failure Reporting from actual structured intermediate state. Recovery returns to the failing stage's safe entry. Final Test only proceeds to Reporting; test metrics never return to selection.

- Data Quality verifies the complete Part 1 contract, dates and persisted snapshot hash.
- Feature Analysis computes training-only target associations, constant features and redundant weather variables, builds chronological features/splits, and fits a Dummy reference.
- Model Selection chooses Ridge or a small seeded single-thread forest using those diagnostics and prior validation results.
- Feature Refinement removes redundant max/min temperature inputs when a measured train/validation error gap warrants it.
- Training/Evaluation record candidate identity, features, actual train/validation MAE/RMSE/R² and gap.
- Recovery supports transient PostgreSQL OperationalError/timeouts and declared transient fit interruption; contract/unsupported-model/permission failures abort.
- Coordinator records a reason for every destination; attempts <=3, DB loads <=2, recoveries <=2, graph recursion <=100.
- Reporting saves actual metrics, provenance, graph topology, events and predictions in a new immutable run folder.

The default loader reads application PostgreSQL in a repeatable-read READ ONLY transaction. Evaluation faults use isolated copies/injected exceptions, never production SQL mutations. Features exclude cnt, casual/registered, IDs and UCI weather; 365/182/184 chronological partitions and training-only fitted transforms match the established problem. Selection uses validation only. Best model and Dummy refit on 547 rows and receive one final 184-day test stage.

## Classroom baseline review and limits

Pinned classroom reference: Kedar-V/automl-research-lab, branch refactor/lab-solution-layout, commit a294145ea9aa4225908ce701c06160c33213335d.

- Student lab DAG and graph are scaffolds. Filled references are solution/airflow/dags/solution_baseline_prep.py and solution/langgraph/graph.py plus loop_runtime.py.
- Native Airflow prep merges customers/transactions, samples rows, fits a fixed LogisticRegression classifier, and publishes CSV. Its schedule is manual. Native simple loop uses scientist/hypothesis/engineer/judge/memory/context/holdout agents, F1 and random splits, with documented no-key heuristics.
- These native classification scores are not comparable to daily cnt regression. The small documented CLI prep helper is separately reproducible; running it does not establish an actual classroom Airflow DAG execution.
- The evaluation suite additionally runs explicitly labeled regression workflow ports: fixed_port (single fixed Ridge operation with bounded infrastructure retries) and simple_port (profile/plan/train/judge-style loop with predefined model choices, without adaptive feature refinement or infrastructure recovery).
- Ports use the same input, features, temporal split, faults and metrics as the adaptive system. They are not represented as exact classroom implementations. The original classroom Airflow DAG has not been run; strict native baseline comparison remains a stated limitation until genuinely verified.

No classroom source is copied into the new graph. Unmodified references live only in ignored artifacts/classroom-reference and are checksum-verified by bonus/fetch_classroom.py. Source pins are in classroom_sources.json.

## Containers and commands

Base compose.yaml and Dockerfiles remain untouched. compose.bonus.yaml only adds opt-in services using the already-tested ids706-ml:1.0.0 image, read-only source mounts and the existing artifact volume. Runner: 1 CPU/1 GiB cap; separate multipage dashboard: 0.5 CPU/512 MiB cap. The existing Part 2 page stays available unchanged in navigation and at localhost:8501.

After explicit runtime approval, with existing Part 1 services healthy:

~~~powershell
py -3.11 bonus/fetch_classroom.py
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus config --quiet
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus up -d --no-deps bonus-dashboard
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner /bin/sh -c 'umask 0002; exec python -m bike_demand_bonus.cli run --id bonus_main_01'
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner /bin/sh -c 'umask 0002; exec python -m bike_demand_bonus.cli evaluate --id bonus_suite_01'
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner /bin/sh -c 'umask 0002; exec python -m bike_demand_bonus.cli classroom --id classroom_probe_01'
~~~

Do not reuse existing IDs; output folders refuse overwrite. All suite executions run serially. No original Airflow service is recreated, reconfigured or triggered.

Read-only integration/unit checks after approval:

~~~powershell
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps -e BONUS_DB_INTEGRATION=1 bonus-runner python -m pytest /opt/project/tests/bonus -c /opt/project/pytest.ini -p no:cacheprovider -q -ra
~~~

Open http://localhost:8502, Optional Part 3. The wrapper also includes the original Verified Part 2 page. Views read real graph/event/report files; they cannot initiate training or mutate SQL.

## Evaluation suite and evidence

Nine declared cases × three policies: normal, duplicate date, missing weather, transient DB, permanent DB, transient fit, exhausted fit retries, weak model, unsupported model. Every case records input, expected behavior, criteria, threshold, observed result and pass/fail. Rejection of unsafe inputs is an expected pass, distinct from task completion.

Suite outputs measure intermediate contracts/features/selection, real final metrics/report completeness, route legality, attempts/recovery, completion and expected-behavior rates, and measured wall/CPU time. RSS is a Linux worker-lifetime high-water value, not a per-run isolated memory peak. Single runs/timing do not justify speed-superiority claims.

The initial controlled runtime was verified: real PostgreSQL-fed bonus_main_01 completed, all 27 declared evaluation executions passed expectations, native reference probes ran, and tests at that stage passed 26 bonus + 39 pipeline + 19 original ML + 1 DAG import = 85, with zero skips/failures. The later independent review passes 102 tests, including the new audit counterexamples. The original model/pipeline logic is unchanged. [The actual report](../docs/verification/bonus/status.md), [comparison](COMPARISON.md), and [screenshot guide](../docs/verification/bonus/screenshot-guide.md) distinguish measured results from the remaining strict native-Airflow baseline gap.

Adaptive selected Ridge alpha=10 with held-out MAE 904.71, RMSE 1202.36 and R2 0.5231, identical to both normal-case regression ports. It explored three candidates and one feature refinement; it did not improve predictive performance. One final prediction was negative and remains unclipped. Native classroom classification F1 is not mixed with these regression metrics. The simplified simple_port omits the native graph's one-pass fit repair; its recovery rate is not evidence of superiority over the actual classroom implementation.

To export new evidence after execution:

~~~powershell
New-Item -ItemType Directory -Force -Path docs/verification/bonus/runtime | Out-Null
docker compose -f compose.yaml -f compose.bonus.yaml cp bonus-dashboard:/opt/project/artifacts/bonus/. ./docs/verification/bonus/runtime
~~~

Old Part 1/2 evidence is never overwritten. See the completed verification report and comparison summary linked above.

## Review / screenshots / remaining requirements

Run pages: localhost:8502 → Optional Part 3 → Bonus recorded run / Recorded evaluation suite; original Part 2 remains localhost:8501 and in the wrapper navigation.

Capture actual UI only after successful runtime: adaptive graph/decisions, recovery trace, evaluation table, comparison with clearly labeled ports, and native reference limitations. No screenshots are fabricated.

Git review (no commit, push or merge performed):

~~~powershell
git -c "safe.directory=$PWD" branch --show-current
git -c "safe.directory=$PWD" diff main --stat
git -c "safe.directory=$PWD" diff main -- README.md
git -c "safe.directory=$PWD" status --short
~~~

The user staged the prior 291-file Bonus set. The refreshed manifest includes the two additional reviewed images and submission-review updates. Inspect the full [changed-file inventory](../docs/verification/bonus/review/bonus-staging.txt) and git status --short --untracked-files=all before deciding what to stage.

No bonus points or instructor acceptance is promised. Exact native fixed-Airflow runtime comparison and acceptance of regression ports must remain explicit limitations if not completed.

## Final independent review and actual screenshots

Seven real Bonus captures are present in screenshots/ and explicitly allowlisted. Image 13 shows the regression comparison. Image 14 shows policy completion/pass-rate bars, not per-agent timings or calls; its filename does not change that scope. The [current screenshot index](../docs/verification/bonus/screenshot-guide.md) records actual content and limitations.

The [final review](../docs/verification/bonus/review/README.md) audits the original evaluator and adds independent saved-event/snapshot/prediction checks with negative tests. It does not retrain production models or rewrite old scores. Original native-Airflow comparison remains partial; passing policy fixtures is not proof of superiority or full bonus credit.
