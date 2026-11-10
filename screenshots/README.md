# Application screenshots

Nineteen genuine Airflow/Streamlit captures document the required workflows and optional adaptive extension. Graph colors, traces and metrics reflect recorded execution. Some captures crop long reasons; complete events and reports are retained in the verification artifacts.

## Parts 1 and 2

| File | Visible evidence |
| --- | --- |
| [01_airflow_dag_success.png](01_airflow_dag_success.png) | dc_bike_weather_daily Grid: nine green task rows across three successful runs, with daily cron |
| [02_airflow_graph.png](02_airflow_graph.png) | Independent UCI/weather ingestion and cleaning, date merge, PostgreSQL load and database-fed EDA |
| [06_langgraph_live_execution.png](06_langgraph_live_execution.png) | Original compiled graph and completed execution: two attempts and finish route |
| [07_langgraph_conditional_retry.png](07_langgraph_conditional_retry.png) | Actual first-attempt retry and second-attempt finish trace |
| [08_regression_evaluation.png](08_regression_evaluation.png) | Selected/Dummy held-out metrics, Ridge alpha=10, validation trials and routing reasons |
| [09_model_comparison_charts.png](09_model_comparison_charts.png) | Real held-out predictions and validation RMSE chart |

These cover the required successful DAG, DAG graph, agent graph and model-evaluation categories. The graph/retry captures show recorded completed execution, not an independently claimed in-flight event. The six original image bytes are unchanged.

## Optional Part 3

| File | Visible evidence |
| --- | --- |
| [10_bonus_adaptive_graph.png](10_bonus_adaptive_graph.png) | bonus_main_01 coordinator/specialist graph, three attempts and feature refinement |
| [11_bonus_routing_recovery.png](11_bonus_routing_recovery.png) | Completed transient-training run with recovery visited and recovery count one |
| [11b_bonus_recovery_events.png](11b_bonus_recovery_events.png) | Trace from recovery to model_selection and attempt two; some reason text is cropped |
| [12_bonus_evaluation_suite.png](12_bonus_evaluation_suite.png) | bonus_suite_01 policy table and actual case statuses, scores and passes |
| [12b_bonus_evaluation_criteria.png](12b_bonus_evaluation_criteria.png) | Expanded case inputs, expected outcomes, criteria and thresholds |
| [13_bonus_baseline_comparison.png](13_bonus_baseline_comparison.png) | Adapted regression-policy metrics, completion/pass rates and scenario outcomes |
| [14_bonus_policy_comparison.png](14_bonus_policy_comparison.png) | Policy-level completion and expected-behavior pass-rate bars |

Image 14 is a policy chart, not a per-agent timing/call table. Measured per-agent values are in the [Bonus run report](../docs/verification/bonus/runtime/runs/bonus_main_01/report.json). Image 13 shows the original regression-port comparison. The [updated comparison](../bonus/COMPARISON.md) separately documents actual native Airflow and LangGraph classification runs. Six additional reviewed captures document the separately executed native baselines below.

## Native classroom references

| File | Visible evidence |
| --- | --- |
| [15_native_airflow_success.png](15_native_airflow_success.png) | Real solution_baseline_prep Grid: successful run and seven green task rows |
| [16_native_airflow_graph.png](16_native_airflow_graph.png) | Original seven-task topology; this cropped graph alone does not show run ID or success states |
| [17_native_airflow_metrics.png](17_native_airflow_metrics.png) | Real XCom records identify native_prep_01 and show validation F1 0.05, 1,600 training and 400 validation rows, and publication |
| [18_native_langgraph_execution.png](18_native_langgraph_execution.png) | Original graph, native_simple_02, three no-key cycles, final classification metrics and unmet 0.8 target |
| [19_native_classification_results.png](19_native_classification_results.png) | Agent execution table, per-cycle validation F1, memory/context revisions and no LLM calls; despite its filename, this capture is not the final metric-card view |
| [20_native_and_regression_scopes.png](20_native_and_regression_scopes.png) | Separate native F1/accuracy and adapted Bike Demand regression-policy tables with scope qualifications |

Images 15 and 17 jointly establish the native DAG run and success; 16 shows its topology. Final native metrics are visible in 18 and 20. No optional extra node/event captures are required. See the [native evidence guide](../docs/verification/bonus/native-classroom/capture-guide.md).

## Evidence and navigation

- Airflow: http://localhost:8080; select dc_bike_weather_daily, a successful run, then Grid or Graph.
- Part 2: http://localhost:8501; select ml_main_01 for graph, trace, evaluation and charts.
- Bonus: http://localhost:8502; select Optional Part 3, a recorded run, or suite bonus_suite_01.
- Native Airflow: http://localhost:8088; solution_baseline_prep, native_prep_01. Native viewer: http://localhost:8503; Native LangGraph and Comparison scopes tabs.
- [PostgreSQL report](../submission/part1/postgres_report.md), [three EDA charts](../submission/part1/README.md), [verification index](../docs/submission.md).

Only these nineteen reviewed PNG names and this README are allowlisted in .gitignore. Historical screenshot hashes retain the filenames used when each verification was recorded.
