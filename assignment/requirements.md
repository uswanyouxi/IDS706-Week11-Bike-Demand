# IDS 706 Week 11 — Assignment Requirements (transcribed from student-supplied screenshots)

## Part 1 — Build an Airflow Data Pipeline (required)
1. Deploy Airflow and create a scheduled DAG.
   - Orchestrate the pipeline from ingestion through analysis.
   - Run independent tasks in parallel where appropriate.
2. Ingest and transform data.
   - Identify and use at least two related datasets or data tables.
   - Clean and transform each dataset; TaskGroups are optional.
   - Merge datasets and load final result into a database such as PostgreSQL, Supabase, or NoSQL where appropriate.
3. Analyze the processed data.
   - Read cleaned data back from the database.
   - Conduct an analysis, e.g. visualization or one simple ML model.
4. Briefly document data sources, transformations, structure, analysis results, scheduling, and parallel processing.

## Part 2 — Agent-Based ML Workflow for Loops (required)
- Adapt the in-class agent workflow to train and evaluate an ML model using Part 1 cleaned data.
- Add, remove, or modify agents to suit the chosen workflow.
- Update live agent graph to show the modified workflow.
- Report accuracy or an appropriate metric.

## Submission (Parts 1 and 2)
- Repository with Airflow DAG, modified agent code, and running instructions.
- Containerized development setup (e.g. Dockerfile and/or devcontainer.json).
- Screenshots: successful DAG run in Airflow UI, DAG graph view, agent graph, model evaluation results.
- README.md: brief pipeline summary, agent changes, findings.

## Part 3 — OPTIONAL Super Bonus (up to 25 points)
- Multi-agent system with distinct responsibilities and a graph representation.
- Adaptive routing, selecting agents, retries based on intermediate results.
- Evaluation suite measuring intermediate and final output quality and coordination effectiveness.
- Every test case has input, expected behavior/outcome, scoring criteria, pass/fail threshold.
- Compare against class-demonstrated baselines: fixed Airflow workflow and simple agent system.
- Submit source, setup instructions, workflow graph, evaluation suite/dashboard and a short comparison summary.
