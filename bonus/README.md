# Optional Part 3: Adaptive Bike-Demand Specialists

This original deterministic LangGraph system extends the verified bike-demand project with specialist coordination, adaptive model/feature choices and bounded failure recovery. It runs without a paid LLM API and reads the cleaned application PostgreSQL dataset.

## Architecture and routing

[Shared state](../src/bike_demand_bonus/state.py), [agents](../src/bike_demand_bonus/agents.py) and the [compiled graph](../src/bike_demand_bonus/graph.py) define distinct responsibilities:

| Agent | Responsibility |
| --- | --- |
| Data loader / quality | READ ONLY database snapshot, complete schema/date/range checks and provenance hash |
| Feature analysis | Training-only diagnostics, chronological split and Dummy reference |
| Coordinator | Choose the next specialist from intermediate state and record the reason |
| Feature refinement | Remove redundant maximum/minimum temperatures when measured collinearity and train/validation error gap justify it |
| Model selection / training | Choose and fit deterministic Ridge or a small single-thread forest |
| Evaluation | Measure training/validation MAE, RMSE and R2; retain the best validation candidate |
| Recovery | Resume a safe stage after a supported transient database or training failure |
| Final test / reporting | Freeze selection, refit on train+validation, test once and persist artifacts; report terminal failures without invented metrics |

The coordinator routes after each specialist. Limits are **three candidate attempts, two database loads, two recoveries and recursion limit 100**. Contract, permission and unsupported-model failures terminate. Test metrics have no path back into selection.

Inputs exclude cnt, casual/registered, identifiers and UCI weather. The chronological **365/182/184** split and training-only fitted preprocessing match Part 2. Evaluation faults use isolated copies or injected exceptions; production PostgreSQL is never corrupted.

## Verified results

Run **bonus_main_01** read 731 cleaned PostgreSQL rows and tried Ridge alpha=10, refined-feature Ridge alpha=100, then a 120-tree forest. It retained the first Ridge, with held-out **MAE 904.71, RMSE 1,202.36, R2 0.5231**. One prediction was negative and remains unclipped. This is an observed-weather retrospective backtest.

The graph performed 29 node operations, including 14 coordinator calls and one feature refinement. Recorded graph wall time was 0.2341 seconds, excluding container startup. Agent calls, errors and elapsed times are in the [actual run report](../docs/verification/bonus/runtime/runs/bonus_main_01/report.json). Worker RSS is a process-lifetime high-water mark, not an isolated per-run peak.

## Evaluation and comparison

Nine declared cases cover normal execution, duplicate date, missing weather, transient/permanent database failure, transient/exhausted training failure, weak model and invalid model. Three policies produce **27 isolated executions**. Each case specifies input, expected behavior, criteria and threshold.

All 27 passed expected-behavior checks and an independent saved-artifact audit. Checks cover contracts, chronological splits, route legality/reasons, exact retry counts, selected model identity, measured role timing consistency and recomputed final metrics. An all-checks score of **1.0** is required; numerical consistency tolerance is 1e-10.

Expected rejection is a pass, distinct from model completion: adaptive completed 4/9, fixed_port 4/9 and simple_port 2/9. All three normal policies selected the same Ridge and have identical test metrics. [Comparison details](COMPARISON.md) explain the explicit regression adaptations and separate native classroom classification probes.

**Both native classroom baselines are reproduced separately.** The actual seven-task DAG reports validation F1 0.0500. Native LangGraph run native_simple_02 reports best validation F1 0.056604 and held-out F1 0.059113 / accuracy 0.5225 after three no-key cycles; target 0.8 was not met. The 400 native DAG validation rows equal the graph holdout rows. Ports remain simplified Bike Demand adaptations, with no cross-task superiority claim. See [native setup/results](native-classroom/README.md) and [qualified comparison](COMPARISON.md).

## Reproduction

First complete the [root setup](../README.md), build the ML image and ensure app-db contains cleaned rows. [compose.bonus.yaml](../compose.bonus.yaml) adds opt-in services using ids706-ml:1.0.0. The runner is limited to 1 CPU/1 GiB and the dashboard to 0.5 CPU/512 MiB. Source and dashboard artifacts are mounted read only; the runner writes only new artifact folders.

~~~powershell
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus config --quiet
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus up -d --no-deps bonus-dashboard
~~~

Open http://localhost:8502 and choose Optional Part 3. The wrapper also exposes the original Part 2 page. Select bonus_main_01 for the verified graph or bonus_suite_01_transient_training_adaptive for a recorded recovery. Views read actual events/reports and cannot initiate training or write SQL.

To reproduce the serial 27-case suite or native reference probes, use new output IDs:

~~~powershell
$suffix = Get-Date -Format 'yyyyMMdd_HHmmss'
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner /bin/sh -c "umask 0002; exec python -m bike_demand_bonus.cli evaluate --id suite_$suffix"
py -3.11 bonus/fetch_classroom.py
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner /bin/sh -c "umask 0002; exec python -m bike_demand_bonus.cli classroom --id classroom_$suffix"
~~~

The reference fetcher checks pinned public Git blobs in an ignored local cache. [Source pins](classroom_sources.json) identify classroom commit a294145ea9aa4225908ce701c06160c33213335d. These earlier CLI probes are historical classification experiments, not native Airflow DAG runs. The separate [native harness](native-classroom/README.md) executes the actual DAG and consumes its publication in the original graph. Existing run folders refuse overwrite.

For Bonus synthetic tests and the explicit read-only database integration test:

~~~powershell
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps -e BONUS_DB_INTEGRATION=1 bonus-runner python -m pytest /opt/project/tests/bonus -c /opt/project/pytest.ini -p no:cacheprovider -q -ra
~~~

## Evidence and limits

- [Seven adaptive-system screenshots](../screenshots/README.md): graph, recovery, suite, criteria and policy comparison.
- [Evaluation results](../docs/verification/bonus/runtime/evaluations/bonus_suite_01/results.json) and [summary](../docs/verification/bonus/runtime/evaluations/bonus_suite_01/summary.json).
- [Native reference results](../docs/verification/bonus/runtime/classroom/classroom_probe_01/summary.json).
- [Verification index](../docs/verification/bonus/review/README.md): 43 Bonus tests plus 59 unchanged pipeline/ML/DAG tests, **102 passed**.
- [Evaluation case definitions](../docs/verification/bonus/evaluation-cases.md).
- [Native classroom execution report](../docs/verification/bonus/native-classroom/results.md) and [six reviewed native captures](../docs/verification/bonus/native-classroom/capture-guide.md).

The policy-rate chart is named 14_bonus_policy_comparison.png; it does not show per-agent timings. Those values are retained in the run report. Candidate validation predictions were not saved; final test predictions were. Nine designed scenarios and single-run timings do not measure broad reliability, generalization or native-classroom superiority.

All nineteen application screenshots are indexed in the [screenshot guide](../screenshots/README.md). The [final submission audit](../docs/verification/final-bonus/README.md) records current preservation, test and packaging checks.
