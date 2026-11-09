# Submission status and verification — November 9, 2026

**Required Parts 1 and 2 are completed, runtime-verified, committed and pushed to [GitHub main](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/main).** The published baseline is [4d4d65f](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/commit/4d4d65f0a6efba1d6b56d2b982963434ffefc713): 317 files and six real screenshots. Part 3 is optional and is not part of the verified main branch.

The earlier preparation checks did not stage, commit or push; publication happened afterward. That historical scope remains accurate in the frozen logs. This documentation cleanup changes no pipeline, ML, Docker, database or credential logic, and repeats no production execution.

## What belongs in Git

The published 317-file inventory is [submission/commit-files.txt](../submission/commit-files.txt), one project-relative path per line. It was checked for secrets, required files and ignored dependencies. The categories below explain what is included; subsequent updates should stage only their intended files.

| Category | Include / rationale |
| --- | --- |
| Root setup | README, Dockerfiles, compose.yaml, .env.example, .dockerignore, .gitignore, .gitattributes, pytest.ini |
| src/, dags/, agents/, dashboard/, sql/ | Original executable pipeline and agent workflow, UI, migrations and SQL verification |
| requirements/, scripts/, tests/ | Pinned requirements/constraints, setup/check/export utilities, meaningful unit/integration tests |
| assignment/ | User-supplied assignment/TA/project specification for traceability |
| docs/ and submission/part1/ | Setup/architecture/source documentation and frozen runtime/SQL/idempotence evidence |
| docs/verification/phase-c/runs/ | Frozen database provenance, features/splits, candidates, routing/events, actual metrics/predictions/plots, small selected model and controlled failure evidence |
| docs/verification/final-submission/ | Current source/evidence hashes, test logs/JUnit and final link/secret/ignore checks |
| screenshots/ | README and exactly the six reviewed PNG files |
| data/raw/.gitkeep, artifacts instructions/.gitkeep | Empty directory scaffolding only |

Recorded build/task logs are verification evidence, not build products. They remain included alongside their reports/manifests to preserve auditability. The small frozen selected_model.joblib is intentionally retained because the run manifest hashes it. Other generated models remain ignored.

Keep these local and ignored: .env and other non-example environment files, credentials/keys, virtual environments/caches, local raw downloads and regenerated artifacts, Docker/database directories/disks/dumps, build/dist/node_modules, and unreviewed screenshots. The original README_FIRST.md/prompts/ authoring archive is preserved locally but excluded from submission. Git ignore rules apply to ordinary staging; never force-add secrets or bulk-add ignored files.

## Recorded runtime and submission checks

[Machine-readable checks](verification/final-submission/checks.json) preserve the original pre-publication counts, results and timestamp. They are historical evidence, not a live Git-status report.

- Pipeline unit tests: **39 passed**.
- ML unit tests in the existing dashboard container: **19 passed**, one upstream pending-deprecation warning.
- Real Airflow DAG-import/configuration test: **1 passed**.
- Tests used synthetic ML fixtures and temporary directories; no production retraining or DAG run occurred.
- Source AST parsing, local Markdown targets, six PNG files/hashes, both Compose profiles, candidate-file secret scan and ignore-rule probes are checked.
- Saved predictions independently reproduce actual MAE/RMSE. One selected-model test prediction is negative; it remains unchanged.
- Implementation/configuration and original binary/machine-readable/log evidence must match the before snapshot. Only authorized documentation and .gitignore are amended.

Logs/JUnit XML live in docs/verification/final-submission/. Prior phase evidence is retained in place. Historical phase preservation baselines include documentation that has now intentionally changed; the final checker provides a new explicit boundary without rewriting those original baselines.

## Historical preparation changes

Existing files updated: .gitignore, README.md, screenshots/README.md, docs/checklist.md, dashboard/README.md, docs/verification/phase-c/capture-guide.md and submission/part1/capture-guide.md. Historical-status banners were added to docs/verification/phase-b/status.md, docs/verification/phase-c/status.md and submission/part1/README.md; original runtime narratives/results remain underneath.

New files: docs/running.md, docs/submission.md, scripts/check_submission.py, submission/commit-files.txt and the final-submission verification directory (before hashes, fresh test logs/JUnit XML and checks.json). No existing algorithm, test, dependency pin, Dockerfile or Compose setting changed.

The published manifest contains **317 files**. The only screenshot files eligible for normal staging are the six reviewed PNGs plus their README. Original authoring prompts, starter instructions and local runtime/build storage remain present locally and ignored.

## Documentation-only follow-up for review

This cleanup updates only README.md, screenshots/README.md and docs/submission.md. The published baseline, source, Docker configuration, database logic, screenshots and historical runtime evidence remain unchanged.

Proposed commit message: **docs: clarify published Parts 1 and 2 submission status**.

Review/staging commands below are for a later approved action; this cleanup does not create a commit or push:

~~~powershell
git -c "safe.directory=$PWD" diff -- README.md screenshots/README.md docs/submission.md
git -c "safe.directory=$PWD" add -- README.md screenshots/README.md docs/submission.md
git -c "safe.directory=$PWD" diff --cached --check
git -c "safe.directory=$PWD" diff --cached --stat
~~~

The project-scoped safe.directory option handles the local sandbox-account ownership difference without changing global Git settings. Do not force-add ignored files. Obtain approval before committing or pushing these documentation changes. Preserve existing verification logs and timestamps; do not rerun historical report writers solely to refresh publication wording.

## Remaining issues

No required screenshot category is missing. Optional schedule/SQL/EDA screenshots are not claimed; their existing reports and actual EDA PNGs are sufficient supporting evidence. Screenshot 07 truncates some reason text horizontally; screenshot 08 and the original JSON show the full routing decisions.

This is an observed-weather retrospective backtest. Ridge produced one negative prediction among 184 held-out dates; no post-test clipping/tuning was applied. Optional Part 3 is not part of the verified main branch; no bonus comparison or evaluation is claimed.

Canvas's deadline/timezone and course AI-use/submission instructions require your own confirmation. The required project is already published; any further documentation commit and push require user approval.
