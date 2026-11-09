# Explicit evaluation cases and actual observations

Each row defines the input, expected behavior, criteria and threshold before evaluation. A case passes only when every applicable assertion is true (score=1.0). This measures policy/contract correctness; intentional failed workflows can be correctly rejected cases. All faults use isolated copies or injected exceptions, not production SQL mutations.

| Case | Input | Expected behavior | Scoring criteria | Threshold | Observed adaptive / fixed / simple status | Case passes |
| --- | --- | --- | --- | --- | --- | --- |
| normal | Unmodified validated PostgreSQL snapshot | All complete with sealed test evaluation | success, valid data/features, finite metrics, bounded routes, complete report | 1.0; all assertions | success / success / success | 3/3 |
| duplicate_date | Isolated copy with date[1]=date[0] | All reject before training | failed, attempt=0, no test metrics | 1.0; all assertions | failed / failed / failed | 3/3 |
| missing_weather | Isolated copy without precipitation_sum | All reject before training | failed, attempt=0, no test metrics | 1.0; all assertions | failed / failed / failed | 3/3 |
| transient_database | One injected OperationalError before snapshot delivery | Adaptive/fixed recover; simple port fails without DB recovery | expected status; successful recovery exactly once where supported | 1.0; all assertions | success / success / failed | 3/3 |
| permanent_database | Injected PermissionError, no database mutation | All fail without retry | failed, recoveries=0, no test metrics | 1.0; all assertions | failed / failed / failed | 3/3 |
| transient_training | One TrainingInterrupted on first candidate | Adaptive/fixed recover; simple port fails | expected status; one recovery where supported | 1.0; all assertions | success / success / failed | 3/3 |
| exhaust_training | Every candidate raises TrainingInterrupted | All fail within budgets | failed; <=3 attempts, <=2 recoveries; no test metrics | 1.0; all assertions | failed / failed / failed | 3/3 |
| weak_model | All candidate operations intentionally use Dummy; real predictions scored | Bounded termination with unmet quality; best Dummy retained | success; adaptive/simple 3 attempts, fixed 1; no improvement claimed | 1.0; all assertions | success / success / success | 3/3 |
| invalid_model | Unsupported model family in isolated candidate fixture | All abort unsupported fit, without recovery | failed; attempt=1, recoveries=0, no test metrics | 1.0; all assertions | failed / failed / failed | 3/3 |

The independent route oracle checks destinations against phase, actual validation target/gap, collinearity/refinement state, error class and remaining budgets. It was strengthened to check the exact recovery destination; recorded executions are reassessed without retraining. Counterexample tests deliberately corrupt a route and best-model selection to ensure those errors are detected.

Final output checks independently recompute MAE/RMSE from saved real held-out predictions. Feature checks exclude target leakage, enforce temporal partition sizes and training-only fitted transforms. Per-agent calls, durations and errors are recorded in every actual run report.

- [Full observed results, criteria, scores and assertions](runtime/evaluations/bonus_suite_01/results.json)
- [Machine-readable case definitions](runtime/evaluations/bonus_suite_01/case_definitions.json)
- [Actual result CSV](runtime/evaluations/bonus_suite_01/results.csv)
