# Phase checklist

## Phase A

- [x] Read requirements, TA clarifications and project specification completely.
- [x] Probe actual UCI ZIP/day.csv schema, types, coverage and target identity.
- [x] Probe full-range Open-Meteo ERA5 response, types, units, timezone and dates.
- [x] Compare source date sets; distinguish probe from a persisted merge.
- [x] Read official version-specific Airflow Docker guide/reference and constraints.
- [x] Inspect Docker/Compose, WSL, Python/Git, RAM and disk without destructive changes.
- [x] Create local Git repo, ignore rules, secret template and local secret generator.
- [x] Author Compose, Dockerfiles, direct pins and isolated ML/dashboard environment.
- [x] Design independent branches, daily schedule, date merge, app DB and DB-fed EDA.
- [x] Design original LangGraph state, agents, conditional routing and bounded loop.
- [x] Create tests/evidence structure and screenshot filename plan.
- [x] Document exact setup commands, phase boundary and approvals.
- [x] Build and smoke-test Part 1 containers with explicit user approval; see verification/phase-b/status.md.
- [x] Complete final static configuration review; see verification/phase-a-review.md.
- [x] Confirm Docker disk location on D: from settings and actual VHDX files.
- [x] Recheck RAM/disk before approved runtime testing and monitor healthy service memory.
- [ ] Confirm deadline/timezone and AI-use rules in Canvas (not connected/verified).

## Phase B — Part 1, runtime verified

- [x] Implement original Airflow 3 DAG and source transformations.
- [x] Observe true task overlap, a successful scheduler-created run, and the next 06:00 local schedule.
- [x] Enforce exact schema/date/units/one-to-one merge contracts; host tests pass.
- [x] Migrate app PostgreSQL, load 731 rows transactionally, prove rerun idempotence and real SQL rollback in the separate test DB.
- [x] Produce three EDA charts per run from new DB reads; document measured findings and limitations.
- [x] Run host and full real Linux/DagBag/PostgreSQL tests; export genuine logs/SQL/EDA evidence.
- [x] Prepare submission/part1 with fresh live run/task checks, immutable EDA/validation exports and a READ ONLY PostgreSQL report.
- [x] Preserve real required Airflow run and graph screenshots: 01_airflow_dag_success.png and 02_airflow_graph.png. Supporting schedule/SQL/EDA UI captures remain optional.

## Phase C — Part 2, runtime verified; screenshots captured

- [x] Implement and stream original executable LangGraph workflow.
- [x] Train on persisted cleaned PostgreSQL data with leakage-safe temporal splits.
- [x] Exercise real retry/finish and missing-DB failure; 19 unit tests cover early success, retry, failure, max attempts and artifacts.
- [x] Compare actual Ridge versus Dummy held-out MAE/RMSE/R2 without test-set tuning.
- [x] Build runtime-reflective compiled-graph UI; verify real events/replay/evaluation and export genuine run artifacts.
- [x] Capture and visually review all six real submission screenshots, including agent graph, retry, evaluation and comparison charts.
- [x] Update root README for both parts with actual results, limitations, commands and existing image links.

## Submission / optional work

- [x] Review the exact recommended staging manifest for secrets, ignored files, real evidence and source attribution; 59 final tests pass.
- [ ] Obtain explicit permission before remote creation, push, publishing or deployment.
- [ ] Optional Part 3 is out of scope; do not claim bonus evaluations without doing them.
