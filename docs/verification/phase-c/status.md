> Historical Phase C verification report. Final update November 9, 2026: all six real screenshots are now captured and visually reviewed; [the screenshot index](../../../screenshots/README.md) and [final submission checks](../../submission.md) supersede the pending-capture statements below. Original runtime metrics, machine-readable evidence and model artifacts are unchanged.

# Phase C / Part 2 actual verification

Verified November 8, 2026 America/New_York (UTC artifacts dated November 9). Assignment requirements, TA clarifications, project specification and prompts/03_agents_ml.txt were read completely. The root README is now the primary documentation for both required parts.

## Requirement status

| Requirement | Status and evidence |
| --- | --- |
| Part 1 prerequisite | Verified real PostgreSQL snapshot: 731 cleaned rows, 731 dates, 3,292,679 rentals, matching Part 1 hash/provenance |
| Original LangGraph state/nodes/edges | Implemented in src/bike_demand_ml; compiled StateGraph with explicit shared state, conditional edges and failure node; no demo copied |
| Data Loader from application PostgreSQL | Real READ ONLY repeatable-read SELECT; validates content hash, date coverage and pipeline provenance; no file fallback |
| Features / target leakage | Twelve calendar/Open-Meteo inputs; cnt only as target; casual/registered/UCI weather and row ID excluded; training-only fitted preprocessing |
| Chronological evaluation | 365 training, 182 validation, 184 held-out dates; no shuffled split; final refit uses 547 rows |
| Dummy and lightweight candidates | Real mean Dummy and Ridge alpha=10/100 comparison; RandomForest is an implemented alternative and was not executed on production data |
| Bounded conditional loop | Real retry after attempt 1, finish after attempt 2; hard cap two and recursion guard 40; candidate choice uses train/validation gap |
| Validation-only selection | Best candidate retained by validation RMSE; selected alpha=10; final held-out stage once with no tuning back edge |
| Appropriate metrics / deterministic behavior | Real MAE/RMSE/R², seed 706, one numerical thread; full actual candidate metrics in report |
| UI reflects original graph | Running localhost:8501; actual compiled topology plus event-derived nodes/edges, visits, routes and regression metrics; replay tested |
| Required route and output tests | 19 passed, zero failures/errors/skips; success, retry, failure, max attempts, DB rule, artifacts and determinism covered |
| Real failure route | Isolated nonexistent-DB probe exited 1; load_postgres → failure_report, attempt 0, no claimed metrics; no DB created |
| Real results / artifacts | ml_main_01 completed; 26 node events, 13 node executions, two candidate fits, one final test stage; 23 exported files byte-verified across success/failure folders |
| Preserve Part 1 | All 182 protected files unchanged; DB count, dates, rentals and hash unchanged; five Part 1 services remain healthy |
| Documentation / screenshots | Root README updated; genuine prior Part 1 image links exist; Part 2 screenshot capture guide prepared, manual capture pending |
| Phase boundaries | No Part 3, external deployment, Git staging/commit/push, production SQL writes or Docker data deletion |

## Actual results

Run ID: ml_main_01. Source: application database bike_demand, table bike_analytics.bike_daily; last pipeline provenance phase_b_manual_02.

Dataset SHA-256: 99123ac3758014b572f0ac290b1cfcba3896a8fae47896055eb1cc9d89579a33.

| Candidate | Training RMSE | Validation MAE | Validation RMSE |
| --- | ---: | ---: | ---: |
| Dummy, mean | 1376.863667 | 2052.435270 | 2449.887152 |
| Ridge alpha=10 | 558.822677 | 1362.248288 | 1573.811443 |
| Ridge alpha=100 | 603.267930 | 1379.545493 | 1614.161359 |

Attempt 1's validation/training RMSE ratio was 2.816298. The predeclared two-candidate comparison routed to retry, choosing stronger Ridge regularization. Attempt 2 was worse, so alpha=10 remained best. The router finished with validation_target_met (target RMSE 2327.392794). Default minimum two ensures a comparison even when the first candidate already reaches the quality target.

After selection froze, both selected Ridge and Dummy were refit on train+validation and scored on July–December 2012 only:

| Final held-out model | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Ridge alpha=10 | 904.706465 | 1202.361305 | 0.523123 |
| Dummy mean | 2452.640301 | 2694.302464 | -1.394579 |

These values came from the actual database-fed workflow, not unit fixtures. Test metrics did not determine retries or selection. One fixed temporal split does not establish broad generalization. Historical observed weather is not a future forecast feed. Unconstrained Ridge produced one negative prediction among the 184 held-out dates; predictions were not clipped or retuned after observing test outcomes.

## Commands actually executed

