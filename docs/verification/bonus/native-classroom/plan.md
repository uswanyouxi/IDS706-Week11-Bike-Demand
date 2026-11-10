# Native classroom baseline reproduction: implementation plan

Status: source/resource inspection complete; no image build, new container, native DAG run or model fit performed. Runtime requires explicit user approval under the attached request.

## Scope and isolation

Work remains on bonus/adaptive-multi-agent, currently at a8715ad. Existing documentation edits and the author's policy-chart rename are retained. Required Parts 1-2, production PostgreSQL, adaptive code, original 27 evaluation executions, models and screenshots are preserved.

The new project directory is bonus/native-classroom. Its Compose project will be **ids706-classroom-native-v1**, which currently has no containers or volumes. It will have its own bridge network, metadata database, credentials, source cache, logs, working repository and evidence volumes. No existing project volume, service definition, database connection or network will be attached.

Only localhost ports **8088** (native Airflow) and **8503** (native evidence viewer) will be published; neither was listening during inspection. The original 8080/8501/8502 applications remain untouched. New local credentials will be isolated in an ignored .env; existing credentials are neither read into the new stack nor regenerated.

## 1. Verified original sources

Reference: Kedar-V/automl-research-lab at **a294145ea9aa4225908ce701c06160c33213335d**. [Pinned file identities](../../../../bonus/native-classroom/source-pins.json) cover 14 original files, verified with Git blob SHA-1 and SHA-256. Original code is kept in an ignored separate cache, artifacts/native-classroom-reference, with attribution.

| File | Executable status / consequence |
| --- | --- |
| solution/airflow/dags/solution_baseline_prep.py | Complete seven-task DAG; execute this exact file under Airflow 2.10.4 |
| solution/airflow/dags/solution_baseline_and_trigger.py | Complete prep plus an eighth trigger_solution_loop STUB; not evidence of a working Airflow-to-LangGraph trigger |
| solution/langgraph/graph.py | Complete seven-agent StateGraph, memory/context loop, judge router, bounded cycles and holdout |
| solution/langgraph/baseline.py | Complete CLI helper, but **not numerically equivalent to the DAG** |
| loop_runtime.py | Complete training, classification metrics, fit repair and documented no-key heuristics |
| lab/airflow/dags/lab_baseline_prep.py | Student stub: NotImplementedError bodies and commented wiring |
| lab/langgraph/graph.py | Student stub: incomplete nodes/router/build_graph |
| infra/docker-compose.yml / infra/Dockerfile.airflow | Classroom Airflow 2.10.4/Python 3.11, LocalExecutor and PostgreSQL; the full stack also starts unrelated services, so it will not be launched |

The native DAG uses a non-stratified 2,000-row sample (seed 42), numeric-only LogisticRegression, and a stratified **80/20 train/validation** split. It reports validation F1 and row counts; it has **no held-out test stage or accuracy output**.

The old CLI helper instead uses proportional class sampling, categorical preprocessing and **60/20/20** partitions. Earlier CLI F1 must not be labeled as the native DAG result. The new native DAG metrics will have new evidence paths and will not replace old observations.

Original source data: 1,000 customer rows and 10,000 transactions, with is_fraud counts 9,694 negative / 306 positive. Inputs are the actual pinned classroom CSVs, not regenerated data. Their attribution describes synthetic educational Kaggle data, CC BY-NC-SA 4.0.

## 2. Runtime resource assessment and gates

See [measured resources](resource-assessment.json). Docker Engine 29.7.2 is reachable with 20 logical CPUs and about 7.65 GiB total memory. Latest host available memory was about 2.76 GiB; guest MemAvailable about 5.66 GiB. D: has about 52.2 GiB free; C: about 11.7 GiB. Docker VHDX files were found under D:/DockerData/DockerDesktopWSL/.

Existing seven containers consume about 1.29 GiB in aggregate at inspection. These observations are instantaneous, not a peak guarantee. They do not establish free filesystem capacity inside Docker's virtual disk.

Immediately before build/start and before each model run, recheck:
- Host free physical memory at least **2.5 GiB**.
- Guest MemAvailable at least **4 GiB** before stack startup; account for new running services before the serial worker.
- Docker-image drive free space at least **25 GiB**; check internal virtual-disk filesystem headroom during approved preflight.
- Correct unused project/ports, preserved existing service IDs/start times, no existing native output directory.

