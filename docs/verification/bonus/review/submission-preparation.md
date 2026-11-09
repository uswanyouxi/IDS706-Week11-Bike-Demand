# Bonus submission preparation - November 9, 2026, America/New_York

The user's prior 291-file staging operation is retained and refreshed with the reviewed additions. No commit, push, merge, service restart, Docker deletion, production DAG run or production model fit is performed.

## Screenshots

All seven Bonus PNGs exist, decode as images, and are explicitly allowlisted alongside the six unchanged published Parts 1-2 captures. Images 13 and 14 were visually inspected without editing or renaming. See the [actual-content index](../screenshot-guide.md).

- Image 13 shows the real regression-port comparison and case outcomes. It does not include the native/port warning within its crop.
- Despite its filename, image 14 shows policy-level completion/pass-rate bars. It does not show per-agent calls or timings. Those values remain in the actual run reports. A readable capture of that table would strengthen visual evidence.

## Historical log preservation and whitespace

The [pre-cleanup inventory](logs-preservation.json) records byte hashes and original modification timestamps for 98 verification logs. They are checked unchanged. Docker's captured progress lines contain genuine trailing spaces.

The new Bonus-scoped .gitattributes sets only blank-at-eol checking off for *.log in this evidence subtree. It preserves every log byte/timestamp and keeps source/documentation whitespace checking active. It changes neither Git's global configuration nor line-ending normalization. No historical output is cleaned, regenerated or deleted.

## Docker and validation

The earlier reported Linux Engine outage was not reproduced: Docker context desktop-linux reports Linux Engine 29.7.2 with 8,215,244,800 bytes of allocated memory. Existing services were already running; none was started or restarted by this review. The submission script stops on Docker execution failures rather than treating saved results as a fresh runtime success.

The refreshed [machine-readable review](checks.json) records the current read-only production snapshot, 27 independent saved-execution audits, source syntax, Markdown targets, ignored-file probes, secret checks, Compose validation and staged-file count. Production PostgreSQL is read only and compared with the original dataset hash, 731 dates and 3,292,679 rentals. Verified Parts 1-2 algorithms, six original screenshots and frozen Bonus exports are preserved.

New synthetic tests may fit disposable fixtures; they do not retrain production models. Fresh results use separate submission-*.log/xml files, leaving earlier test logs untouched. Earlier 102-test results remain historical records. The review script now reads the fresh JUnit records.

## Scope and remaining grading risks

The strict two-native-classroom-baseline requirement remains partial: the native classroom Airflow DAG was never executed. Regression ports are labeled as adaptations. Candidate validation predictions were not saved, and nine designed fault scenarios do not establish general reliability or superiority. All normal regression policies have the same test metrics. No claim of all bonus points is made.

The exact staging inventory is [bonus-staging.txt](bonus-staging.txt). Review its file count together with checks.json and Git's actual index before committing. No credentials, caches, database storage, ignored classroom cache or unreviewed images are included. The two earlier local scratch audit JSONs remain outside the manifest.

After approval, from the repository root in PowerShell:

~~~powershell
if ((git -c "safe.directory=$PWD" branch --show-current) -ne 'bonus/adaptive-multi-agent') { throw 'Wrong branch' }
git -c "safe.directory=$PWD" diff --cached --check
if ($LASTEXITCODE -ne 0) { throw 'Resolve staged whitespace check failures before committing' }
git -c "safe.directory=$PWD" diff --cached --stat
git -c "safe.directory=$PWD" commit -m "Add verified adaptive multi-agent bonus and submission evidence"
~~~

The commit command is supplied for the user; it has not been executed. No push or merge is authorized or included.
