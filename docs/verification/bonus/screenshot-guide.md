# Bonus dashboard evidence

The [screenshot index](../../../screenshots/README.md) covers all nineteen genuine captures. The seven Bonus images show the following recorded application views:

| Image | View and evidence |
| --- | --- |
| [10_bonus_adaptive_graph.png](../../../screenshots/10_bonus_adaptive_graph.png) | bonus_main_01: original specialist graph, three candidate attempts and one feature refinement |
| [11_bonus_routing_recovery.png](../../../screenshots/11_bonus_routing_recovery.png) | bonus_suite_01_transient_training_adaptive: completed recovery route |
| [11b_bonus_recovery_events.png](../../../screenshots/11b_bonus_recovery_events.png) | Recovery followed by model_selection and attempt two; some reasons are cropped |
| [12_bonus_evaluation_suite.png](../../../screenshots/12_bonus_evaluation_suite.png) | bonus_suite_01: observed policy/case results and pass thresholds |
| [12b_bonus_evaluation_criteria.png](../../../screenshots/12b_bonus_evaluation_criteria.png) | Expanded scenario inputs, expected behavior, criteria and thresholds |
| [13_bonus_baseline_comparison.png](../../../screenshots/13_bonus_baseline_comparison.png) | Adapted regression-policy metrics and completion/pass-rate comparison |
| [14_bonus_policy_comparison.png](../../../screenshots/14_bonus_policy_comparison.png) | Policy-level completion/pass-rate chart; no per-agent timings |

Open http://localhost:8502 and select Optional Part 3. Select the named run or suite in its dropdown. To inspect intermediate feature routing, uncheck Follow bonus execution and replay bonus_main_01 event 24. Recovery is recorded in bonus_suite_01_transient_training_adaptive. Captured completed traces are distinct from an in-flight execution claim.

[Run reports](runtime/runs/bonus_main_01/report.json) retain per-agent calls, errors and measured durations. [Comparison details](../../../bonus/COMPARISON.md) distinguish regression ports from the separately reproduced native classification baselines. Image 13 shows the original regression suite, not the newer native classification results. Follow the [native capture guide](native-classroom/capture-guide.md) for actual runs native_prep_01 and native_simple_02; all six reviewed files 15-20 are included; image 19 shows execution records and images 18/20 show final metrics.

The policy-chart rename preserves the original image bytes. Historical hash records retain the filename used at capture time. The six published Parts 1-2 images are unchanged.