If these gates fail, do not force startup or change system settings. Wait for user-managed resource headroom. Start only the requested native services, not the instructor's full application stack.

| New service | Memory cap | CPU cap | Lifecycle |
| --- | ---: | ---: | --- |
| native-storage-init | 128 MiB | 0.25 | One shot; initializes only new volume roots |
| native-airflow-init | 768 MiB | 1 | One shot; migrate new metadata and create new FAB administrator |
| native-db | 256 MiB | 0.5 | Isolated PostgreSQL metadata |
| native-scheduler | 1 GiB | 1 | LocalExecutor, two task slots, one parser |
| native-webserver | 768 MiB | 0.5 | One worker, localhost:8088 |
| native-loop-worker | 768 MiB | 1 | One serial classification run; no external credentials |
| native-viewer | 256 MiB | 0.5 | Read-only native evidence, localhost:8503 |

Initialization is sequential. The steady Airflow services total 2 GiB in configured caps; with worker and viewer the maximum concurrent caps total **3 GiB**, excluding Docker/build overhead and existing services. Build and worker operations will not overlap. These caps are proposed; runtime adequacy is not claimed.

## 3. Prepare the isolated runtime after approval

Create an additive Compose file and guarded setup/driver under bonus/native-classroom. Build a separate image based on the instructor's **apache/airflow:2.10.4-python3.11**.

Pin Airflow 2.10.4, pandas 2.1.4, NumPy 1.26.4, scikit-learn 1.5.2 and SciPy 1.14.1. The verified official Airflow constraints are vendored alongside [source pins](../../../../bonus/native-classroom/source-pins.json). scikit-learn/SciPy metadata supports the proposed Python/NumPy combination; **dependency resolution, image build and pip check remain unverified**.

Environment deviations from the classroom infrastructure will be explicit:
- Unique project/ports/volumes, isolated credentials, resource/thread limits and loopback-only UI.
- Exact dependency pins replace the instructor's broad ranges; binary wheels avoid unnecessary compiler installation.
- Reuse the already-present postgres:16.11-bookworm instead of pulling postgres:16-alpine; metadata stays isolated.
- Mount the original prep DAG and original input CSVs read only. Use new writable volumes for /repo publication paths and Airflow logs; initialize group permissions only on these new volume roots.
- Keep the original DAG imports, seven task bodies, sample, features, classifier, parameters, split, retries and manual schedule unchanged. If source compatibility edits become necessary, record an exact patch and report that the DAG is modified rather than claiming byte-identical execution.
- The native LangGraph worker reuses ids706-ml:1.0.0 and imports the exact original graph/loop_runtime source, independently of bike_demand_bonus. Record its different dependency versions; do not rank cross-environment execution speeds.

## 4. Execute the real Airflow DAG

After approved build and initialization:
1. Confirm no import errors and exact DAG ID solution_baseline_prep, schedule=None, catchup=False and seven expected tasks/edges.
2. Trigger an actual scheduler-managed run with proposed unique ID **native_prep_01**. Abort if that ID or evidence directory already exists.
3. Poll task/run states to a terminal outcome with bounded wait. Never substitute a Python function call or prep CLI for a DAG run.
4. Require success for validate_customers, validate_transactions, merge_csvs, make_subset, profile_light, train_baseline and publish_merged.
5. Save the real run ID/logical date, API/CLI task states, all task logs, metadata/XCom return values, dependency graph, package versions, image identity and measured durations.
6. Preserve original sample/merged/published bytes and hashes. Independently validate merge size, subset size, classes, publication equality, F1 finite in [0,1], and actual train/validation counts. A valid low F1 is an honest outcome, not a quality success claim. Capture any convergence warnings.
7. Report only the metrics the DAG actually emits. There is no native DAG held-out score or accuracy result.

No native classification result is currently known.

## 5. Run the completed native LangGraph

Use the **same dataset published by the real DAG**, not the old helper's differently sampled output. Run the instructor's exact completed graph with seed=42, target=is_fraud, target_score=0.8, holdout_frac=0.2 and **max_cycles=3**; proposed evidence ID **native_simple_01**.

