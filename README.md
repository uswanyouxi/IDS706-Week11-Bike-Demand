# DC Bike Demand and Weather Intelligence

## Project overview

How do calendar patterns and weather relate to daily Washington DC bike demand, and how well can lightweight models predict historical rental counts? This Duke IDS 706 Week 11 project combines an original Airflow pipeline, an original LangGraph ML workflow, and an optional adaptive multi-agent extension.

**Parts 1 and 2 are completed and runtime-verified on [main](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/main).** The optional adaptive extension is on [bonus/adaptive-multi-agent](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/bonus/adaptive-multi-agent), with separately verified native classroom baselines and explicitly adapted Bike Demand comparisons.

## Data sources

- [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset): day.csv provides daily Capital Bikeshare rental count cnt and calendar fields.
- [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api): ERA5 mean/maximum/minimum temperature, precipitation and maximum wind for Washington DC (38.9072, -77.0369), requested with America/New_York.

Both cover **2011-01-01 through 2012-12-31**. The pipeline downloads both real sources; host data/raw files are source-verification downloads, not pipeline inputs.

## Part 1: Airflow pipeline

[DAG dc_bike_weather_daily](dags/dc_bike_weather.py) runs two independent branches concurrently:

~~~text
start -> download_uci -> clean_bike --------+
      -> fetch_era5_weather -> clean_weather-+
                                          -> validate_and_merge_dates
                                         -> load_application_postgres
                                         -> read_database_and_make_eda -> end
~~~

Cleaning validates schema, units, numerical ranges, unique dates and complete coverage. A one-to-one date join found **731 matches and zero unmatched dates**. Transactional upserts preserve **731 rows / 731 unique dates and 3,292,679 rentals** across repeated runs.

Application data lives in app-db / bike_demand / bike_analytics.bike_daily, separate from Airflow metadata. A new PostgreSQL query generates three [EDA charts and summaries](submission/part1/README.md). Mean demand is **4,504.35 rentals/day**; temperature correlation is **0.607** and precipitation correlation is **-0.281**.

The schedule is **06:00 America/New_York daily**, cron 0 6 * * *, catchup=False, one active run and two task slots. Three verified runs completed all nine tasks; source-branch overlap was measured. Daily execution refreshes a historical dataset for reproducibility.

## Part 2: LangGraph regression workflow

The [original executable graph](src/bike_demand_ml/graph.py) uses explicit state and conditional edges:

~~~text
PostgreSQL snapshot -> features -> Dummy baseline -> candidate -> train
    -> validation -> router -> bounded retry / final test once -> report
Errors -> failure report
~~~

Calendar features and five Open-Meteo weather fields predict cnt. Inputs exclude cnt, casual, registered, identifiers and UCI weather. Data comes from a validated **READ ONLY PostgreSQL snapshot**, with no raw-file fallback. Chronological train/validation/test partitions contain **365 / 182 / 184 days**; preprocessing fits on training data during selection.

The policy compares two candidates, with a hard two-attempt cap and a 5% validation-RMSE improvement target over Dummy. It starts with Ridge alpha=10. A validation/train RMSE ratio above 1.5 selects stronger regularization; otherwise it selects a seeded RandomForest. Run **ml_main_01** compared Ridge alpha=10 and alpha=100, retained alpha=10 by validation RMSE (**1,573.81 versus 1,614.16**), and refit selected/Dummy models on 547 rows before one final held-out test. RandomForest was not used in that run.

| Held-out model | MAE | RMSE | R2 |
| --- | ---: | ---: | ---: |
| Selected Ridge alpha=10 | 904.71 | 1,202.36 | 0.5231 |
| Mean Dummy baseline | 2,452.64 | 2,694.30 | -1.3946 |

The Streamlit UI displays the compiled graph, recorded node progress, routing reasons and actual metrics. See the [model report](docs/verification/phase-c/runs/ml_main_01/report.json).

## Optional Part 3: adaptive multi-agent system

The [adaptive graph](src/bike_demand_bonus/graph.py) adds a coordinator and specialists for data quality, feature analysis/refinement, model selection, training, evaluation, recovery and reporting. Intermediate diagnostics determine the next agent. Budgets limit execution to **three candidate attempts, two database loads and two recoveries**. Permanent failures terminate with a failure report; final test results never return to selection.

Run **bonus_main_01** explored two Ridge candidates and a small forest, including one weather-feature refinement, then retained the original Ridge alpha=10. The dashboard at localhost:8502 shows real events, recovery, evaluation cases and measured agent calls/timings. [Bonus documentation](bonus/README.md) covers architecture, reproduction and evidence.

## Evaluation and baseline comparison

Nine scenarios test normal execution, duplicate dates, missing weather, transient/permanent database failures, transient/exhausted training failures, a weak model and an invalid model: **27 executions across three policies**. All passed their declared expected-behavior checks and independent saved-artifact audits.

| Regression policy | Completed cases | Expected-behavior passes | Recoveries |
| --- | ---: | ---: | ---: |
| Adaptive specialists | 4/9 | 9/9 | 4 |
| Fixed workflow port | 4/9 | 9/9 | 4 |
| Simple agent port | 2/9 | 9/9 | 0 |

Expected rejection counts as a passed evaluation case, not a completed model run. All three normal-case policies have identical held-out Ridge metrics; adaptivity did not improve predictive accuracy.

