# Optional Part 3: real implementation and verification

Branch: **bonus/adaptive-multi-agent**, based on verified main **d3a4465**. The controlled runtime test was explicitly approved. Parts 1 and 2 source, Docker definitions, data, evidence and six screenshots are preserved. Only a short optional section is appended to the root README; main itself is not changed, committed, merged or pushed.

**Status: adaptive implementation and controlled runtime VERIFIED; strict classroom-baseline comparison PARTIAL.** Do not claim that every official bonus requirement or all 25 bonus points is satisfied.

## Requirement-by-requirement checklist

| Official requirement / user constraint | Status | Actual evidence |
| --- | --- | --- |
| Distinct specialist responsibilities and graph | VERIFIED | Data loader, quality, feature analysis/refinement, model selection/training, evaluation, coordinator, recovery and reporting; real compiled StateGraph |
| Adaptive selection/routing from intermediate results | VERIFIED | Main run selected feature refinement after measured gap 2.8163 and collinear weather, then stronger Ridge and forest |
| Bounded retry and recovery | VERIFIED | Actual isolated transient DB/fit cases recovered; permanent/contract failures rejected; 3 candidate / 2 DB-load / 2 recovery limits |
| Meaningful shared state / explanations | VERIFIED | Actual provenance, training diagnostics, trials, best candidate, issue type/stage/budgets and a reason for each coordinator destination |
| Application PostgreSQL input / provenance | VERIFIED | READ ONLY repeatable-read snapshot; 731 dates, 3,292,679 rentals, same persisted hash before/after |
| Leakage protection / chronological partitions | VERIFIED | Calendar + independent weather inputs; forbidden target/ID/UCI-weather fields excluded; 365/182/184 partitions, training-only transforms |
| Validation-only selection / one final held-out stage | VERIFIED | Best validation candidate retained; final selected/Dummy fit on 547 rows and test once on 184; no tuning back edge |
| Intermediate, final and coordination evaluation | VERIFIED | Contract/feature/selection/reliability assertions, actual MAE/RMSE/R2, attempts/recovery/route correctness, report completeness, timing and RSS |
| Every case has input, expected behavior, scoring and threshold | VERIFIED | Nine cases x three policies; actual results include observed status, assertions, score and pass/fail; all 27 cases passed expectations |
| Comparison against classroom fixed Airflow AND simple-agent baselines | PARTIAL | Sources pinned/reviewed; native prep CLI and native simple graph executed on fraud; both direct cnt probes failed with ValueError; fair regression ports executed separately. Exact original Airflow DAG was NOT executed |
| Original source / container instructions / graph / evaluation / comparison summary | VERIFIED | New isolated package, additive Compose overlay, compiled graph exports, real suite and comparison document |
| Dashboard displays actual graph/progress/routes/metrics/evaluation/comparison | VERIFIED | Real running UI at localhost:8502; AppTest checks graph, event replay, recovery, 27 rows, 3 policies, actual metrics and original Part 2 navigation |
| Manual screenshots | MANUAL | Exact guide prepared; no bonus application screenshots fabricated or claimed captured |
| Preserve verified main / Part 1-2 evidence | VERIFIED | All original non-README bytes and timestamps audited; original source/config unchanged, README original text retained before appended bonus section |
| No paid API / no production fault injection / no destructive Git or Docker action | VERIFIED | Pinned existing ML image; no-key native fallbacks; fault copies/exceptions only; no original service restart, volume deletion, commit, merge or push |

## Actual database-fed main execution

Run: **bonus_main_01**. All 731 cleaned rows came from application PostgreSQL. Dataset hash:
99123ac3758014b572f0ac290b1cfcba3896a8fae47896055eb1cc9d89579a33.

| Attempt | Candidate | Feature count | Training RMSE | Validation RMSE | Decision afterward |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | Ridge alpha=10 | 12 | 558.8227 | 1573.8114 | Feature refinement from gap/collinearity |
| 2 | Ridge alpha=100 | 10 | 608.6806 | 1588.2419 | Another candidate from remaining gap |
| 3 | Forest, 120 trees | 10 | 405.7395 | 2275.1290 | Finite attempt budget exhausted |

Selection retained the first Ridge with all 12 inputs. The explored alternatives did not improve validation RMSE. Held-out metrics were MAE **904.706465**, RMSE **1202.361305**, R2 **0.523123**; Dummy had MAE **2452.640301**, RMSE **2694.302464**, R2 **-1.394579**. One prediction was negative, unchanged and unclipped.