Unset OpenRouter/Cursor credentials in the isolated worker and verify used_llm=False throughout. Preserve the instructor's no-key heuristics, model-family choices, memory/context, one-pass fit repair and routing. Do not patch the graph to force an outcome.

Save compiled topology, actual stream/step records, validation metrics per cycle, chosen spec, repair flags, verdicts, routes, stop/budget behavior and final held-out F1/accuracy. The native graph uses 60/20/20 random stratified selection partitions and refits on the non-holdout 80% for final testing. Require a single holdout stage and finite metrics, and distinguish unmet 0.8 target from execution failure. Do not promise that a repair path will occur naturally.

The viewer will show these recorded results, source/dataset identities and native/port qualifications. It will not initiate training or write SQL.

## 6. Scientific comparison

Produce two separate report sections:
A. **Native classroom reproduction**: actual Airflow validation F1/counts and actual native LangGraph validation/held-out metrics on the same published fraud subset. Explain different splits, features, preprocessing and dependency versions. No direct F1 ranking across these differing contracts.
B. **Same-problem Bike Demand**: retain the original adaptive/fixed_port/simple_port 27-case regression results, chronological partitions and MAE/RMSE. These are explicit adaptations, not unmodified classroom runs.

Additional fair checks can compare aligned saved per-date regression predictions and matched scenario records without fitting any production model. They will not rerun the existing 27 executions or replace their scores. Native classification F1 will never be compared numerically against regression RMSE. Actual native reproduction closes the missing-execution evidence gap; exact same-problem native-classroom equivalence is not automatically established, and instructor grading remains external.

## 7. New evidence, tests and documentation

Write new runtime evidence only under:
- New native evidence volume, partitioned by native_classroom_01/native_prep_01 and native_classroom_01/native_simple_01.
- Host exports: docs/verification/bonus/native-classroom/runtime/native_classroom_01/.
- New manifests contain source/dataset/image identities, exact commands, resource readings, run/task IDs, timing, actual outcomes, failures and artifact SHA-256.

Run meaningful isolation/provenance/evidence tests, the existing Bonus and Parts 1-2 regression tests with synthetic temporary fixtures, read-only production snapshot verification, source syntax, links, secret scans and final source/evidence hash checks. Production database writes, DAG reruns, model retraining, changes to existing algorithms, screenshot regeneration and historical report overwrites are excluded.

After actual verification, update the concise root README, bonus/COMPARISON.md and screenshot guide with real results. Preserve prior native CLI probes as explicitly different historical experiments. The old submission reviewer has known documentation-baseline incompatibilities; report them, never weaken validation to imply success.

## 8. Screenshot checklist after successful execution

These are proposed files, not existing captures:
- **15_native_airflow_success.png**: http://localhost:8088, DAG solution_baseline_prep, run native_prep_01, successful run and all seven green task states.
- **16_native_airflow_graph.png**: same real DAG/run, Graph showing both validators, merge, subset, profile, train and publish.
- **17_native_airflow_metrics.png**: same run, train_baseline XCom return_value and publish_merged return_value, actual F1/counts/published path; never show credentials.
- **18_native_langgraph_execution.png**: http://localhost:8503, native_simple_01, compiled classroom graph, recorded cycle/revision/repair flags and no-key mode.
- **19_native_classification_results.png**: http://localhost:8503, native classification validation/held-out metrics, subset hash and explicit split differences.
- **20_native_and_regression_scopes.png**: http://localhost:8503, separate native classification and Bike Demand regression sections, with exact adaptation limitations.

If an ID must change, record the real ID in the final capture guide. Do not allowlist or link proposed PNGs as present before genuine captures exist.

## Approval boundary

Requested approval will cover implementing the isolated harness, pulling/building the native Airflow image, creating the named new containers/network/volumes and local credentials, running **one real native DAG plus one native LangGraph run capped at three cycles**, serial test checks and a read-only evidence viewer. It includes stopping only new native services if resource/health checks fail and removing one-shot worker containers while retaining volumes/evidence.

It does not authorize stopping/restarting/changing existing services, attaching production volumes/networks, changing system settings, deleting volumes, rerunning original DAG/models/evaluation suite, paid API use, commits, merges, pushes or external deployment.
