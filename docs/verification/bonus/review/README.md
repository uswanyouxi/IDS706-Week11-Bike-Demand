# Bonus final independent-review preparation

This report supersedes pending-capture/staging wording in earlier Bonus reports. Historical runtime outputs and scores are unchanged. Branch: bonus/adaptive-multi-agent; verified main remains d3a4465. No commit, merge or push is performed.

## Requirement-by-requirement status

| Requirement | Review result |
| --- | --- |
| Distinct original specialist graph | VERIFIED: actual compiled graph, role calls and recorded events; original training/routing code unchanged |
| Conditional routing, selection and explanations | VERIFIED for the declared cases: independent event-based oracle recomputes destinations/reasons from phase, measured gaps and budgets |
| Bounded retries/recovery and terminal failures | VERIFIED: exact scenario fault types/stages, load/fit/recovery counts, terminal node, and no held-out artifacts after expected failures |
| Intermediate data/feature/selection quality | VERIFIED with limits: snapshot contract/hash, training-derived diagnostics, chronological boundaries, allowed features and selected candidate identity checked |
| Final output metrics | VERIFIED: selected/Dummy MAE, RMSE and R2 independently recomputed from saved predictions; weak-model scenario remains weak |
| Explicit cases, criteria and thresholds | VERIFIED: 9 cases x 3 policies, all 27 actual saved executions pass the stricter artifact review; score threshold 1.0 means every applicable check must pass |
| Same-problem comparison | VERIFIED only for explicitly adapted regression ports; all three normal policies have equal held-out metrics |
| Native fixed Airflow and simple-agent comparison | PARTIAL: native prep CLI and simple classification graph ran; original classroom Airflow DAG did NOT run. Ports are not exact classroom baselines |
| Real screenshots | Seven actual reviewed Bonus PNGs included. Image 14 shows policy-level bars, not per-agent timings/calls |
| Parts 1-2 preservation | Verified algorithms, production dataset, published six images and old runtime evidence remain unchanged; only README/Git-ignore/screenshot documentation changes are authorized |
| Tests / links / secrets / staging | Current results in checks.json; explicit manifest supplied and refreshed staging verified; no commit, merge or push |

## Actual reviewed screenshots

See [the current screenshot index](../screenshot-guide.md). Actual names: 10_bonus_adaptive_graph.png, 11_bonus_routing_recovery.png, 11b_bonus_recovery_events.png, 12_bonus_evaluation_suite.png 12b_bonus_evaluation_criteria.png, 13_bonus_baseline_comparison.png and 14_bonus_agent_metrics.png.

Both additional genuine PNGs are now included. Image 13 shows the regression comparison and scenario results; image 14 shows policy completion/pass-rate bars, not the per-agent calls/timing table suggested by its filename. The native/port warning is outside image 13's crop. A readable per-agent table and native limitations panel would improve visual evidence; complete records remain in JSON. See [submission preparation details](submission-preparation.md).

## Evaluation audit: weaknesses and corrections

The original assess() checks use real scenario-driven execution records, but some individual predicates are weak:

- all(...) over an empty route list can pass vacuously.
- Counters bounded only by <= do not prove that a declared retry-exhaustion case exhausted its budget.
- Finite metrics are a numerical validity check, not a model-quality threshold.
- A contract_valid flag, forbidden-name exclusion alone, and partition sizes alone trust producer summaries.
- Minimum RMSE alone does not prove that the reported model identity/features correspond to the winning trial.
- Agent durations >=0 do not prove that the reported times match execution.
- A mirrored router specification can share mistakes with production code; a zero measured error rate over designed cases does not establish a general rate.

The added audit_saved_run() independently reads actual events, topology, snapshots and predictions. It requires nonempty paired/ordered events, graph-valid transitions, exact observed counters/error classes/recovery destinations, specific reasons, and one correct terminal node. It checks snapshots/contracts/hashes, nonempty allowed features, actual temporal boundaries, independently computed Dummy validation metrics, winning model identity, report/event consistency and measured role times. It recomputes final MAE/RMSE/R2 and forbids test artifacts after expected failures.

Future evaluate_suite() grades now require both the original checks and the independent artifact gate. Sixteen audit-focused tests and one suite-level tampering test reject empty logs, forged counters/features/model identities/quality/timings, altered predictions and premature exhaustion. Numerical metric agreement uses relative/absolute tolerance 1e-10; candidate RMSE identity uses 1e-12. These are numerical-consistency thresholds, not post-hoc model-quality cutoffs. The audit itself does not fit models. A separate audit result preserves old scores rather than rewriting the captured historical suite.

