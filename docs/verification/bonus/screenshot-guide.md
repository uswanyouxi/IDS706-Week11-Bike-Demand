# Reviewed Bonus screenshots and content limitations

Seven reviewed Bonus captures are present in screenshots/. They were inspected as real application images and remain unchanged. The six published Parts 1-2 screenshots are also unchanged. This index supersedes the earlier planned filenames/locations.

| Actual file | What is visible |
| --- | --- |
| [10_bonus_adaptive_graph.png](../../../screenshots/10_bonus_adaptive_graph.png) | bonus_main_01; original coordinator/specialist graph with refinement visited; three attempts and zero recoveries |
| [11_bonus_routing_recovery.png](../../../screenshots/11_bonus_routing_recovery.png) | bonus_suite_01_transient_training_adaptive; completed graph with recovery visited, three attempts and one recovery |
| [11b_bonus_recovery_events.png](../../../screenshots/11b_bonus_recovery_events.png) | Cropped recorded trace showing recovery then resumption at model_selection and attempt two; some text is truncated horizontally |
| [12_bonus_evaluation_suite.png](../../../screenshots/12_bonus_evaluation_suite.png) | bonus_suite_01; actual adaptive/fixed_port/simple_port comparison and observed case statuses, scores, thresholds and passes |
| [12b_bonus_evaluation_criteria.png](../../../screenshots/12b_bonus_evaluation_criteria.png) | Expanded real case definitions showing inputs, expected outcomes, criteria and thresholds; this is not the full nine-case table in one image |
| [13_bonus_baseline_comparison.png](../../../screenshots/13_bonus_baseline_comparison.png) | Real bonus_suite_01 comparison table with equal held-out regression scores, completion/pass rates and scenario outcomes; native/port warning is outside the crop |
| [14_bonus_agent_metrics.png](../../../screenshots/14_bonus_agent_metrics.png) | Policy-level completion/pass-rate bars and collapsed criteria expander; no per-agent timing/call table is visible despite the filename |

Both additional PNGs were visually reviewed without editing or renaming. A readable per-agent calls/timings capture and the native-reference limitation panel remain useful supporting evidence. The existing per-agent values are retained in actual report JSON. All seven real names are explicitly allowlisted.

Actual application: **http://localhost:8502**, Optional Part 3. The original Part 2 page remains at http://localhost:8501 and in the wrapper navigation.

Optional additional captures:

- Select bonus_suite_01; include the comparison table and the warning that fixed/simple rows are regression ports, plus the separate native-reference summary.
- Select bonus_main_01; scroll to Agent-level validation and decisions; show measured calls, durations and errors.
- To inspect dynamic feature routing, select bonus_main_01, uncheck Follow bonus execution and replay event 24.
- For recovery, select bonus_suite_01_transient_training_adaptive and inspect the actual recorded recovery events. The captured images show the completed trace; they are not claimed to be an event-24 replay or an in-flight screen.

Original scores/screenshots document the original evaluation. The independent final review rechecks saved traces, fault counts, snapshots and predictions without retraining or rewriting those records. See [the review report](review/README.md) and [baseline limitations](../../../bonus/COMPARISON.md). Passing expected-failure cases is distinct from successful model completion.
