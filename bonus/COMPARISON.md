# Baseline comparison

Two complementary comparisons are reported separately: original classroom fraud-classification reproductions, and adapted workflows on the Bike Demand regression problem. F1/accuracy are never ranked against MAE/RMSE.

## A. Native classroom reproduction

The original instructor sources at [a294145ea9aa4225908ce701c06160c33213335d](https://github.com/Kedar-V/automl-research-lab/tree/a294145ea9aa4225908ce701c06160c33213335d) were executed without source edits. The actual solution_baseline_prep DAG ran through Airflow 2.10.4's scheduler, not its CLI helper. The completed solution/langgraph/graph.py ran with the original loop_runtime.py and documented no-key heuristics.

Both consumed the **same DAG-published 2,000-row fraud sample**, containing 1,940 negatives and 60 positives, derived from the original 1,000 customers and 10,000 transactions.

| Original system / run | Evaluation stage | Actual F1 | Accuracy | Data protocol |
| --- | --- | ---: | ---: | --- |
| Airflow DAG / native_prep_01 | Validation | 0.050000 | Not emitted | Numeric-only LogisticRegression; 1,600 train / 400 validation |
| Simple LangGraph / native_simple_02 | Best validation | 0.056604 | 0.5000 at selected trial | 1,200 train / 400 validation / 400 holdout |
| Simple LangGraph / native_simple_02 | Final held-out | 0.059113 | 0.5225 | Selected model refit on 1,600 rows; one 400-row final stage |

All **seven native DAG tasks succeeded**: validate_customers, validate_transactions, merge_csvs, make_subset, profile_light, train_baseline and publish_merged. Published CSV bytes match the sampled subset; source data and DAG hashes were verified.

The native LangGraph completed **three cycles**, with two memory/context revisions and one final holdout stage. It selected the first LogisticRegression specification (C=0.25, max_iter=300). Validation F1 values were 0.056604, 0.056075 and 0.056604. The 0.8 target remained unmet; native stop_reason is finalize. No LLM was used and no fit-repair path was taken in this run. Iteration-limit convergence warnings occurred in both native workflows and were preserved, not tuned away.

### Qualification of the native results

A [no-fit split diagnostic](../docs/verification/bonus/native-classroom/runtime/native_classroom_01/native-split-comparison.json) confirmed that the DAG's 400 validation indices are exactly the native graph's 400 holdout indices. They are **not independent evaluation populations**. Native graph selection uses its separate internal validation partition; parameters were fixed before execution and were not retuned using these results.

The DAG and graph also differ in preprocessing, selection protocol and dependency versions. DAG: pandas 2.1.4, NumPy 1.26.4, scikit-learn 1.5.2; graph: pandas 2.3.3, NumPy 2.2.6, scikit-learn 1.7.2. The isolated scheduler used one LocalExecutor slot and slower parsing to fit available memory. A shared log volume replaced its redundant log server. These environment adaptations did not alter instructor task/node/model code.

The native DAG took about 30.48 seconds including scheduling/tasks; native graph wall time was 0.6311 seconds excluding container/import setup. These cover different work and are not a speed ranking. Native class predictions/models were not exported by the original code; reported classification scores come from actual task returns and graph outputs, checked for consistency without extra classifier refits.

Both required native reference workflows have actual execution evidence. This does **not** make the Bike Demand ports exact classroom implementations, establish predictive superiority or guarantee all Bonus points. The no-key run does not evaluate the classroom's LLM-enabled path.

### Evidence

- [Native reproduction and requirement report](../docs/verification/bonus/native-classroom/results.md).
- [Real DAG report](../docs/verification/bonus/native-classroom/runtime/native_classroom_01/artifacts/native_prep_01/report.json), [seven task states](../docs/verification/bonus/native-classroom/runtime/native_classroom_01/artifacts/native_prep_01/task-states.json), task logs and XComs in the same bundle.
- [Real native graph report](../docs/verification/bonus/native-classroom/runtime/native_classroom_01/artifacts/native_simple_02/report.json), compiled graph and events in the same directory.
- [Source pins and attribution](native-classroom/README.md), [six reviewed native screenshots](../docs/verification/bonus/native-classroom/capture-guide.md).

The earlier [classroom_probe_01](../docs/verification/bonus/runtime/classroom/classroom_probe_01/summary.json) remains historical evidence. Its prep CLI F1 0.060606 and two-cycle native-graph held-out F1 0.085366 used the helper's differently sampled dataset. They are not substituted for the new actual DAG/native-publication results. The helper differs from the DAG in sampling, preprocessing and split structure.

## B. Same-problem Bike Demand regression

The preserved adaptive, fixed_port and simple_port executions use identical PostgreSQL-derived data, calendar/weather features, chronological partitions, nine isolated fault scenarios and held-out metrics. Fixed/simple policies are explicit simplified regression workflow ports, not unmodified classroom systems.

| Policy | Test MAE | Test RMSE | R2 | Completed cases | Expected-behavior passes | Incorrect routes | Attempts | Recoveries | Graph wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| adaptive | 904.71 | 1,202.36 | 0.5231 | 4/9 | 9/9 | 0 | 16 | 4 | 0.7962 |
| fixed_port | 904.71 | 1,202.36 | 0.5231 | 4/9 | 9/9 | 0 | 9 | 4 | 0.2999 |
| simple_port | 904.71 | 1,202.36 | 0.5231 | 2/9 | 9/9 | 0 | 7 | 0 | 0.2887 |

Expected rejection is a passed evaluation case, not a completed modeling workflow. A [paired prediction check](../docs/verification/bonus/native-classroom/runtime/native_classroom_01/paired-regression-prediction-check.json) recomputed MAE/RMSE and aligned all 184 test dates: normal-case predictions are **exactly identical across all three policies**. No original graph, model or 27-case suite was rerun.

Adaptive exploration included feature refinement, regularization and a forest, but retained Ridge alpha=10. It required more operations than fixed_port without improving predictions. simple_port omits native memory/context/LLM features and one-pass fit repair; its lower completion rate is not evidence that the actual classroom system cannot recover. fixed_port uses the common LangGraph harness rather than an Airflow scheduler.

The [original suite summary](../docs/verification/bonus/runtime/evaluations/bonus_suite_01/summary.json), [27 actual case results](../docs/verification/bonus/runtime/evaluations/bonus_suite_01/results.json), [independent artifact audit](../docs/verification/bonus/review/evaluation-audit.json) and [seven reviewed Bonus captures](../screenshots/README.md) remain unchanged.

Nine designed scenarios and single-run timings do not establish general reliability or statistically significant advantages. Candidate regression validation predictions were not saved for independent recomputation; final held-out predictions were saved and audited.