The new auditor initially assumed a baseline field existed in events; it was corrected to use the report baseline and independently verify it from the snapshot. Synthetic CSV verification also needed round-trip float parsing. Initial diagnostic/test failures are retained; final tests pass. These were audit-tool defects, not failures of the previously verified production workflows.

### Residual limitations

Candidate validation predictions were not saved, so their metrics cannot be independently recomputed from prediction files without refitting. This review checks their logged consistency/selection and tests metric calculations, but does not claim a complete independent reproduction of each validation score. No post-hoc held-out performance cutoff was introduced. Passing contract tests is distinct from predictive superiority or statistical generalization.

Faults are isolated copies/injected exceptions with known expected policies, not real production outages or a broad randomized benchmark. Timing is single-run graph time, not comparable native Airflow scheduler latency or statistically significant speed evidence.

## Evidence and automated tests

Final tests: **102 passed, zero failed, zero skipped**:

- 43 Bonus tests, including read-only PostgreSQL integration and 17 new audit/counterexample tests.
- 19 unchanged Part 2 tests.
- 39 unchanged pipeline unit tests.
- 1 unchanged real DAG-import/schedule/dependency test.

The fresh submission rerun also passed all 102 tests. Non-failing warnings were the upstream LangChain pending deprecation and the temporary DAG test harness's unregistered airflow mark. A host console GBK rendering error occurred after the 39 pipeline tests had already saved their successful JUnit/log; it did not invalidate or rerun those tests. Initial failed new-auditor checks are retained separately from final successful JUnit/log files. No production model or DAG was rerun; only synthetic unit fixtures were fitted. Old Part 1-2 and Bonus runtime evidence was not overwritten.

- [Current machine-readable checks](checks.json)
- [Independent audit of the 27 saved executions](evaluation-audit.json)
- [Fresh Bonus/Part 2 JUnit](submission-bonus-ml.xml)
- [Fresh pipeline JUnit](submission-pipeline.xml), [fresh DAG-import JUnit](submission-dag.xml)
- [Original comparison evidence](../runtime/evaluations/bonus_suite_01/summary.json)
- [Native classification evidence and explicit non-DAG scope](../runtime/classroom/classroom_probe_01/summary.json)

Original model findings are unchanged: selected Ridge alpha=10, held-out MAE 904.71, RMSE 1202.36, R2 0.5231; one negative prediction, unclipped. Adaptive, fixed_port and simple_port normal scores are identical. No native-classroom superiority is claimed.

## Exact staging and pre-commit review process

The [Bonus staging list](bonus-staging.txt) contains only modified tracked files and new Git-eligible Bonus source/tests/UI/configuration, reviewed screenshots and reproducibility evidence. It excludes unchanged main files, credentials, caches, raw classroom-reference cache and unreviewed/missing screenshots. Inspect every listed path.

~~~powershell
py -3.11 bonus/review_submission.py
Get-Content -Encoding UTF8 docs/verification/bonus/review/bonus-staging.txt
git -c "safe.directory=$PWD" --literal-pathspecs add --pathspec-from-file=docs/verification/bonus/review/bonus-staging.txt
git -c "safe.directory=$PWD" diff --cached --check
git -c "safe.directory=$PWD" diff --cached --stat
git -c "safe.directory=$PWD" status --short
~~~

The original 291 files were staged by the user; this preparation refreshes the exact manifest and stages only reviewed submission updates. No commit, merge or push is performed. Existing evidence writers target historical snapshots and may flag the newly authorized .gitignore/screenshots README changes; use the current review script instead of overwriting old verification reports.

## Remaining grading/submission risks

The strict two-classroom-baseline requirement is the largest unresolved risk. A documented CLI prep run is not an original Airflow DAG run. The simplified simple_port omits native memory/LLM/one-pass fit repair; its lower completion rate is not evidence against the real classroom system. Instructor acceptance of the adapted comparison or separately approved faithful native reproduction is still needed.

Seven captures support the actual graph, recovery, scores and declared criteria. Image 14 does not show per-agent calls/timings, and the comparison crop does not contain native-baseline limitations. No full-bonus or all-25-points claim is made. Canvas submission/AI-use requirements and any final commit/push remain the user's decisions.
