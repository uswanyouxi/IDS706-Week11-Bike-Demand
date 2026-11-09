> Historical Phase B runtime report. Final submission update November 9, 2026: Part 2 is also verified and all six real screenshots are captured. Later screenshot/service/phase status supersedes the original phase-boundary wording below; see [the root README](../../../README.md). Runtime records and results remain unchanged.

# Phase B — Part 1 implemented and runtime verified

Verified November 8, 2026 (America/New_York); UTC timestamps fall on November 9.
The user explicitly approved the controlled runtime test. Part 2 was not started.
No Docker data was deleted/moved, no system settings changed, and nothing was
pushed or externally deployed.

## Requirement-by-requirement result

| Requirement | Actual result / evidence |
| --- | --- |
| Original scheduled DAG | Real Airflow 3.4.0 DagBag passes: 9 tasks, cron 0 6 * * *, America/New_York, catchup=False, max_active_runs=1 and max_active_tasks=2. A scheduler-created run succeeded. |
| Two independent real sources | Every successful run fetched UCI and Open-Meteo ERA5 inside ingestion tasks; both HTTP 200 with run-time retrieval timestamps and source checksums. No host-cache fallback. |
| Concurrent branches | Actual task timestamps show overlapping ingestion and cleaning; first manual run overlap 1.113586 s ingestion and 0.552582 s cleaning. Second manual ingestion overlap 4.519830 s; its cleaning tasks did not overlap, which is valid dependency-driven scheduling. |
| Separate cleaning and strict merge | All runs validated 731 unique days per source, complete coverage including leap day, finite/ranged values and calendar/count identities. Merge: 731 matches, 0 bike-only, 0 weather-only, 731 output rows, one-to-one semantics. |
| Separate application PostgreSQL | bike_demand.bike_analytics contains the application tables. A live metadata DB query found zero bike_analytics tables in airflow. |
| Idempotence | Before and after second manual refresh: 731 rows, 731 unique dates, 2011-01-01 through 2012-12-31, one stable content hash. Three provenance rows represent three actual runs, not duplicate daily records. |
| DB-fed EDA | Each run reopened application PostgreSQL, verified the persisted hash and produced three PNGs plus JSON/text findings. All 9 PNGs exported; final run's three charts visually inspected. |
| Tests and imports | Host: 39 passed/3 explicit skips. Final Linux full suite: 41 passed/1 skip, including real DagBag and 2 real PostgreSQL tests. Linux pip check passed. |
| Initialization / health / auth | Real migrations and FAB admin creation succeeded. Repeated init preserved the existing Admin. API token authentication HTTP 201 succeeded; no token was persisted. All five long-running Part 1 containers are healthy. |
| Instructions/evidence | README has exact build/init/startup/trigger/schedule/SQL/export commands. Actual logs, JUnit, run/task states, source provenance, validation, SQL, schema, EDA and permission probes are saved here. |
| Scope | ML dashboard/runner remain off. No training, Part 2, bonus, push or external deployment. |

The health JSON reports the intentionally absent triggerer as down/unhealthy.
This DAG uses no deferrable tasks. Metadata database, scheduler and DAG processor
all report healthy; API and both DB container checks also pass. Do not describe
the optional triggerer as running.

## Actual successful DAG runs

All times below are UTC, directly from Airflow:

| Run ID | Start | End | Result |
| --- | --- | --- | --- |
| scheduled__2026-11-08T11:00:00+00:00 | 2026-11-09 02:53:52.237785 | 2026-11-09 02:54:06.355713 | success, 9/9 tasks |
| phase_b_manual_01 | 2026-11-09 02:54:07.395227 | 2026-11-09 02:54:18.522245 | success, 9/9 tasks |
| phase_b_manual_02 | 2026-11-09 02:57:30.779006 | 2026-11-09 02:57:45.946872 | success, 9/9 tasks |

The scheduler-created run became due before the DAG was unpaused, then ran
naturally when enabled. Its logical/run-after date is distinct from its actual
start time. Next execution reported by Airflow is 2026-11-09T11:00:00+00:00,
which is November 9 at 06:00 America/New_York. No run type was forged.

Each substantive task succeeded on attempt 1 (21 successful audit files).
Empty start/end tasks are included in the 9-task Airflow state reports.
runtime-results.json reconciles all 3 runs with their task states, load receipts,
validation reports, PNG signatures, source fetch statuses and DB provenance.

## Measured database findings

Application table: bike_demand.bike_analytics.bike_daily.

- Rows / distinct dates: **731 / 731**, unchanged after rerun.
- Date range: **2011-01-01–2012-12-31**.
- Total rentals: **3,292,679**; mean daily rentals: **4,504.35**.
- Demand vs ERA5 mean temperature Pearson r: **0.607441**.
- Demand vs precipitation Pearson r: **-0.280501**.
- Dataset SHA-256: 99123ac3758014b572f0ac290b1cfcba3896a8fae47896055eb1cc9d89579a33.

These are descriptive historical associations. Calendar, season and time trends
can confound them; no causal relationship or forecasting/model quality is claimed.
Weather uses the API's returned local-date labels and fixed-offset daily windows,
with the already documented DST boundary limitation.

