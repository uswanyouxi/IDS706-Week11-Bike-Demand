# Chosen Project — DC Bike Demand & Weather Intelligence Pipeline

## Research problem
How do weather and calendar factors relate to daily Capital Bikeshare rental demand in Washington, DC, and can a simple ML model predict historical daily rental counts?

## Two independent data sources
1. UCI Bike Sharing Dataset, `day.csv` (daily Capital Bikeshare rentals, 2011-01-01 to 2012-12-31, ~731 records): https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset
2. Open-Meteo Historical Weather API, Washington DC point (38.9072, -77.0369), daily date range 2011-01-01 to 2012-12-31, timezone America/New_York. Documentation https://open-meteo.com/en/docs/historical-weather-api ; API base https://archive-api.open-meteo.com/v1/archive . Request daily temperature_2m_mean, temperature_2m_max, temperature_2m_min, precipitation_sum, wind_speed_10m_max. Explicit `models=era5` may be appropriate for consistent historical reanalysis, validate availability.

## Data schema, transformation and merge
- UCI `dteday` is a date; target `cnt` is number of rentals; features e.g. `weekday`, `workingday`, `holiday`, `season`, `mnth`.
- The UCI source also contains `casual`, `registered`, `temp`, `atemp`, `hum`, `windspeed`, `weathersit`; do not use casual/registered as ML features because `cnt=casual+registered`. Prefer weather inputs from independent Open-Meteo source to demonstrate meaningful integration, and document other exclusions.
- API `daily.time` -> date. Other daily arrays -> date-indexed records, validate array lengths and non-null values.
- Parse and normalize two dates to local dates. Validate unique dates on each side and a strict one-to-one merge on date with explicit unmatched counts.
- Persist merged result into application PostgreSQL database (separate from Airflow metadata), using idempotent upsert or replace-in-transaction.
- Rerun safely without duplicate rows; cache raw source responses optionally for offline testing, but production ingestion must trace to real URL/API.

## DAG outline
Start -> parallel branches A: download UCI + clean bike data, B: fetch Open-Meteo + clean weather data -> validate/merge -> write PostgreSQL -> read from PostgreSQL and produce EDA charts + summary -> end. Use actual schedule e.g. `@daily`, catchup=False, bounded retries, separate outputs as artifacts, explicit dependency graph. Data is historical and static: explain schedule reruns as reproducibility/refresh exercise, not claim there are daily 2011-12 updates.

## EDA & ML
- EDA: rental counts by weekday/month; compare demand vs precipitation or temperature. Read from PostgreSQL after load.
- Regression target: `cnt`. Metrics MAE, RMSE and optionally R2. Use chronological train/validation/test splitting; show baseline DummyRegressor vs Ridge/RandomForestRegressor/HistGradientBoostingRegressor, avoid overfitting 731 rows.
- Historical daily observed weather is not a known future forecast. Frame as retrospective explanatory analysis/backtesting. For actual forward prediction a future forecast feed would be needed.
- Agent workflow: load data -> feature agent -> train -> evaluate -> conditional router -> retry with another model/hyperparameter if justified and under max_attempts -> report. Agent workflow MUST have a real state machine graph, conditional branching, bounded loop and live execution visualization; labels/metrics must match task.
- Bonus optional: separate specialist agents, adaptive routing/retries, test suite with expected outcomes + thresholds, explicit fair baselines using actual class demo implementation.

## Evidence and honesty
- Never fabricate screenshots, metric values, test results, source columns, downloaded files, DAG success, or model quality.
- Must record exact tested commands, results, database row counts, API response validity, join coverage and any missing prerequisites.
- Require approval before publishing/pushing to GitHub or deploying.
