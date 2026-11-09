# Phase C project-local change inventory

No successful Part 1 DAG, source transformation, SQL, Airflow image, persisted dataset, EDA export, prior evidence or screenshot was altered. The preservation manifest checks 182 existing protected files.

## Existing files updated

| File | Change |
| --- | --- |
| Dockerfile.ml | Install pinned ML environment plus pytest; copy ML implementation/UI/tests; run non-root with bounded numerical threads |
| compose.yaml | ML image tags changed from phase-a to 1.0.0; Part 1 service definitions and volume permissions unchanged |
| agents/run.py | Replace phase placeholder with executable ML CLI entry point |
| agents/README.md | Supplementary implementation map and link to primary root README |
| dashboard/app.py | Replace placeholder with original read-only, event-reflective graph/replay/evaluation application |
| README.md | Primary guide for both parts, actual results, commands, limitations, genuine image links and pending screenshot captures |
| tests/README.md | Add isolated Part 2 test/evidence instructions |
| docs/checklist.md | Record actually completed phases and remaining submission items |
| docs/architecture.md | Mark original Phase A document as historical and point to implemented policy |

Existing direct ML dependency pins were reused; requirements/ml.txt and all Airflow constraints/pins were unchanged.

## New implementation and tests

- src/bike_demand_ml/__init__.py
- src/bike_demand_ml/state.py
- src/bike_demand_ml/db.py
- src/bike_demand_ml/models.py
- src/bike_demand_ml/nodes.py
- src/bike_demand_ml/graph.py
- src/bike_demand_ml/artifacts.py
- src/bike_demand_ml/runner.py
- src/bike_demand_ml/cli.py
- src/bike_demand_ml/visuals.py
- tests/ml/conftest.py
- tests/ml/test_policy.py
- tests/ml/test_database.py
- tests/ml/test_execution.py
- scripts/verify_phase_c_evidence.py
- dashboard/README.md

## New evidence/documentation

This docs/verification/phase-c directory contains actual build/test/runtime logs, JUnit XML, dependency freeze, health/UI checks, preservation snapshots, byte-verification manifest, status/change/capture documents and exported success/failure run folders. No placeholder screenshot files were created.

The successful run folder contains the real database snapshot/provenance, models, held-out predictions, figures, compiled topology and node events. The controlled failure folder contains its real failure report/graph/events, without evaluation metrics.

All changes remain local; no staging, commit, push or external deployment was performed.
