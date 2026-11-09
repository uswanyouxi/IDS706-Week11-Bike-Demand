# Actual bonus comparison and baseline limitations

The three regression policies used the same PostgreSQL-derived input, features, chronological partitions, nine fault cases and held-out metrics. They ran serially in the same pinned ML image. Fixed/simple policies are explicit simplified regression workflow ports, not unmodified classroom executions.

## Regression workflow policies

| System | Test MAE | Test RMSE | R2 | Completed cases | Expected-behavior passes | Incorrect routes | Attempts across cases | Recoveries | Graph wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| adaptive | 904.71 | 1202.36 | 0.5231 | 4/9 | 9/9 | 0 | 16 | 4 | 0.7962 |
| fixed_port | 904.71 | 1202.36 | 0.5231 | 4/9 | 9/9 | 0 | 9 | 4 | 0.2999 |
| simple_port | 904.71 | 1202.36 | 0.5231 | 2/9 | 9/9 | 0 | 7 | 0 | 0.2887 |

Expected rejection of malformed/permanent-failure inputs counts as a passed evaluation case, not a completed modeling run. Timings cover a single worker graph execution, not Docker startup or isolated end-to-end service latency; they do not establish statistically significant speed differences.

The adaptive system explored refinement/regularization/forest candidates but retained Ridge alpha=10. All three normal-case regression policies have identical held-out metrics. Adaptive execution cost more operations/time than fixed_port; no predictive improvement or superiority over the classroom systems is claimed.

The simple_port intentionally omits native classroom memory/context/LLM features and fit-spec repair. The real instructor graph has a one-pass fit-repair path. Consequently the lower simple_port fault-completion rate is a property of this simplified port; it is not evidence that the classroom simple-agent implementation cannot recover. The fixed_port runs in the common LangGraph evaluation harness, not an actual Airflow scheduler.

## Unmodified classroom references: separate classification results

Pinned source: [Kedar-V/automl-research-lab a294145](https://github.com/Kedar-V/automl-research-lab/tree/a294145ea9aa4225908ce701c06160c33213335d), branch refactor/lab-solution-layout. The student lab files are scaffolds; the filled solution files were reviewed. Public references/data are checksum-verified in an ignored local cache, not presented as original project code.

| Reference execution | Data / metric stage | Actual result | Scope |
| --- | --- | --- | --- |
| Documented prep CLI helper | 2,000-row classroom fraud subset; validation | F1 0.060606; accuracy 0.5350 | Original Airflow DAG source reviewed, but its DAG was not executed |
| Original simple LangGraph, no-key fallback | Same classroom fraud subset; held-out, 2 cycles | F1 0.085366; accuracy 0.6250 | Original source executed without paid API |

The original simple graph's best validation F1 was 0.069307. Both direct cnt capability probes ended with ValueError; no MAE/RMSE or successful regression evaluation is claimed for them.

Classification F1/accuracy and bike-demand MAE/RMSE are not interchangeable. Native reference runs use random partitions and a different problem; no model-performance or runtime ranking is made across those incompatible runs.

**Strict classroom baseline comparison is PARTIAL.** The exact classroom fixed Airflow DAG has not been run, and the two regression ports are not exact reproductions of the classroom systems. Closing that rubric item requires an approved native Airflow reproduction and/or instructor acceptance of the explicitly adapted comparison. This branch does not claim all bonus points or complete native-baseline equivalence.

- [Actual regression suite summary](../docs/verification/bonus/runtime/evaluations/bonus_suite_01/summary.json)
- [Actual native reference summary](../docs/verification/bonus/runtime/classroom/classroom_probe_01/summary.json)
- [Source pins/checksums](classroom_sources.json)

## Final review qualification

The seven actual reviewed screenshots are indexed in [the current screenshot guide](../docs/verification/bonus/screenshot-guide.md). Images 12 and 13 show the regression comparison; image 14 shows policy completion/pass-rate bars, despite its agent-metrics filename. Native/port limitations are outside image 13's crop and remain documented above. Per-agent timings and calls remain available in the actual runtime reports; image 14 does not show those values.

Original scores above are unchanged. A later [independent audit](../docs/verification/bonus/review/README.md) checks saved observations, exact scenario fault/retry counts, model identity and recomputed final metrics. It also identifies report-trusting checks, unsaved validation predictions and simplified-port fidelity as limitations. Zero incorrect routes on these nine designed scenarios does not establish a general error rate or a native-baseline advantage.
