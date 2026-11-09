# Original Part 2 workflow

Run agents/run.py through the isolated ML container using the root README commands. This entry point delegates to src/bike_demand_ml/cli.py; implementation lives in src/bike_demand_ml rather than duplicate agent modules.

- state.py: explicit shared state and accumulated trial/routing records.
- db.py: application PostgreSQL repeatable-read, READ ONLY snapshot; no file fallback.
- models.py: calendar/Open-Meteo inputs, fixed chronological splits, Dummy/Ridge/conditional RandomForest and regression metrics.
- nodes.py: specialist operations and bounded validation-only control policy.
- graph.py: original compiled StateGraph, conditional retry, final-test and failure edges.
- artifacts.py / runner.py: actual node events, immutable run folders and graph serialization.
- visuals.py: compiled topology plus recorded runtime events.

Default run compares two candidates with a hard cap of two. Model selection never reads final test metrics. A single final stage refits selected/Dummy models on train+validation and evaluates both on held-out data. For ml_main_01, validation selected Ridge alpha=10; see the root README and actual report under docs/verification/phase-c/runs/ml_main_01.

The classroom loop and UI were not copied. Optional bonus comparisons were not performed. [Root README](../README.md) is the complete setup/results guide.
