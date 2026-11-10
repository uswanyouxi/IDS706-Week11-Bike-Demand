# Part 1: PostgreSQL and EDA evidence

The original Airflow pipeline downloads UCI daily bike counts and Open-Meteo ERA5 weather, cleans each source independently, validates a one-to-one date merge, loads application PostgreSQL and queries it back for analysis. See the [root README](../../README.md) for architecture and running instructions.

## Verified results

| Measure | Recorded result |
| --- | --- |
| DAG | dc_bike_weather_daily; daily 06:00 America/New_York |
| Successful executions | Three recorded runs, nine successful tasks each |
| Date coverage | 2011-01-01 through 2012-12-31 |
| Final rows / unique dates | 731 / 731 |
| Date merge | 731 matches; zero bike-only or weather-only dates |
| Total rentals | 3,292,679 |
| Repeated loads | Same row count, unique dates and dataset hash; no duplicates |

The [read-only PostgreSQL report](postgres_report.md) records the query time, totals and load history. [Before](idempotence_before.json) and [after](idempotence_after.json) snapshots document the controlled idempotence test. These are recorded observations, not a claim that this page continuously queries live services.

## Three database-fed EDA charts

Charts were exported unchanged from the verified phase_b_manual_02 artifacts. The analysis opens a fresh application-database connection after loading; it does not analyze the in-memory merge or a host CSV.

| Chart | Content |
| --- | --- |
| [Weekday mean rentals](eda/weekday_mean_rentals.png) | Average daily rentals by weekday |
| [Monthly mean rentals](eda/monthly_mean_rentals.png) | Average daily rentals by calendar month |
| [Weather and demand](eda/weather_vs_demand.png) | Rental count versus temperature, with precipitation shown by color |

Mean demand is **4,504.35 rentals/day**. Pearson correlations are **0.607441** for temperature and **-0.280501** for precipitation. These are descriptive historical associations, not causal effects or a future forecast. The [EDA summary](eda/summary.json) retains the actual query, run ID, provenance and dataset hash.

## Validation and reproducibility

- [Bike cleaning](validation/bike.json), [weather cleaning](validation/weather.json), [date merge](validation/merged.json) and [committed load receipt](validation/load-receipt.json).
- [Recorded PostgreSQL snapshot](postgres_live_snapshot.json) and [read-only SQL](postgres_verify.sql).
- [Airflow task/run verification](airflow/live-check.json) and [export hashes/origin](manifest.json).
- [Real application screenshots](../../screenshots/README.md): successful Airflow Grid and parallel graph.
- [Part 1 runtime report](../../docs/verification/phase-b/status.md).

Machine-readable exports, image bytes and historical logs retain their original contents and timestamps. Parts 1 and 2 are complete; the separate [optional adaptive extension](../../bonus/README.md) documents its own results and baseline limitations.