~~~powershell
docker compose --profile ml --progress plain build ml-runner
docker compose --profile ml up -d --no-deps dashboard
docker compose --profile ml run --rm --no-deps ml-runner /bin/sh -c 'umask 0002; exec python agents/run.py --run-id ml_main_01'
docker compose --profile ml run --rm --no-deps ml-runner python -m pytest tests/ml -p no:cacheprovider -q -ra --junitxml=/opt/project/artifacts/ml-verification/tests-final.xml
docker compose --profile ml run --rm --no-deps -e APP_DB_NAME=bike_demand_missing_probe ml-runner /bin/sh -c 'umask 0002; exec python agents/run.py --run-id ml_failure_probe_01'
docker compose cp dashboard:/opt/project/artifacts/ml/. ./docs/verification/phase-c/runs
docker compose cp dashboard:/opt/project/artifacts/ml-verification/. ./docs/verification/phase-c/test-artifacts
py -3.11 scripts/verify_phase_c_evidence.py
~~~

The main run exited 0. The negative probe intentionally exited 1 and was asserted as such. Its override affected only the one-shot container; no database was created or modified. Reusing an existing run ID is refused to protect prior evidence. Use new IDs for future training runs.

The initial 19-test pass emitted an additional nonfatal pytest-cache permissions warning because the image workdir is not writable to the runner. Final tests used no cache provider and passed 19 tests with one upstream LangChain pending-deprecation warning. No permission broadening was applied. The ML image's pip check reported no broken requirements.

PowerShell 5 wraps Docker progress written on stderr in NativeCommandError records in some raw logs. Command exit codes and actual pytest/JUnit/workflow output establish success/failure; those wrapper records alone are not failed builds/tests.

## Final safe static checks

Both Compose profiles validated. Seventeen Python files parsed, 63 local Markdown links resolved, and 69 text files were checked against actual local credential values with zero leaks found. Independent recomputation from all 184 saved test predictions matched reported MAE/RMSE for both estimators. See [static checks](static-checks.json).

## Dashboard verification

The real dashboard container returned HTTP 200 / ok at /_stcore/health. Streamlit AppTest against its installed application verified:

- No application exceptions.
- The actual compiled graph rendered.
- The evaluation table exactly matched the saved selected/Dummy report metrics.
- Replay event 14 showed attempt 1 / retry and the expected trace length.
- The intentionally failed run displayed an error without successful-evaluation claims.

This is backend application verification, not browser-pixel or screenshot verification. The graph PNG, held-out plot and validation plot were also visually inspected as exported scientific/execution artifacts. No application screenshot was synthesized or captured by the agent.

## Evidence files

- [Actual main report](runs/ml_main_01/report.json), [trials/routes](runs/ml_main_01/trials.json), [events](runs/ml_main_01/events.jsonl)
- [Database provenance](runs/ml_main_01/provenance.json), [features](runs/ml_main_01/features.json), [chronological splits](runs/ml_main_01/splits.json)
- [Compiled graph export](runs/ml_main_01/graph.json), [graph execution artifact](runs/ml_main_01/agent_graph.png)
- [Held-out predictions CSV](runs/ml_main_01/test_predictions.csv), [held-out plot](runs/ml_main_01/test_predictions.png), [validation plot](runs/ml_main_01/validation_rmse.png)
- [Actual controlled failure report](runs/ml_failure_probe_01/report.json)
- [Machine-readable verification](runtime-results.json), [JUnit XML](test-artifacts/tests-final.xml), [test log](tests-final.log)
- [Main workflow log](workflow-main.log), [failure-probe log](workflow-failure-probe.log)
- [Dashboard AppTest](dashboard-apptest-final.json), [HTTP health](dashboard-health-final.json), [pip check](pip-check-final.log), [Linux package freeze](linux-freeze.txt)
- [Part 1 before snapshot](part1-before.json), [preservation check](part1-preservation.json), [service states](service-status-final.json)
- [Export SHA-256 manifest](export-sha256.json), [exact change inventory](changes.md), [manual screenshot guide](capture-guide.md)

Run outputs reside in the named artifact volume and were copied to this verification tree. Host exports matched all 23 original files byte-for-byte. The selected_model.joblib is a local model artifact; the dashboard does not deserialize it.

## Remaining submission gaps and operational limits

No unresolved runtime blocker was observed for the tested ML run. Capture the real Part 2 agent graph and evaluation screenshots at localhost:8501; the retry image is additional evidence. Follow capture-guide.md. The root README links only the two existing Part 1 screenshots and real exported analysis artifacts.

Git still has no staged/tracked project files or commit from this work. Before submission, review what to include and deliberately include actual screenshots despite their ignore rule. No push is authorized. Canvas deadline/timezone and course AI-use policy remain unverified. Optional Part 3 comparisons/evaluation are outside scope and are not claimed.

Docker has only approximately 7.65 GiB and host free memory was low at preflight. Only the targeted ML image/dashboard/one-shot runner were added; existing Part 1 services were not stopped or recreated. Further simultaneous workloads may require releasing host memory. No system settings or Docker disk contents were changed.

## Implementation references

The workflow uses the official [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), its streaming interface supported by pinned 1.0.3, and scikit-learn regression estimators/metrics. [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest) verifies the real application without substituting for screenshots. Installed dependency versions are captured in linux-freeze.txt.
