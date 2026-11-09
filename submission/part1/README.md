> Historical Part 1 evidence bundle: statements below describe its original export scope before Part 2. Final update November 9, 2026: both parts are verified and all six real screenshots are captured. See [the root README](../../README.md) and [current screenshot index](../../screenshots/README.md). The original data, machine-readable records and chart bytes remain unchanged.

# Part 1 submission evidence

This bundle is sourced from real, successful Part 1 executions. It contains no
invented screenshots or model/evaluation results. Successful pipeline logic was
not modified. No new DAG was triggered, database data changed, service stopped,
Part 2 started, or Git push performed.

## Reviewed requirements

The project-supplied assignment/requirements.md and assignment/ta_clarifications.md
were read completely. They require an original scheduled Airflow pipeline, two
distinct related sources cleaned separately and merged, database persistence,
database-fed analysis, setup/README documentation and genuine DAG-success/graph
screenshots. They require an original agent loop for Part 2, which is deferred.
The TA demo pipeline/loop was not reused.

The assignment file is a transcription from the user's screenshots; Canvas's
original wording/deadline and course AI-use policy were not independently accessed.

## Verified current evidence

- DAG: dc_bike_weather_daily.
- All three original successful runs remain in live Airflow.
- Each run still has all nine task instances in success state.
- Current read-only PostgreSQL snapshot: 731 rows, 731 unique dates,
  2011-01-01–2012-12-31, 3,292,679 rentals and one dataset hash.
- Prior before/after refresh snapshots match current totals; all three persisted
  loads use the same hash and have EDA recorded.
- Genuine chart/validation exports match source-container SHA-256 hashes.
- GUI inspection could not start because of the sandbox helper failure; no visual
  observation or screenshot capture is claimed. Use the manual guide.

## Bundle contents

| Location | Purpose |
| --- | --- |
| eda/weekday_mean_rentals.png | Actual PostgreSQL-fed weekday means |
| eda/monthly_mean_rentals.png | Actual PostgreSQL-fed monthly means |
| eda/weather_vs_demand.png | Actual PostgreSQL-fed demand/ERA5 temperature, colored by precipitation |
| eda/summary.json, summary.txt | Findings, exact SELECT, source provenance, run ID and dataset hash |
| validation/bike.json, weather.json, merged.json | Real cleaning coverage/date/timezone and merge diagnostics |
| validation/load-receipt.json | Actual committed row count/hash receipt |
| postgres_report.md / .txt | Human-readable read-only DB and historical idempotence report |
| postgres_live_snapshot.json | Fresh server-enforced READ ONLY query output |
| postgres_verify.sql | Exact read-only verification query |
| idempotence_before.json, idempotence_after.json | Preserved original controlled-run snapshots; not a new experiment |
| airflow/live-runs.json and *-tasks.json | Fresh native Airflow run/task states |
| airflow/live-check.json | Recheck time, 9/9 task verification and next schedule |
| airflow/ui-link-checks.json | HTML route reachability only, not a visual UI check |
| manifest.json | Export origin/run, hash comparisons and no-write/no-screenshot scope |
| repository-state.json | Read-only local Git submission-state check |
| capture-guide.md | Exact pages, manual screenshot filenames and capture instructions |

The source run for these three EDA charts is phase_b_manual_02. They are copied
unchanged from the live project-artifacts named volume, not recomputed from host
raw CSVs. mean daily rentals=4,504.35; temperature Pearson r=0.607441 and
precipitation Pearson r=-0.280501. These are retrospective, confounded associations,
not a trained model, causal claim or future forecast.

## Remaining submission gaps

1. Capture the two required real Airflow UI screenshots (successful run and graph).
   Four supporting screenshots are specified in capture-guide.md.
2. Review and include source/setup/README/evidence and captured PNGs in the final
   repository. Screenshots are ignored by default and require deliberate inclusion.
   The live Git check found no HEAD commit and zero tracked files. No staging/commit/
   push was performed; repository-state.json records that state.
3. Check Canvas's exact submission instructions/deadline and any required AI-use
   disclosure. The full Parts 1–2 submission still needs Part 2 later.

No Part 1 pipeline/runtime gap was found in this evidence recheck. Services remain
running; credentials/tokens are not copied into this bundle.

To refresh the read-only evidence after reviewing its scope:

~~~powershell
py -3.11 scripts/prepare_part1_evidence.py
~~~

The script reads Airflow and app PostgreSQL and copies existing files. It does not
run ingestion, mutate data or test new idempotence through a DAG rerun.
