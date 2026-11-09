# Detailed operating and test commands

[Root README](../README.md) is the primary guide. Commands below are for intentional reproduction; final submission preparation did not rerun ingestion or production training.

## Fresh environment

Use Windows PowerShell, Docker Desktop Linux containers/WSL2 and Python 3.11. Ensure sufficient Docker disk headroom and approximately 8 GiB engine RAM. No system resource settings are changed by project setup.

~~~powershell
py -3.11 scripts/new_local_env.py
docker compose config --quiet
docker compose --profile ml config --quiet
docker compose --progress plain build airflow-init
docker compose up airflow-init
docker compose up -d app-db airflow-apiserver airflow-scheduler airflow-dag-processor
docker compose ps --all
docker compose exec -T airflow-scheduler python -m pip check
docker compose exec -T airflow-scheduler python /opt/project/scripts/verify_dag.py
docker compose exec -T airflow-scheduler airflow dags list-import-errors --local --output json
~~~

Do not regenerate an existing .env. Initialization migrates Airflow metadata, checks/creates the FAB administrator, and initializes shared-volume group permissions. No application data is loaded until the DAG executes. Existing database volumes must retain their credentials.

Airflow: http://localhost:8080. Default username student; use the generated local admin password privately. Health endpoint: http://localhost:8080/api/v2/monitor/health; inspect component states as well as HTTP status.

## Pipeline execution / read-only verification

~~~powershell
docker compose exec -T airflow-scheduler airflow dags unpause dc_bike_weather_daily
$runId = 'manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
docker compose exec -T airflow-scheduler airflow dags trigger dc_bike_weather_daily --run-id $runId --output json
docker compose exec -T airflow-scheduler airflow dags list-runs dc_bike_weather_daily --output json
docker compose exec -T airflow-scheduler airflow tasks states-for-dag-run dc_bike_weather_daily $runId --output json
docker compose exec -T airflow-scheduler airflow dags next-execution dc_bike_weather_daily
docker compose exec -T app-db psql -U bike_app -d bike_demand -c "BEGIN READ ONLY; SELECT count(*) AS rows, count(DISTINCT date) AS unique_dates, min(date), max(date), sum(cnt) AS total_rentals FROM bike_analytics.bike_daily; SELECT run_id,row_count,dataset_hash,eda_summary IS NOT NULL AS analysis_complete FROM bike_analytics.pipeline_runs ORDER BY loaded_at; COMMIT;"
~~~

Wait for all nine task states to become success. Refreshes upsert by date. Verified historical results were 731 rows/unique dates and 3,292,679 rentals; upstream data changes can change a future content hash without indicating duplicate rows. The scheduler runs at 06:00 America/New_York daily with catchup=False.

## ML execution / dashboard

Once Part 1 has succeeded and app-db remains healthy:

~~~powershell
docker compose --profile ml --progress plain build ml-runner
docker compose --profile ml up -d --no-deps dashboard
docker compose --profile ml run --rm --no-deps ml-runner
~~~

For a chosen unique run ID:

~~~powershell
$mlRun = 'ml_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
docker compose --profile ml run --rm --no-deps ml-runner /bin/sh -c "umask 0002; exec python agents/run.py --run-id $mlRun"
~~~

Open http://localhost:8501 and select that run. The default command generates a unique ID. Existing folders cannot be overwritten. Profile ml excludes these services from normal startup; it does not stop an already-running dashboard. Targeted --no-deps avoids rerunning Airflow initialization.

The runner uses a READ ONLY application PostgreSQL snapshot, not host raw files. Shared artifact folders support UID 50000/group 0 and UID 10001/group 0 via setgid/group write, without world-write. The dashboard's artifact mount is read-only.

## Tests without new production executions

Host pipeline unit tests:

~~~powershell
py -3.11 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements/pipeline-test.txt
./.venv/Scripts/python.exe -m pytest tests/unit -p no:cacheprovider -q -ra
~~~

With already-running services, DAG parsing and isolated synthetic ML tests:

~~~powershell
docker compose exec -T airflow-scheduler python -m pytest /opt/project/tests/integration/test_dag.py -p no:cacheprovider -q -ra
docker compose exec -T dashboard python -m pytest tests/ml -p no:cacheprovider -q -ra
py -3.11 scripts/check_submission.py
~~~

These commands do not trigger the DAG, retrain the production model, or mutate production SQL. ML unit tests fit synthetic fixtures in temporary directories. Separate real SQL integration tests are described in [tests documentation](../tests/README.md); they require an explicitly named disposable *_test database.

Historical scripts/check_phase_b.py writes its original Phase B report paths. scripts/verify_phase_c_evidence.py checks a historical 182-file snapshot that includes documentation since intentionally updated for final submission. Use the new submission checker for final source/evidence preservation; keep historical reports intact.

## Evidence locations

- Host data/raw: ignored source-probe downloads, not production ingestion input.
- Named project-data: actual pipeline HTTP responses and cleaned intermediates.
- Named project-artifacts: pipeline audits/EDA and ML event streams/reports/models.
- [submission/part1](../submission/part1/README.md): frozen PostgreSQL/idempotence/EDA evidence.
- [docs/verification/phase-c](verification/phase-c/status.md): frozen ML success/failure runs and metrics.
- [Final submission checks](submission.md): current files, links, secret scan, tests and staging plan.

No deletion/prune, service stop, system setting changes, external deployment or Git push is needed to prepare the submission.
