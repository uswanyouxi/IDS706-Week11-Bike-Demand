# Part 2 captured screenshot guide

All four Part 2 images now exist and were visually reviewed on November 9, 2026. They supplement the two existing Airflow images. The [complete six-file index](../../../screenshots/README.md) is authoritative.

| Existing file under screenshots/ | Actual content |
| --- | --- |
| [06_langgraph_live_execution.png](../../../screenshots/06_langgraph_live_execution.png) | Original compiled graph and recorded execution progress at event 26/26; candidate attempts 2; finish reason validation_target_met |
| [07_langgraph_conditional_retry.png](../../../screenshots/07_langgraph_conditional_retry.png) | Real completed-run trace showing retry event 14, candidate attempt 2, and finish event 22 |
| [08_regression_evaluation.png](../../../screenshots/08_regression_evaluation.png) | Selected Ridge alpha=10; selected/Dummy held-out metrics; both actual validation trials and full routing decisions |
| [09_model_comparison_charts.png](../../../screenshots/09_model_comparison_charts.png) | Real dashboard comparison of held-out predictions and validation RMSE |

Source page: http://localhost:8501, recorded execution ml_main_01. Captures show actual recorded execution and results; the filename containing live_execution does not claim an in-flight screenshot. The retry capture shows the completed trace, not an event-14 replay position. Full reason text is visible in file 08 even where the narrow trace capture truncates it.

To inspect the same transition interactively, uncheck Follow live execution and set Replay actual event to 14. The final report below remains the completed-run result. No new training run is needed to inspect recorded evidence.

Held-out selected metrics: MAE 904.7065, RMSE 1202.3613, R² 0.5231. Dummy: MAE 2452.6403, RMSE 2694.3025. The final Ridge produced one negative test prediction; this is a retrospective observed-weather backtest.

Generated agent_graph.png, test_predictions.png and validation_rmse.png remain scientific/execution artifacts, distinct from these UI screenshots. No image was fabricated or changed during final preparation. All six reviewed screenshots are explicitly allowlisted in Git; no staging or push has occurred.
