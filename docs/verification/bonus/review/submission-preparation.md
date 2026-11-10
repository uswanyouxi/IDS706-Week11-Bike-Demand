# Evidence integrity

The runtime evidence records actual application/database executions. Historical JSON, predictions, charts and test logs retain their original contents and modification timestamps.

- [Log inventory](logs-preservation.json): byte hashes and original timestamps of 98 logs before final submission packaging.
- [Frozen Bonus exports](../runtime-export-sha256.json): 202 runtime artifact hashes.
- [Parts 1-2 preservation baseline](../preservation-before.json): original verified main files.
- [Current documentation checks](../../documentation-checks.json): authorized documentation changes, source/evidence preservation and filename validation.

Docker progress logs contain genuine trailing spaces. The Bonus-scoped .gitattributes disables only end-of-line-blank checks for these *.log files; source/documentation whitespace checking remains active. No historical log was trimmed or regenerated.

The reviewed policy chart was renamed by the author without changing its bytes. The [current screenshot index](../../../../screenshots/README.md) and file inventory use its current filename; historical hash records retain the capture-time name. It shows policy rates, not per-agent calls or timings.

Read-only production verification records **731 unique dates and 3,292,679 rentals**, with dataset hash 99123ac3758014b572f0ac290b1cfcba3896a8fae47896055eb1cc9d89579a33. Verification snapshots document their original query times rather than implying continuous live checks.

[Comparison limitations](../../../../bonus/COMPARISON.md) remain explicit: regression ports are adaptations, both original native baselines are now [separately reproduced](../native-classroom/results.md), and finite designed fault coverage does not establish broad reliability or predictive superiority.
