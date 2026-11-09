# DC Bike Demand & Weather Intelligence

Duke IDS 706 Week 11: an original Airflow data pipeline and an original LangGraph regression workflow. **Required Parts 1 and 2 are completed, runtime-verified, committed and published on [GitHub main](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/main), with six real application screenshots.** Part 3 is optional and is not part of the verified main branch.

The project asks how weather and calendar factors relate to daily Washington DC bike demand, and how well a lightweight model predicts historical daily rentals.

## Pipeline and results

[UCI Bike Sharing day.csv](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) provides daily Capital Bikeshare counts/calendar fields. Independent [Open-Meteo ERA5 historical weather](https://open-meteo.com/en/docs/historical-weather-api) provides mean/max/min temperature, precipitation and maximum wind at Washington DC (38.9072, -77.0369), requested with America/New_York for 2011–2012.

[Airflow DAG dc_bike_weather_daily](dags/dc_bike_weather.py) downloads both sources inside two independent branches: download_uci → clean_bike and fetch_era5_weather → clean_weather. They converge at date validation/merge, then load application PostgreSQL and query it back for EDA. Cleaning checks schemas, numeric ranges, complete coverage and unique dates; the one-to-one join found **731 matches and zero unmatched dates**.

The schedule is **06:00 America/New_York daily**, cron 0 6 * * *, catchup=False, one active run and two task slots. Actual ingestion/cleaning overlap was observed. Scheduled historical refreshes demonstrate reproducibility, not newly collected 2011–2012 observations. Three verified runs each completed all nine tasks.

Transactional date upserts retained **731 rows / 731 unique dates**, covering 2011-01-01–2012-12-31, and **3,292,679 rentals** across repeated loads. Application data is in app-db / bike_demand / bike_analytics.bike_daily, separate from Airflow metadata. Fresh PostgreSQL reads produced three [EDA charts and findings](submission/part1/README.md): mean demand 4,504.35/day; demand/temperature Pearson r=0.607 and demand/precipitation r=-0.281.

## Agent workflow and evaluation

The [executable LangGraph](src/bike_demand_ml/graph.py) uses explicit shared state and specialist nodes:

~~~text
PostgreSQL loader → feature preparation → Dummy baseline → choose candidate
    → train → evaluate validation → conditional router
                retry ↖ choose candidate    ↓ finish
                                      final test once → report
Errors → failure report → END
~~~

Training input comes from a validated **READ ONLY PostgreSQL snapshot**, with no raw-file fallback. Calendar and five Open-Meteo features predict cnt. Inputs exclude cnt itself, casual, registered, row identifiers and UCI weather. Preprocessing fits on training data during selection.

Chronological partitions are 2011 training (365 days), January–June 2012 validation (182), and July–December 2012 held-out test (184). The original loop has a hard cap of two attempts. It first tries Ridge alpha=10; a validation/train RMSE ratio above 1.5 chooses stronger regularization (alpha=100), otherwise a small seeded RandomForest. Default minimum two compares candidates; the router stops on a 5% validation-RMSE improvement over Dummy or an exhausted budget.

Real run **ml_main_01** retried with alpha=100, retained alpha=10 by validation RMSE (1,573.81 versus 1,614.16), then refit selected/Dummy estimators on 547 train+validation rows. One final test stage scored both, without a tuning back edge. RandomForest was not trained in this production run.

| Held-out model | MAE (rentals) | RMSE (rentals) | R² |
| --- | ---: | ---: | ---: |
| Selected Ridge alpha=10 | 904.71 | 1,202.36 | 0.5231 |
| Mean Dummy baseline | 2,452.64 | 2,694.30 | -1.3946 |

**The final Ridge model produced one negative prediction among 184 test dates.** No clipping or retuning was applied. This is a **retrospective backtest using observed weather**, not a future real-time forecast. One temporal split, changing demand and Open-Meteo's historical fixed-offset day boundaries limit generalization. Correlations are descriptive.

## Setup and execution

Use PowerShell, Python 3.11 and Docker Desktop Linux containers/WSL2. After cloning, run project commands from the repository root. The tested host has 16 GB RAM with ~7.65 GiB assigned to Docker; allow disk/memory headroom. Airflow 3.4.0/Python 3.11 uses [pinned Airflow dependencies](requirements/airflow.txt) and [official constraints](requirements/airflow-constraints-3.11.txt); the isolated ML image has [separate pins](requirements/ml.txt). Keep existing .env passwords when retaining database volumes.

**Fresh checkout only** (do not regenerate an existing .env):

~~~powershell
git clone https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand.git
Set-Location IDS706-Week11-Bike-Demand
py -3.11 scripts/new_local_env.py
docker compose config --quiet
docker compose --progress plain build airflow-init
docker compose up airflow-init
docker compose up -d app-db airflow-apiserver airflow-scheduler airflow-dag-processor
docker compose ps --all
docker compose exec -T airflow-scheduler python /opt/project/scripts/verify_dag.py
~~~

Open Airflow at http://localhost:8080 using the local .env administrator credentials. For a new pipeline execution, unpause and trigger with a unique ID, then verify all nine tasks succeed:

~~~powershell
docker compose exec -T airflow-scheduler airflow dags unpause dc_bike_weather_daily
$runId = 'manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
docker compose exec -T airflow-scheduler airflow dags trigger dc_bike_weather_daily --run-id $runId --output json
docker compose exec -T airflow-scheduler airflow tasks states-for-dag-run dc_bike_weather_daily $runId --output json
~~~

After the pipeline succeeds and app-db is healthy, build/start only ML:

~~~powershell
docker compose --profile ml --progress plain build ml-runner
docker compose --profile ml up -d --no-deps dashboard
docker compose --profile ml run --rm --no-deps ml-runner
~~~

Open http://localhost:8501. Select a recorded run; the UI derives its graph from the compiled workflow and shows actual streamed node events, conditional edges, metrics and errors. Uncheck Follow live execution to replay events; ml_main_01 event 14 records the retry. New runs receive unique IDs and cannot overwrite prior run folders. ML services are excluded from default startup by the ml profile.

Named volumes store SQL data, raw pipeline downloads and artifacts. Host data/raw verification downloads are not production pipeline inputs. Do not commit .env, volumes or local caches. [Detailed operating/test commands](docs/running.md) supplement this guide.

## Real screenshots and reproducibility evidence

All six files below exist and were visually reviewed; none is an AI-generated UI image.

| Screenshot | Evidence |
| --- | --- |
| [01 — Airflow success](screenshots/01_airflow_dag_success.png) | Nine task rows and three successful run columns |
| [02 — Airflow graph](screenshots/02_airflow_graph.png) | Independent source branches, merge, persistence and analysis |
| [06 — Agent graph](screenshots/06_langgraph_live_execution.png) | Original executable graph and recorded execution progress |
| [07 — Conditional retry](screenshots/07_langgraph_conditional_retry.png) | Actual retry after attempt one and finish after attempt two |
| [08 — Regression evaluation](screenshots/08_regression_evaluation.png) | Held-out metrics, candidate results and routing decisions |
| [09 — Comparison charts](screenshots/09_model_comparison_charts.png) | Held-out predictions and validation RMSE comparison |

[Full screenshot index](screenshots/README.md) describes the captures. Original [Part 1 runtime evidence](docs/verification/phase-b/status.md), [PostgreSQL/idempotence report](submission/part1/postgres_report.md), [Part 2 report](docs/verification/phase-c/runs/ml_main_01/report.json), and [Part 2 verification](docs/verification/phase-c/status.md) contain actual logs, metrics, provenance and hashes. Earlier phase reports retain their historical scope.

Final submission checks passed **39 pipeline unit tests, 19 ML tests and one real DAG-import test**. Synthetic ML test fits did not rerun production training. No production DAG/model run was repeated for submission preparation. See [final checks and exact commit list](docs/submission.md).

The repository includes the source code, Docker setup, tests, documentation, and screenshots for Parts 1 and 2. Both workflows have been implemented and successfully tested. Detailed execution logs and verification results are available in the `docs/verification/` directory.


## Optional Part 3 - separate bonus branch

The local bonus/adaptive-multi-agent branch adds an original adaptive specialist graph, bounded recovery, a PostgreSQL-fed runtime, and 27 isolated evaluation executions. It preserves the verified Parts 1 and 2 above. Strict classroom-baseline comparison remains partial: native classification probes and explicit bike-demand regression ports are reported separately, and the original classroom Airflow DAG was not executed. Seven reviewed Bonus screenshots are present. The image named 14_bonus_agent_metrics.png shows policy completion/pass rates; per-agent calls and timings are retained in the runtime reports. No full bonus-points claim is made.

See the [bonus guide](bonus/README.md), [actual comparison](bonus/COMPARISON.md), [requirement-by-requirement verification](docs/verification/bonus/status.md), and [screenshot instructions](docs/verification/bonus/screenshot-guide.md). These bonus changes remain local; they have not been committed, merged into main, or pushed.

The [final independent-review report](docs/verification/bonus/review/README.md) lists the actual Bonus screenshots, evaluator weaknesses and independent artifact checks, exact staging manifest, and remaining strict-baseline risk.
