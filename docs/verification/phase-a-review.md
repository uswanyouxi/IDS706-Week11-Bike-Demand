# Final Phase A configuration review

**Follow-up correction:** see [phase-a-followup.md](phase-a-followup.md). The direct
Python init command does not receive the entrypoint DB wait; the init script now
performs its own bounded readiness check. Admin-role verification, a runner umask
and expanded mocked tests supersede the earlier descriptions/counts below.

Reviewed November 8, 2026 (America/New_York). Phase B is not implemented.
The user confirmed Docker Desktop's WSL2 disk image is currently on C: with about
9.9 GB free and will move it to D: themselves using Docker Desktop settings.
This review did not move/delete Docker data, change system settings, build/pull
images, start containers, run migrations, push, or deploy.

## Changes made

| File | Change and reason |
| --- | --- |
| compose.yaml | Set parallelism=2, max_active_tasks_per_dag=2 and max_active_runs_per_dag=1. Set API workers=1, DAG parsing processes=1 and OMP/OpenBLAS/MKL/NumExpr threads=1 to avoid oversubscribing the 16 GB host. Add shared persistent API secret. Replace best-effort entrypoint init flags plus `version` with explicit checked init. |
| Dockerfile.airflow | Copy the container init script into the image. Base image and package pins unchanged. |
| scripts/init_airflow.py | Explicit metadata migration and migration check; create FAB admin only if absent; fail on errors without a password-bearing command traceback. Preserve existing users/passwords. Only executed on later container startup. |
| .env.example, scripts/new_local_env.py | Include a distinct random AIRFLOW_API_SECRET_KEY for new checkouts. |
| ignored .env | Append only the previously missing API secret. Existing passwords, JWT and Fernet values were not rotated or printed. |
| docs/architecture.md | Synchronize the two-slot design and init contract; require real in-DAG downloads and application-DB model input. |
| README.md | Explain raw host files versus named volume, explicit ML activation, revised init, resource/storage preflight and review link. |
| docs/verification/environment.md | Record the user's confirmed C: location and planned self-managed move to D:, retaining original measurements. |
| tests/unit/test_init_airflow.py, tests/README.md | Add three pure mocked init safety checks and their exact invocation; no pipeline tests or success claims. |
| docs/checklist.md, docs/verification/versions.md | Link the current review and update the remaining storage check. |
| docs/verification/phase-a-review-checks.json | Save sanitized static-check outcomes; no credentials or interpolated Compose dump. |
| this document | Record the review, validation limits, startup risks and full change list. |

No hard container RAM limits were guessed: arbitrary caps could OOM the scheduler
and both task subprocesses. Two task slots limit simultaneous task work, not total
stack memory. One parser affects DAG discovery, not ingestion concurrency. Phase B
must explicitly use `max_active_tasks=2`, `max_active_runs=1`, no cross-branch edge,
and leave at least two slots in its pool. Actual overlap still requires runtime
execution evidence; it has not been demonstrated yet.

## Airflow 3.4.0 compatibility review