**Native classroom reproduction is verified separately.** The actual seven-task Airflow DAG (native_prep_01) achieved validation F1 **0.0500**. The original no-key LangGraph (native_simple_02) completed three cycles: best validation F1 **0.056604**, held-out F1 **0.059113**, accuracy **0.5225**; its 0.8 target was not met. Native DAG validation and graph holdout use the same 400 rows, with different preprocessing/selection contracts. Classification F1 cannot be ranked against Bike Demand RMSE. See [actual native results](docs/verification/bonus/native-classroom/results.md), [isolated setup](bonus/native-classroom/README.md) and [qualified comparison](bonus/COMPARISON.md).

## Docker setup and execution

Use PowerShell, Python 3.11 and Docker Desktop Linux containers/WSL2. The tested Windows host has 16 GB RAM and about 7.65 GiB assigned to Docker. Provide disk/memory headroom. Airflow 3.4.0/Python 3.11 and ML use [separate pinned dependencies](requirements/).

For a fresh checkout only; retain an existing .env and database credentials:

~~~powershell
git clone --branch bonus/adaptive-multi-agent https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand.git
Set-Location IDS706-Week11-Bike-Demand
py -3.11 scripts/new_local_env.py
docker compose config --quiet
docker compose --progress plain build airflow-init
docker compose up airflow-init
docker compose up -d app-db airflow-apiserver airflow-scheduler airflow-dag-processor
docker compose ps --all
docker compose exec -T airflow-scheduler python /opt/project/scripts/verify_dag.py
~~~

Open Airflow at http://localhost:8080 with local .env administrator credentials. Unpause and trigger a new run; wait for all nine tasks to succeed:

~~~powershell
docker compose exec -T airflow-scheduler airflow dags unpause dc_bike_weather_daily
$runId = 'manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
docker compose exec -T airflow-scheduler airflow dags trigger dc_bike_weather_daily --run-id $runId --output json
docker compose exec -T airflow-scheduler airflow tasks states-for-dag-run dc_bike_weather_daily $runId --output json
~~~

With cleaned PostgreSQL data available, run Part 2:

~~~powershell
docker compose --profile ml --progress plain build ml-runner
docker compose --profile ml up -d --no-deps dashboard
docker compose --profile ml run --rm --no-deps ml-runner
~~~

Open http://localhost:8501 and select a recorded run. To execute the optional graph and open its separate dashboard:

~~~powershell
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus run --rm --no-deps bonus-runner
docker compose -f compose.yaml -f compose.bonus.yaml --profile bonus up -d --no-deps bonus-dashboard
~~~

ML and Bonus services are opt-in profiles. Named volumes hold databases, pipeline downloads and artifacts; .env and local caches remain ignored. See [operating/test commands](docs/running.md) and [Bonus suite/reference commands](bonus/README.md).

## Screenshots and verification

All 19 captures are genuine application images. Recorded graph progress and replay reflect actual executions.

| Part | Screenshots |
| --- | --- |
| Airflow | [Successful runs](screenshots/01_airflow_dag_success.png), [parallel DAG](screenshots/02_airflow_graph.png) |
| Part 2 graph | [Execution](screenshots/06_langgraph_live_execution.png), [conditional retry](screenshots/07_langgraph_conditional_retry.png) |
| Part 2 evaluation | [Metrics](screenshots/08_regression_evaluation.png), [model charts](screenshots/09_model_comparison_charts.png) |
| Bonus graph/recovery | [Adaptive graph](screenshots/10_bonus_adaptive_graph.png), [recovery route](screenshots/11_bonus_routing_recovery.png), [recovery events](screenshots/11b_bonus_recovery_events.png) |
| Native Airflow | [Successful run](screenshots/15_native_airflow_success.png), [seven-task topology](screenshots/16_native_airflow_graph.png), [XCom metrics and run ID](screenshots/17_native_airflow_metrics.png) |
| Native LangGraph | [Graph and final metrics](screenshots/18_native_langgraph_execution.png), [agent execution records](screenshots/19_native_classification_results.png), [separate comparison scopes](screenshots/20_native_and_regression_scopes.png) |
| Bonus evaluation | [Suite](screenshots/12_bonus_evaluation_suite.png), [criteria](screenshots/12b_bonus_evaluation_criteria.png), [baseline table](screenshots/13_bonus_baseline_comparison.png), [policy rates](screenshots/14_bonus_policy_comparison.png) |

The [screenshot index](screenshots/README.md) describes each capture. [Submission evidence](docs/submission.md) links SQL/idempotence checks, three EDA charts, model artifacts and verification results. The final audit passed **128 tests**: 100 existing pipeline/ML/Bonus synthetic tests, one real DAG import, one read-only PostgreSQL integration test, 16 native isolation checks and 10 reviewer safeguards. All six native captures are included; image 19 shows execution records rather than final metric cards, which are visible in 18 and 20. Historical logs retain their timestamps. The [final audit](docs/verification/final-bonus/README.md) documents current checks and the explicit submission inventory.

## Limitations

This is a **retrospective backtest using observed weather**, not a future real-time forecast. The final Ridge produced **one negative prediction among 184 test dates**, retained without clipping or post-test tuning. One temporal split, changing demand and historical weather day-boundary differences limit generalization; correlations are not causal.

Native classroom execution is reproduced; the same-problem Bike Demand ports remain simplified adaptations, and the classroom LLM-enabled path is untested. Native classifiers emitted convergence warnings. Designed fault cases and single-run timings do not establish general reliability or superiority. Candidate validation predictions were not saved for independent recomputation; final held-out predictions were saved and audited.