## Actual output files

Latest manual run (phase_b_manual_02) uses run key 3f0c5b99a18c83f3e98bc59c:

- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/eda/weekday_mean_rentals.png
- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/eda/monthly_mean_rentals.png
- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/eda/weather_vs_demand.png
- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/eda/summary.json and summary.txt
- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/validation/bike.json, weather.json, merged.json
- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/load-receipt.json
- runtime-artifacts/3f0c5b99a18c83f3e98bc59c/tasks/*_attempt_1.json

Other real run folders:
2e6003b7f6ec3ea9b43699a1 (manual 01),
ed16b9044267dcba9617d614 (scheduler-created).

Key verification files:

| File | Evidence |
| --- | --- |
| runtime-results.json | Reconciled final results, real counts and overlap statistics |
| runtime-verification/dag-parse.json | Real final-image DAG parsing/configuration |
| runtime-verification/linux-full-tests.xml, linux-full-tests.log | 41 passes, 1 explicit skip |
| host-tests.xml, host-tests.log, host-checks.json | Pinned host tests and separately labeled cached-file probe |
| postgres-tests.log | Real disposable-DB idempotence and injected SQL rollback tests |
| sql-before-rerun.json, sql-after-rerun.json | Unchanged production counts/date range |
| run-provenance-final.json | Actual source URLs/checksums/timestamps, validation and EDA query for all runs |
| application-schema.json, database-separation.json | Actual column types and metadata/application DB separation |
| runs-final.json.log, tasks-*.json.log | Native Airflow run and task results |
| airflow-task-logs/manifest.json and hashed folders | 21 exported genuine task logs, original Linux paths recorded |
| health-final.json, services-final.json, authentication.json | Actual health, ML-off status and successful token authentication flag |
| volume-permissions.log | Real cross-UID 50000/10001 artifact writes, group 0, directories 2775/files 664 |
| container-memory-snapshot.jsonl | About 1.07 GiB across the five containers at that snapshot; not peak/system usage |
| runtime-versions.json, linux-freeze.txt | Airflow 3.4.0 / Python 3.11.18 and actual installed packages |
| docker-build*.log, initialization*.log, startup*.log | Actual build/init/repeated-init/startup output |
| secret-scan.json | Exact local-secret check over exported text evidence |

The optional cached-source unit test skips inside Linux because host data/raw is
intentionally neither copied nor mounted there. This does not weaken the live
source evidence: all three DAG runs fetched the real endpoints successfully.
The disposable bike_demand_test DB contains explicitly synthetic SQL test rows,
separate from these production results.

## Failures encountered and corrections

| Observed issue | Correction / preserved evidence |
| --- | --- |
| Sandbox command runner fails setup refresh | Approved outside-sandbox project-local execution; no system policy change. |
| Large write exceeded Windows command length | Split writes; failed command created no implementation files. |
| Initial host pytest: 1 failed, 38 passed | Pandas rejected the fractional test fixture before validator execution. Explicit fixture object dtype fixed the test; all final host tests pass. |
| UTF-8 file read with default Windows GBK | Explicit UTF-8 in subsequent helpers. No data loss. |
| Pandas deprecation warning | day_of_week replaces dayofweek; final tests have no warnings. |
| Real DagBag rejected include_examples | Removed the obsolete argument and used airflow.dag_processing.dagbag; dag-parse-initial.log preserves failure. |
| Old private timetable _expression assertion failed | Verified public dag.schedule from the real object; dag-parse-timetable.log preserves failure. Exploratory summary lookup was also unavailable. |
| Standalone pip launcher permission denied at /root/bin/pip | python -m pip check passes; README corrected. Initial error preserved in linux-pip-check-initial.log. |
| Windows direct copy rejected scheduled run ID colons | scripts/export_task_logs.py exports real logs to hash-keyed safe paths with original path manifest. No Docker data removed. |
| Unpause command printed True | Subsequent authoritative DAG listing showed False, and the scheduler-created run succeeded; both observations retained. |

These were setup/verifier/export issues. No production ingestion, validation,
SQL load or EDA task failed in the three observed runs. PowerShell's
NativeCommandError formatting of Docker progress on stderr is not itself a Docker
failure; successful build/startup exit codes and service/run evidence are retained.

## Resource and submission limits

Docker settings and actual VHDX files confirm D:\DockerData\DockerDesktopWSL.
Preflight host free RAM recovered to 2,631,460 KiB; D: had 48,364,740,608 free bytes.
Docker engine memory was 8,215,236,608 bytes (~7.65 GiB). A later host free-memory
snapshot was 1,859,160 KiB. Peak RAM/long-term reliability were not measured.

No Part 1 runtime blocker remains from this controlled test. Genuine Airflow UI,
Graph View, schedule and SQL/EDA screenshots still need capture using the checklist;
chart PNG exports are not mislabeled as UI screenshots. Canvas deadline/timezone
and course AI-use policy remain external checks.

Part 1 services are left running and the DAG is unpaused for user inspection at
http://localhost:8080. ML services remain off. To stop this project while preserving
all volumes use docker compose down; do not append --volumes or prune Docker.
This phase stops here; Part 2 requires a separate request.
