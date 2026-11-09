# Part 1 verification

Run host tests with the project-local pinned environment:

~~~powershell
./.venv/Scripts/python.exe scripts/check_phase_b.py
~~~

The script saves actual pytest output/JUnit XML, package versions and the cached
real-source contract probe under docs/verification/phase-b. It starts no containers.

- test_contracts.py uses explicitly synthetic 731-day fixtures for schema, range,
  leakage exclusions, target identity, duplicate/missing dates, invalid weather,
  unmatched rows, row explosion prevention and stable dataset hashes.
- test_cached_real_sources separately uses the original real UCI/Open-Meteo
  downloads when available; missing raw downloads cause an explicit skip.
- test_pipeline_io.py covers atomic JSON round trips, run-path safety, failure-audit
  secret handling, forwarded run IDs and permanent/transient/rate-limited HTTP.
- test_init_airflow.py contains 12 mocked setup safety tests, not runtime evidence.
- integration/test_dag.py imports a real Airflow DagBag and checks actual schedule,
  timezone, retries, task set and dependency edges. It skips if Airflow is absent.
- integration/test_postgres.py requires a real existing disposable *_test DB.
  It checks idempotent upserts and fresh snapshots, then injects a real server-side
  SQL error inside the loader transaction and verifies rollback. It never targets
  Airflow metadata or the production bike_demand DB.

The Docker image includes tests, SQL migration and a DAG snapshot. Run the real
DagBag verifier against mounted /opt/airflow/dags as well; the test snapshot cannot
prove that an edited mounted DAG imports. See README for exact runtime commands.

## Part 2 isolated ML verification

The primary setup/results guide is [the root README](../README.md). Part 2 tests are in tests/ml and run inside the separate pinned ML image:

~~~powershell
docker compose --profile ml run --rm --no-deps ml-runner python -m pytest tests/ml -p no:cacheprovider -q -ra --junitxml=/opt/project/artifacts/ml-verification/tests-final.xml
~~~

Actual result: 19 passed, zero skipped. Policy tests cover success, predeclared comparison retry, missed quality target retry, hard max attempts, validation-only selection, adaptive regularization/nonlinearity, temporal splits and training-only preprocessing. Database tests assert READ ONLY application SQL and no file fallback. Execution tests run the compiled graph on explicitly synthetic fixtures to verify loop limits, one final test stage, failed-run reporting, artifacts, deterministic metrics, safe paths and refusal to overwrite evidence.

These synthetic test results do not establish production model performance. The independent real ml_main_01 run reads PostgreSQL and supplies the reported held-out metrics. A real nonexistent-database probe follows the failure graph and claims no metrics. Streamlit AppTest in the actual dashboard checks graph rendering, replay and exact metric values.

[Actual JUnit XML](../docs/verification/phase-c/test-artifacts/tests-final.xml), [test log](../docs/verification/phase-c/tests-final.log) and [requirement status](../docs/verification/phase-c/status.md) are preserved. The no-cache option avoids attempting to write pytest cache into the image workdir; permissions were not weakened. Host Part 1 environments without LangGraph skip ML modules explicitly.