# Real submission screenshots - required Parts 1-2 and optional Bonus

All six screenshots have been captured from the real Airflow/Streamlit applications, supplied by the user, and visually reviewed on November 9, 2026 (America/New_York). No image was fabricated, generated, edited or renamed during final preparation.

| Existing file | What the image actually shows |
| --- | --- |
| [01_airflow_dag_success.png](01_airflow_dag_success.png) | Airflow DAG dc_bike_weather_daily; Grid with all nine task rows green across three runs, successful-run summary and daily cron |
| [02_airflow_graph.png](02_airflow_graph.png) | Airflow graph with independent UCI/weather branches, separate cleaning, date merge, PostgreSQL load and EDA |
| [06_langgraph_live_execution.png](06_langgraph_live_execution.png) | Original compiled agent graph with actual completed execution, two attempts, finish route and recorded event trace |
| [07_langgraph_conditional_retry.png](07_langgraph_conditional_retry.png) | Actual trace rows showing retry at event 14 after attempt one, second attempt, then finish at event 22 |
| [08_regression_evaluation.png](08_regression_evaluation.png) | Held-out selected/Dummy MAE, RMSE, R²; Ridge alpha=10; both validation trials and route reasons |
| [09_model_comparison_charts.png](09_model_comparison_charts.png) | Dashboard's real held-out predictions chart and validation RMSE comparison |

The assignment requests successful Airflow-run, DAG-graph, agent-graph and model-evaluation images. Files 01, 02, 06 and 08 cover those categories; 07 and 09 provide supporting submission evidence. All six are explicitly allowlisted by .gitignore; the seven reviewed Bonus additions below are also allowlisted. All other screenshot files remain ignored.

The Airflow graph capture is named **02_airflow_graph.png**. There is no separate schedule/SQL/EDA/Grid screenshot in this six-file set. File 01 already includes Grid and cron information; SQL and EDA have their own real exported reports/charts.

The completed agent-graph screenshot reflects recorded execution, rather than claiming an in-flight capture. The retry image shows the completed run's trace, not a replay slider positioned at event 14. Some reason text is horizontally truncated there; the full routing table is readable in file 08 and the report JSON.

- [Airflow page locations](../submission/part1/capture-guide.md)
- [Part 2 page/capture details](../docs/verification/phase-c/capture-guide.md)
- [Exact recommended staging process](../docs/submission.md)

The six image bytes are preserved. Screenshot SHA-256 values and final source/evidence preservation checks are recorded under docs/verification/final-submission/. No credentials, .env contents or login token is visible in the reviewed images. All six screenshots are committed and published on the repository's [main branch](https://github.com/uswanyouxi/IDS706-Week11-Bike-Demand/tree/main/screenshots). Historical verification records retain their original timestamps.

## Optional Part 3 - seven reviewed captures on the bonus branch

These real Bonus files are present and reviewed; the six published images above remain byte-for-byte unchanged.

| Actual image | Evidence |
| --- | --- |
| [10_bonus_adaptive_graph.png](10_bonus_adaptive_graph.png) | bonus_main_01, original graph, three attempts and refinement |
| [11_bonus_routing_recovery.png](11_bonus_routing_recovery.png) | Completed transient-training run, recovery path visited and recovery count one |
| [11b_bonus_recovery_events.png](11b_bonus_recovery_events.png) | Actual trace from recovery to model_selection/attempt two; cropped reasons |
| [12_bonus_evaluation_suite.png](12_bonus_evaluation_suite.png) | Real comparison table and observed case scores/statuses for bonus_suite_01 |
| [12b_bonus_evaluation_criteria.png](12b_bonus_evaluation_criteria.png) | Expanded declared inputs, expected outcomes, criteria and thresholds |
| [13_bonus_baseline_comparison.png](13_bonus_baseline_comparison.png) | Actual bonus_suite_01 adaptive/fixed_port/simple_port metrics, completion/pass rates and case results; native-reference warning is outside the crop |
| [14_bonus_agent_metrics.png](14_bonus_agent_metrics.png) | Policy-level completion and expected-behavior pass-rate bar chart, with criteria expander; despite its filename, no per-agent calls/timings are visible |

Both additional PNGs were visually reviewed as genuine application captures. Image 14 is accurately described by its content. A readable per-agent calls/timings capture would still strengthen the evidence; the actual values are preserved in run reports. No screenshot was generated, edited or renamed.

See the [current Bonus index/capture details](../docs/verification/bonus/screenshot-guide.md) and [independent review](../docs/verification/bonus/review/README.md). These are bonus-branch additions, not a claim of publication or of a native classroom Airflow DAG execution. Only the seven actual reviewed Bonus names were added to .gitignore.
