# Real submission screenshots — Parts 1 and 2

All six screenshots have been captured from the real Airflow/Streamlit applications, supplied by the user, and visually reviewed on November 9, 2026 (America/New_York). No image was fabricated, generated, edited or renamed during final preparation.

| Existing file | What the image actually shows |
| --- | --- |
| [01_airflow_dag_success.png](01_airflow_dag_success.png) | Airflow DAG dc_bike_weather_daily; Grid with all nine task rows green across three runs, successful-run summary and daily cron |
| [02_airflow_graph.png](02_airflow_graph.png) | Airflow graph with independent UCI/weather branches, separate cleaning, date merge, PostgreSQL load and EDA |
| [06_langgraph_live_execution.png](06_langgraph_live_execution.png) | Original compiled agent graph with actual completed execution, two attempts, finish route and recorded event trace |
| [07_langgraph_conditional_retry.png](07_langgraph_conditional_retry.png) | Actual trace rows showing retry at event 14 after attempt one, second attempt, then finish at event 22 |
| [08_regression_evaluation.png](08_regression_evaluation.png) | Held-out selected/Dummy MAE, RMSE, R²; Ridge alpha=10; both validation trials and route reasons |
| [09_model_comparison_charts.png](09_model_comparison_charts.png) | Dashboard's real held-out predictions chart and validation RMSE comparison |

The assignment requests successful Airflow-run, DAG-graph, agent-graph and model-evaluation images. Files 01, 02, 06 and 08 cover those categories; 07 and 09 provide supporting submission evidence. All six are explicitly allowlisted by .gitignore; other screenshot files remain ignored.

The Airflow graph capture is named **02_airflow_graph.png**. There is no separate schedule/SQL/EDA/Grid screenshot in this six-file set. File 01 already includes Grid and cron information; SQL and EDA have their own real exported reports/charts.

The completed agent-graph screenshot reflects recorded execution, rather than claiming an in-flight capture. The retry image shows the completed run's trace, not a replay slider positioned at event 14. Some reason text is horizontally truncated there; the full routing table is readable in file 08 and the report JSON.

- [Airflow page locations](../submission/part1/capture-guide.md)
- [Part 2 page/capture details](../docs/verification/phase-c/capture-guide.md)
- [Exact recommended staging process](../docs/submission.md)

The six image bytes are preserved. Screenshot SHA-256 values and final source/evidence preservation checks are recorded under docs/verification/final-submission/. No credentials, .env contents or login token is visible in the reviewed images. No Git staging/commit/push has occurred.