The [version-specific Docker guide](https://airflow.apache.org/docs/apache-airflow/3.4.0/howto/docker-compose/index.html),
[configuration reference](https://airflow.apache.org/docs/apache-airflow/3.4.0/configurations-ref.html),
[CLI reference](https://airflow.apache.org/docs/apache-airflow/3.4.0/cli-and-env-variables-ref.html)
and [release entrypoint source](https://github.com/apache/airflow/blob/3.4.0/scripts/docker/entrypoint_prod.sh)
were checked. This is a source/static compatibility review, not a running-stack certification.

| Area | Review result |
| --- | --- |
| LocalExecutor | Retained. Executes task subprocesses in the scheduler; no Redis/Celery worker needed for these two small branches. |
| FAB | Correct configured import and provider pin retained. Init uses FAB `users list/create`; a successful real login is still unverified. |
| API Server | `api-server` retained, one worker, both core/execution apps enabled by default, localhost port 8080. |
| Scheduler / DAG Processor | Separate `scheduler` and `dag-processor` commands retained. No Airflow 2 webserver command introduced. |
| Init | Official entrypoint sets runtime umask; explicit Python init now owns the DB readiness check, migration/check-migrations, conditional user creation and Admin-role verification. |
| JWT | Same nonempty api_auth JWT secret and issuer `ids706-local` on all Airflow processes; correct internal execution URL `http://airflow-apiserver:8080/execution/`. |
| API secret | Persistent api.secret_key supplied separately from JWT/Fernet across Airflow processes; avoids different generated keys after restarts. |
| PostgreSQL | Separate metadata/application PostgreSQL services and volumes; psycopg SQLAlchemy URL retained; no published DB ports. |
| Health checks | Official API `/api/v2/monitor/health`, SchedulerJob and DagProcessorJob CLI checks, plus pg_isready retained. These are source-compatible checks; they have not executed in containers. |

The API HTTP check alone tests reachability: an HTTP 200 is not proof every
reported component is healthy. Read its JSON health statuses during the later
smoke test, along with independent scheduler/DAG-processor heartbeats, DB checks,
init exit status and login. `depends_on` gates initial startup, not ongoing
recovery of dependencies. JWT use also requires consistent system time.

The release entrypoint uses `|| true` for both migration and user creation.
Previously, `command: version` could mask those errors. Removing the special init
flags and calling checked commands explicitly closes that gap. Existing accounts
are not reset on reruns; if their password/role was manually changed, inspect it
rather than expecting .env to overwrite it. Rebuild the Airflow image after init
script edits because the script is copied into the image, not bind-mounted.

The base remains `apache/airflow:3.4.0-python3.11`. The remote official 3.4.0 Python
3.11 constraint bytes were compared with the vendored file and matched exactly:
SHA-256 `22ac327cdf6fe75b8d873ab363455bbe0645c03cee3e3896c6513d583c25e5f8`.
Standard 1.21.0, postgres 7.1.1 and FAB 3.10.2 match that constraint snapshot.
The Dockerfile repeats the core pin during pip installation and retains `pip check`.
Matplotlib is an explicitly pinned extra, not a fabricated entry in the official
constraints. Prior dependency dry-run evidence remains applicable because package
pins did not change; an actual Linux image build/pip check remains pending.

## Data and ML input contracts

| Storage | Purpose |
| --- | --- |
| Windows `./data/raw/` | Phase A verifier downloads only; Git-ignored, Docker-build-excluded, not mounted into the pipeline volume. |
| Logical Compose `project-data` | Docker named volume, normally `ids706-bike-demand_project-data`, mounted as `/opt/project/data` in Airflow. Future tasks download UCI and Open-Meteo inside the DAG and store run-scoped raw/cleaned artifacts here. |
| `app-db` / `bike_demand` | Persisted final cleaned dataset; fresh SELECTs provide EDA and agent input. Model snapshot exports must originate from this DB, not raw files or Airflow metadata. |

The host's source verifier is not an ingestion task. A later genuine DAG run must
request both real endpoints and record URL, timestamp, parameters and checksums.
An offline fixture/cache path must be explicit and labeled. The LangGraph load
node will read the cleaned app DB in a consistent snapshot before freezing the
model dataset; its implementation is still deferred.

Both ML services retain `profiles: [ml]`; default services exclude them when
COMPOSE_PROFILES does not enable ml. Explicit service targets also activate a
profiled service. `--profile ml up` without a target starts both dashboard and
runner; use `--profile ml up -d dashboard` and a separate explicit runner command
when those phases are ready. The runner remains an unimplemented placeholder.

## Verification actually run

- Both default and ml-profile Compose JSON configurations parsed successfully.
- Default model contains seven services; ml model contains nine. ML is absent by default.
- Resolved Airflow settings, shared/distinct secrets, execution URL, init dependency
  contract, separate DB volumes, nonpublished DB ports and loopback UI bindings checked.
- All eight project/test Python files parsed; three mocked init tests passed:
  migration failure blocks subsequent work, existing user preserved, and user
  creation failure does not expose the supplied password in its exception.
- .env still matches Git's ignore rules. No credentials were printed or staged.
- Exact remote/local constraint equality verified; packages were not reinstalled.

Read-only/static commands included:

```powershell
docker compose config --quiet
docker compose --profile ml config --quiet
py -3.11 -B -m unittest discover -s tests/unit -p test_init_airflow.py -v
git -c safe.directory='D:/未来/IDS706/IDS706-Week11-Bike-Demand' check-ignore .env
```

The review also parsed `docker compose [--profile ml] config --format json` only
in memory and persisted sanitized assertions to phase-a-review-checks.json. Do
not dump the full interpolated config into logs because it includes credentials.
The sandbox setup still fails; approved outside-sandbox execution was used for
project-local edits and checks. This did not change global Git trust or execution policy.

## Remaining blockers and Windows startup risks

1. Finish your move of Docker's disk image from C: to D: through Docker Desktop,
   then confirm the new disk location/free space before building. No Docker data
   was touched by this review. Relocating the project directory alone is insufficient.
2. Release host RAM before starting. The previous ~1.56 GiB free measurement is
   historical, not a current guarantee. The tuned 7.65 GiB engine may be sufficient
   for this small stack, but peak usage and OOM behavior remain unmeasured.
3. Windows folder sharing/read permission must permit read-only DAG/src bind mounts.
   Keep Linux volume permissions separate from NTFS permissions. The root-only
   storage initializer touches three named-volume roots, not host paths; nonroot
   Airflow uses group 0. Actual volume permissions remain a runtime check.
4. Use the accessible desktop-linux engine and quoted PowerShell paths when needed.
   No native WSL user-shell distribution was tested. The Store Python launcher and
   Docker pipe require access outside this session's sandbox; `python` is not on PATH.
5. Keep .env intact/private. Regenerating it does not change passwords inside an
   already initialized Postgres volume; do not delete volumes to resolve a mismatch.
   An older checkout missing AIRFLOW_API_SECRET_KEY will fail Compose interpolation;
   this workspace's existing .env has already been supplemented safely.
6. Port availability, image builds, Linux dependency imports/pip check, init migration,
   volume writes, FAB login, component health and real DAG parallelism remain untested.
   No claim of runtime readiness or Phase B completion is made.