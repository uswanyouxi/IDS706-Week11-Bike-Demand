# Runtime-reflective agent dashboard

Open http://localhost:8501 after starting only the dashboard with the root README commands. Select ml_main_01 for verified real results.

The page reads JSONL events, serialized compiled graph topology and reports from a read-only artifact volume. It does not load models, start training or modify PostgreSQL. Streamlit refreshes the fragment every two seconds; uncheck Follow live execution to replay actual recorded events. Event 14 in ml_main_01 shows the first retry and its reason.

Graph colors/edges and visit counts derive from real node-start/completion events. The report area below shows the completed run's final held-out metrics, even when the trace is replayed at an earlier step. Candidate metrics, routing reasons, predictions and provenance match this workflow's regression task.

Actual container AppTest verified graph rendering, replay, the report's metric values and the failed-run display without application exceptions. All six submission screenshots have now been captured and visually reviewed; see [the screenshot index](../screenshots/README.md). The original AppTest result remains backend verification, distinct from the later manual captures.

[Root README](../README.md) is the primary guide for Parts 1 and 2.
