# Read-only PostgreSQL verification

Checked at UTC: 2026-11-09T03:25:27.489362+00:00. Database: bike_demand; table: bike_analytics.bike_daily.
Server transaction_read_only = on. Only SELECT was executed between BEGIN READ ONLY and COMMIT.

| Measure | Live result |
| --- | --- |
| Final rows | 731 |
| Unique dates | 731 |
| Date coverage | 2011-01-01 to 2012-12-31 |
| Total rentals | 3,292,679 |
| Content versions | 1 |

Dataset SHA-256: 99123ac3758014b572f0ac290b1cfcba3896a8fae47896055eb1cc9d89579a33.

## Persisted load history

| Run ID | Loaded rows | Matched | Bike-only | Weather-only | EDA recorded |
| --- | --- | --- | --- | --- | --- |
| scheduled__2026-11-08T11:00:00+00:00 | 731 | 731 | 0 | 0 | True |
| phase_b_manual_01 | 731 | 731 | 0 | 0 | True |
| phase_b_manual_02 | 731 | 731 | 0 | 0 | True |

## Idempotence evidence

The prior controlled runtime test measured the table before and after phase_b_manual_02.
Both saved snapshots show 731 rows, 731 unique dates, 3,292,679 rentals and one dataset version.
All three persisted successful load records share the same content hash.
Today's read-only snapshot matches those totals/hash. No new DAG run or SQL write was performed.

This combines saved before/after evidence with a fresh read; it does not claim a new idempotence experiment.
See idempotence_before.json, idempotence_after.json, postgres_live_snapshot.json and postgres_verify.sql.

The EDA provenance stores an ordered SELECT of persisted cleaned columns from bike_analytics.bike_daily.
This report and the EDA exports are evidence artifacts, not UI screenshots.
