# Phase A init and shared-permission follow-up

Completed November 8, 2026 (America/New_York). No containers were started, images
built/pulled, migrations executed, Docker data modified/deleted, system settings
changed, or Phase B code implemented. Sandbox setup still fails; project-local
edits and read-only checks used approved outside-sandbox execution.

## Findings and corrections

**Init path was already correctly packaged.** Dockerfile.airflow contains:

```dockerfile
COPY --chown=airflow:root scripts/init_airflow.py /opt/project/scripts/init_airflow.py
```

The source file exists, is not excluded by .dockerignore, and no common/init mount
covers /opt/project/scripts or an ancestor. No scripts bind mount is necessary.
Dockerfile.airflow was left unchanged. A fresh image build will include the file;
this review cannot certify an old/stale image or inspect a running container.
Rebuild the Airflow image before the later startup test.

**Corrected the earlier entrypoint DB-wait statement.** The exact
[Airflow 3.4.0 entrypoint](https://github.com/apache/airflow/blob/3.4.0/scripts/docker/entrypoint_prod.sh)
only performs its DB wait for component commands, not a direct Python command.
It still sets umask 0002 before Python passthrough. The init script now explicitly
runs `airflow db check --retry 20 --retry-delay 3` before migration, with a 90-second
subprocess ceiling. It then runs migrate (600-second ceiling) and check-migrations
(60-second migration wait, 90-second subprocess ceiling). Readiness or migration
failure prevents user creation and dependent Airflow startup.

**FAB administration is checked, not assumed.** The published FAB 3.10.2 wheel's
user CLI source was inspected in memory through its
[official PyPI release](https://pypi.org/project/apache-airflow-providers-fab/3.10.2/).
Its JSON users-list exposes role objects, normalized to role-name arrays by
[Airflow 3.4.0's JSON formatter](https://github.com/apache/airflow/blob/3.4.0/airflow-core/src/airflow/cli/simple_table.py).
Init rejects malformed lookup output, checks the configured username, creates it
with role Admin only when absent, then rereads and verifies that role. An existing
non-admin fails with a safe diagnostic; it is not silently promoted. A valid
existing administrator and password remain untouched on rerun. CLI listing does
not expose account active status or verify password correctness; actual login
remains untested.

Every CLI call captures raw output and has a timeout. Known failures report only
the safe stage and exit status; errors never interpolate password-bearing argv,
raw CLI output, or TimeoutExpired into logs. The console shows the current stage.
This reduces diagnostic detail intentionally; a failing runtime stage still needs
inspection in the container without copying credentials into shared logs.

**Different UIDs can share the artifact volume through GID 0.** storage-init runs
as root and changes only the three named-volume roots to owner 50000, group 0,
mode 2775. ml-runner runs as 10001:0 and therefore uses the group write/traverse
permissions. The setgid bit makes normal newly created subdirectories inherit GID
0. Its command now sets umask 0002 before the unchanged Phase A runner placeholder,
so usual mkdir(0777)/file(0666) operations produce group-writable 2775 directories
and 0664 files, without world write. The dashboard keeps its read-only mount.
No chmod 777, recursive ownership change, host permission change, or actual volume
operation was run. Existing restrictive descendants and deliberately private
creation modes still need targeted inspection if runtime access fails.

## Official configuration and dependency checks

All **17 configured AIRFLOW__ variable names** were checked against the
[Airflow 3.4.0 configuration reference](https://airflow.apache.org/docs/apache-airflow/3.4.0/configurations-ref.html).
AIRFLOW_ADMIN_USERNAME/PASSWORD and APP_DB_* are project variables consumed by our
code; numeric thread variables belong to their libraries. They are not claimed
as Airflow core configuration options. The versioned official Compose reference
was fetched and matched FAB, component commands, API health endpoint and job-check
tokens. The Python 3.11 official constraint bytes still match the vendored file
exactly; the base image, package pins and Dockerfile installation rules did not change.

Static dependency assertions passed:

- airflow-init waits for healthy airflow-db and completed storage-init.
- API Server and DAG Processor wait for successful airflow-init.
- Scheduler waits for healthy API Server and application DB.
- ML runner waits for completed storage-init and healthy application DB.
- Shared JWT/API-secret values are consistent; the API secret is distinct from JWT.
- The default configuration excludes dashboard and runner; ml explicitly includes both.
- Database ports remain unpublished, UI ports bind to loopback, and DB volumes differ.

The API HTTP check alone proves reachability, not every status in its JSON. Health
commands were reviewed statically, not run against live components. No actual DAG
exists yet, so concurrency=2 is available capacity, not proven branch overlap.

## Checks actually passed

Commands:

```powershell
py -3.11 -B -m unittest discover -s tests/unit -p test_init_airflow.py -v
docker compose config --quiet
docker compose --profile ml config --quiet
git -c safe.directory='D:/未来/IDS706/IDS706-Week11-Bike-Demand' check-ignore .env data/raw/day.csv
```

All 12 mocked unit tests passed:

1. test_db_readiness_is_bounded_and_blocks_migration
2. test_existing_admin_is_preserved
3. test_existing_nonadmin_fails_without_grant_or_reset
4. test_failed_migration_blocks_user_creation
5. test_failed_migration_verification_blocks_user_lookup
6. test_failed_user_creation_excludes_password_from_exception
7. test_malformed_users_json_fails
8. test_missing_user_after_successful_create_fails
9. test_new_admin_is_created_then_role_verified
10. test_placeholder_credentials_fail_before_cli
11. test_second_run_does_not_recreate_admin
12. test_timeout_does_not_expose_secret_argv

The subprocess layer is mocked: none of these invokes Airflow or connects to a
DB. Eight Python source/test files parsed successfully. Additional one-shot
assertions inspected Compose JSON only in memory, checked COPY/build exclusions,
mount coverage, dependency conditions, mode bits/umask, profile behavior, secret
consistency and official reference names. Results are in
[phase-a-followup-checks.json](phase-a-followup-checks.json), which contains no secrets.

The source checks were an **offline integrity recheck of previously downloaded
real sources**, not fresh remote dataset/API requests. Both ZIP/weather hashes
match sources.json; extracted day.csv matches the host CSV byte-for-byte. UCI has
731 rows/16 columns, no empty cells and the count-component identity. Weather has
five finite numeric arrays of length 731, correct temperature ordering and
nonnegative precipitation/wind. Both date sequences match exactly, including
leap day; timezone metadata remains America/New_York. Historical fetch evidence
and raw files were preserved unchanged. Fresh documentation/constraint/source-code
requests above were separate read-only network checks.

## Exactly which files changed in this follow-up

1. compose.yaml — corrected init comment; added ML runner umask.
2. scripts/init_airflow.py — explicit readiness, strict Admin verification,
   bounded subprocesses, safe stage-specific failure handling.
3. tests/unit/test_init_airflow.py — expanded from 3 to 12 mocked tests.
4. README.md — current init behavior and link to this follow-up.
5. docs/architecture.md — corrected DB-wait contract and artifact permissions.
6. tests/README.md — current mocked-test scope/count.
7. docs/verification/phase-a-review.md — clearly superseded prior DB-wait/count claims.
8. docs/verification/phase-a-followup-checks.json — new sanitized check evidence.
9. docs/verification/phase-a-followup.md — this report.

Dockerfile.airflow, Dockerfile.ml, .dockerignore, package pins, .env and existing
source evidence/raw downloads were not modified by this follow-up.

## Still requires runtime verification

- Confirm the user's Docker disk-image move to D: and available disk/RAM headroom.
- Build the image, verify the init script inside it, and run Linux dependency checks.
- Exercise actual PostgreSQL readiness/migration, FAB creation/repeated init and login.
- Test real writes/reads across UIDs 50000 and 10001 on nested artifact paths.
- Inspect API JSON health and Scheduler/DAG Processor heartbeats, port availability
  and actual peak resource use. Any old restrictive volume contents need a targeted
  review, not blanket recursive chmod or deletion.
- Only after Phase B implementation: verify genuine task overlap, pipeline downloads,
  transactional DB load and database-fed EDA. No such results are claimed here.