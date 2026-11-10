# Native classroom screenshot evidence

All six required native captures exist and were visually reviewed. No extra optional agent-event screenshots are required. These are genuine application captures, not generated illustrations.

| Capture | Application / evidence |
| --- | --- |
| [15: native Airflow success](../../../../screenshots/15_native_airflow_success.png) | localhost:8088, solution_baseline_prep Grid: one successful run and seven green task rows |
| [16: native DAG topology](../../../../screenshots/16_native_airflow_graph.png) | Same DAG, Graph: original seven-task dependencies. The crop does not itself show run identity or execution status; use 15 and 17 alongside it |
| [17: native Airflow metrics](../../../../screenshots/17_native_airflow_metrics.png) | Airflow XCom list: native_prep_01, validation F1 0.05, n_train 1600, n_val 400 and publication records |
| [18: native LangGraph](../../../../screenshots/18_native_langgraph_execution.png) | localhost:8503, Native LangGraph: native_simple_02, original compiled graph, three no-key cycles, validation/holdout metrics and unmet target |
| [19: classification execution records](../../../../screenshots/19_native_classification_results.png) | Same page: agent execution table, per-cycle validation F1 and memory/context revisions. Its filename is broader than its contents; final metric cards are in 18 and 20 |
| [20: comparison scopes](../../../../screenshots/20_native_and_regression_scopes.png) | Comparison scopes: separate native fraud classification and adapted Bike Demand regression tables; no cross-task metric ranking |

Actual native graph metrics: best validation F1 **0.056604**, held-out F1 **0.059113**, accuracy **0.5225**; the 0.8 target was not met. The native DAG emits validation F1 only, not held-out accuracy.

For private access, the native Airflow username is native_admin; its password is NATIVE_ADMIN_PASSWORD in ignored artifacts/native-classroom-local/.env. Never include credentials in images.

The native scheduler was intentionally stopped after its manual run to save memory; completed task records remain in metadata. The original Bike Demand scheduler is independent. To open an existing page when needed, the guarded commands below reuse built images and enforce at least 2.5 GiB available Windows memory. They do not trigger training:

~~~powershell
py -3.11 bonus/native-classroom/control.py web
py -3.11 bonus/native-classroom/control.py viewer
~~~

See [actual results and protocol limits](results.md), including overlapping native evaluation rows and preserved convergence warnings. Native classification F1 is not directly comparable with regression RMSE.
