# Final submission preparation — November 9, 2026

Parts 1 and 2 passed real runtime verification before this submission review. All six real screenshots are present and were visually inspected. No pipeline/ML algorithm was changed, and no production DAG execution, model retraining, database writes, service restart, secret regeneration, staging, commit or push was performed.

## What belongs in Git

The exact current file list is [submission/commit-files.txt](../submission/commit-files.txt), one project-relative path per line. It is generated from normal Git eligibility and checked for secrets, required files and ignored dependencies. Review the complete file, rather than staging the workspace indiscriminately.

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

## Actual final checks

[Machine-readable checks](verification/final-submission/checks.json) record current counts and results.

- Pipeline unit tests: **39 passed**.
- ML unit tests in the existing dashboard container: **19 passed**, one upstream pending-deprecation warning.
- Real Airflow DAG-import/configuration test: **1 passed**.
- Tests used synthetic ML fixtures and temporary directories; no production retraining or DAG run occurred.
- Source AST parsing, local Markdown targets, six PNG files/hashes, both Compose profiles, candidate-file secret scan and ignore-rule probes are checked.
- Saved predictions independently reproduce actual MAE/RMSE. One selected-model test prediction is negative; it remains unchanged.
- Implementation/configuration and original binary/machine-readable/log evidence must match the before snapshot. Only authorized documentation and .gitignore are amended.

Logs/JUnit XML live in docs/verification/final-submission/. Prior phase evidence is retained in place. Historical phase preservation baselines include documentation that has now intentionally changed; the final checker provides a new explicit boundary without rewriting those original baselines.

## Files changed during final preparation

Existing files updated: .gitignore, README.md, screenshots/README.md, docs/checklist.md, dashboard/README.md, docs/verification/phase-c/capture-guide.md and submission/part1/capture-guide.md. Historical-status banners were added to docs/verification/phase-b/status.md, docs/verification/phase-c/status.md and submission/part1/README.md; original runtime narratives/results remain underneath.

New files: docs/running.md, docs/submission.md, scripts/check_submission.py, submission/commit-files.txt and the final-submission verification directory (before hashes, fresh test logs/JUnit XML and checks.json). No existing algorithm, test, dependency pin, Dockerfile or Compose setting changed.

The recommended manifest currently contains **317 files**. The only screenshot files eligible for normal staging are the six reviewed PNGs plus their README. Original authoring prompts, starter instructions and local runtime/build storage remain present locally and ignored.

## Exact recommended staging commands — not executed

Run from the project root in PowerShell after reviewing the manifest:

~~~powershell
py -3.11 scripts/check_submission.py
Get-Content -Encoding UTF8 submission/commit-files.txt
git -c "safe.directory=$PWD" --literal-pathspecs add --pathspec-from-file=submission/commit-files.txt
git -c "safe.directory=$PWD" diff --cached --check
git -c "safe.directory=$PWD" diff --cached --stat
git -c "safe.directory=$PWD" status --short
~~~

The project-scoped safe.directory option addresses the local sandbox-account ownership difference without changing global Git settings. Do not use git add -f. No commit/push command is authorized or executed. Approval is required before either action.

To regenerate the manifest after deliberately adding/removing submission files, use py -3.11 scripts/check_submission.py --write-manifest, then inspect the exact list again.

## Remaining issues

No required screenshot category is missing. Optional schedule/SQL/EDA screenshots are not claimed; their existing reports and actual EDA PNGs are sufficient supporting evidence. Screenshot 07 truncates some reason text horizontally; screenshot 08 and the original JSON show the full routing decisions.

This is an observed-weather retrospective backtest. Ridge produced one negative prediction among 184 held-out dates; no post-test clipping/tuning was applied. Optional Part 3 was not implemented, compared or evaluated and is not claimed.

Canvas's deadline/timezone and course AI-use/submission instructions require your own confirmation. Staging, committing and pushing are pending user review/approval.
