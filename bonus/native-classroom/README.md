# Native classroom baseline reproduction

The actual seven-task instructor Airflow DAG and completed LangGraph were executed in an isolated Docker project. Instructor task/node/model source remains byte-identical to commit a294145ea9aa4225908ce701c06160c33213335d. The Bike Demand pipeline and adaptive algorithms are unchanged.

## Verified results

| System | Run | Actual result |
| --- | --- | --- |
| Airflow 2.10.4 | native_prep_01 | Seven successful tasks; validation F1 0.0500; 1,600 train / 400 validation rows |
| Original LangGraph, no-key heuristics | native_simple_02 | Three cycles; best validation F1 0.056604; held-out F1 0.059113 / accuracy 0.5225 |

Both use the exact DAG-published sample: 2,000 fraud-classification rows, including 60 positives. Native DAG validation and native graph holdout have the same 400 row indices; they are not independent populations. The graph's 0.8 target was not met. Iteration-limit warnings remain in both workflows.

[Full results/tests](../../docs/verification/bonus/native-classroom/results.md), [comparison](../COMPARISON.md) and [manual screenshot instructions](../../docs/verification/bonus/native-classroom/capture-guide.md) explain the qualifications. The earlier native_simple_01 folder preserves an observer import failure before fitting; no historical output was overwritten.

## Environment and isolation

- Project ids706-classroom-native-v1: its own database, bridge and four named volumes.
- Built image ids706-native-airflow:2.10.4-py3.11; direct pins: pandas 2.1.4, NumPy 1.26.4, scikit-learn 1.5.2 and SciPy 1.14.1.
- Native graph worker reuses ids706-ml:1.0.0, with original reference sources mounted read only and networking disabled.
- LocalExecutor has one task slot and one parser, with 300-second reparse intervals and no redundant log server. Native task logs are shared with its webserver.
- Worker cap 768 MiB, webserver 768 MiB, scheduler 1 GiB, viewer 256 MiB, PostgreSQL 256 MiB. Work is serialized.
- The Windows host driver keeps the **2.5 GiB available-RAM gate**, checks guest memory and D: headroom, and verifies original service IDs/start times.
- New credentials live only in ignored artifacts/native-classroom-local/.env. The original project .env is never copied into this stack.

The native scheduler is stopped after its completed manual run to save memory; evidence UIs use persisted records. The original project scheduler remains running.

## Inspect current evidence

Airflow: http://localhost:8088, user native_admin with the local native password. Viewer: http://localhost:8503. Native Airflow API verification confirmed native_prep_01 and all seven successful tasks; Streamlit AppTest confirmed real metric tables and compiled graph without application exceptions.

These commands start only the named native page after its resource gate, without training or rebuilding:

~~~powershell
py -3.11 bonus/native-classroom/control.py web
py -3.11 bonus/native-classroom/control.py viewer
~~~

To observe the already completed run, use the UI or exported reports. Do not rerun loop merely to capture screenshots: native run directories deliberately refuse overwrite.

## Fresh reproduction

Use Windows PowerShell, Python 3.11 and Docker Desktop Linux/WSL2. A fresh Docker project is required: prepare refuses existing native containers/volumes rather than reinitializing their evidence. Select a new host output group because the repository retains the original runtime exports.

~~~powershell
$group = 'native_classroom_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
py -3.11 bonus/native-classroom/control.py prepare --evidence-group $group
py -3.11 bonus/native-classroom/control.py build --evidence-group $group
py -3.11 bonus/native-classroom/control.py start --evidence-group $group
py -3.11 bonus/native-classroom/control.py airflow --evidence-group $group
py -3.11 bonus/native-classroom/control.py pause-scheduler --evidence-group $group
py -3.11 bonus/native-classroom/control.py loop --evidence-group $group
py -3.11 bonus/native-classroom/control.py viewer --evidence-group $group
py -3.11 bonus/native-classroom/control.py web --evidence-group $group
py -3.11 bonus/native-classroom/control.py export --evidence-group $group
~~~

Skip build when the matching verified image already exists. The current reproduction reused the previously built image. Fresh successful graph ID defaults to native_simple_01; this checkout's actual successful ID is native_simple_02 because its initial pre-training wrapper failure is retained.

The driver fetches missing public references by immutable commit and verifies all 14 file hashes. It creates only new local credentials and preservation snapshots. Stop on any failed gate; do not delete volumes or change existing services to bypass it.

## Validation and provenance

~~~powershell
py -3.11 bonus/native-classroom/test_isolation.py
py -3.11 bonus/native-classroom/verify_native.py docs/verification/bonus/native-classroom/runtime/native_classroom_01/artifacts
~~~

The verifier checks actual task/XCom/events, shared publication bytes, budgets and emitted metrics without refitting classifiers. Sixteen lightweight tests cover isolation, memory-gate enforcement, missing evidence and log preservation. Fresh original regression tests, read-only PostgreSQL assertions and the original real DAG-import test are linked in the results report.

[Source pins](source-pins.json) and [instructor/data attribution](ATTRIBUTION.md) accompany the code. Reference code lives in an ignored separate cache, not the student's adaptive agents. The old CLI helper is not equivalent to the native DAG: it changes sampling, preprocessing and splits.

Native classification is separate from the preserved Bike Demand regression ports. No cross-task F1/RMSE ranking, LLM-enabled benchmark, predictive superiority or full-Bonus-credit claim is made.