Main execution recorded 29 node operations, including 14 coordinator calls, 3 training/evaluation calls and one refinement. Streaming/report wall time was 0.2341 seconds; worker-lifetime RSS high-water was 248,996 KiB (243.16 MiB). This excludes Docker startup and is not a statistical latency benchmark.

This remains a retrospective observed-weather backtest. No held-out metric triggered retraining or selection.

## Real evaluation and comparisons

- 27 isolated evaluations: **27 expected-behavior passes**, zero incorrect routes under the declared oracle.
- Adaptive completed 4/9 workflow cases, fixed_port 4/9, simple_port 2/9. Expected input rejection/failure is counted separately from task completion.
- All three normal-case regression policies selected the same Ridge and had identical held-out metrics. Adaptive used more attempts/time; no predictive superiority is claimed.
- Across nine cases: adaptive 16 attempts / 4 recoveries; fixed_port 9 / 4; simple_port 7 / 0.
- The exact recovery destination and minimum validation-RMSE selection were independently checked; counterexample unit tests detect deliberately incorrect values. Existing records were reassessed without refitting.

Native classroom references were fetched at commit a294145ea9aa4225908ce701c06160c33213335d and verified by Git blob checksums. Original prep CLI: fraud validation F1 0.060606, accuracy 0.535. Original simple graph: fraud held-out F1 0.085366, accuracy 0.625, two cycles. These are classification results on different data/splits, not bike-demand metrics.

The fixed/simple regression ports are deliberately labeled adaptations. Fixed_port is not an Airflow scheduler run. Simple_port omits native memory/LLM/spec-repair features; its recovery-completion rate cannot be used to claim superiority over the real classroom agent. The exact classroom Airflow DAG and a fidelity-matched same-problem native comparison remain unverified.

See [actual comparison and limitations](../../../bonus/COMPARISON.md) and [all cases/observations](evaluation-cases.md).

## Tests and verification

Final tests: **85 passed, zero failed, zero skipped**:

- Bonus: 26, including real read-only PostgreSQL integration and two oracle counterexample tests.
- Original pipeline unit tests: 39.
- Original Part 2 ML unit tests: 19.
- Original real Airflow DAG import/schedule/edge test: 1.

Initial 23 synthetic passes / one explicit DB skip and the earlier 24-test integration run are retained as historical bonus logs. Final tests do not rerun the original production DAG or Part 2 model.

One upstream LangChain pending-deprecation warning remains. PowerShell can wrap Docker stderr/progress as NativeCommandError even when exit code is zero; actual pytest/JUnit/process results establish success. Bare Streamlit AppTest context warnings are expected. AppTest is backend verification, not browser-pixel or screenshot verification.

[Final machine-readable checks](final-checks.json), [26-test JUnit](final-bonus-tests.xml), [main report](runtime/runs/bonus_main_01/report.json), [suite summary](runtime/evaluations/bonus_suite_01/summary.json), [native reference probes](runtime/classroom/classroom_probe_01/summary.json), and [all changed/new files](changed-files.txt) contain the concrete evidence.

## Runtime/resources and preservation

Reused ids706-ml:1.0.0; no build or image pull was needed. New services only: bonus-runner (one serial worker, 1 CPU / 1 GiB cap) and bonus-dashboard (0.5 CPU / 512 MiB cap, localhost:8502). Existing Compose definitions were compared and found identical.

Host free RAM was around 1.17 GiB, with about 5.48 GiB available in WSL and 38.1 GiB free on D:. To avoid overlapping the new heavy processes, the driver completed production/evaluation/reference workers before starting the new dashboard. Memory gates required at least 1 GiB host free and 3 GiB guest available before each step; no forced startup occurred. Existing services remain healthy. RSS figures are process-lifetime high-water values, not isolated per-case peaks; peak Windows/whole-stack memory was not measured.

Database before/after snapshots match exactly and were server-enforced READ ONLY. Fault cases were in-memory copies or declared exceptions. No original DAG was rerun, and no original services/volumes/data were stopped, recreated, deleted or migrated.

## Manual submission work / remaining rubric gap

Capture the real pages using [the exact screenshot guide](screenshot-guide.md). No bonus screenshots have been created by the agent. The original six screenshots remain unchanged.

A strict native classroom fixed-Airflow execution/comparison is still missing. Completing that would require a separately scoped approved reproduction and/or instructor confirmation that the explicit regression ports satisfy the comparison requirement. No full-bonus grade claim is made.

Review this local branch and all new evidence before deciding to commit/push. No commit, push, merge, history rewrite, external deployment or credential change was performed.
