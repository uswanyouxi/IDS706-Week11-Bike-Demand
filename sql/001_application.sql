-- Application DB only; all DDL and data writes share the loader transaction.
CREATE SCHEMA IF NOT EXISTS bike_analytics;
CREATE TABLE IF NOT EXISTS bike_analytics.schema_migrations (
    version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS bike_analytics.pipeline_runs (
    run_id text PRIMARY KEY, dataset_hash text NOT NULL,
    row_count integer NOT NULL CHECK (row_count > 0),
    sources jsonb NOT NULL, validation jsonb NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(), eda_summary jsonb
);
CREATE TABLE IF NOT EXISTS bike_analytics.bike_daily (
    date date PRIMARY KEY CHECK (date BETWEEN DATE '2011-01-01' AND DATE '2012-12-31'),
    cnt integer NOT NULL CHECK (cnt BETWEEN 0 AND 100000),
    yr smallint NOT NULL CHECK (yr BETWEEN 0 AND 1),
    mnth smallint NOT NULL CHECK (mnth BETWEEN 1 AND 12),
    weekday smallint NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    season smallint NOT NULL CHECK (season BETWEEN 1 AND 4),
    holiday boolean NOT NULL, workingday boolean NOT NULL,
    temperature_2m_mean double precision NOT NULL CHECK (temperature_2m_mean BETWEEN -60 AND 60),
    temperature_2m_max double precision NOT NULL CHECK (temperature_2m_max BETWEEN -60 AND 60),
    temperature_2m_min double precision NOT NULL CHECK (temperature_2m_min BETWEEN -60 AND 60),
    precipitation_sum double precision NOT NULL CHECK (precipitation_sum BETWEEN 0 AND 1000),
    wind_speed_10m_max double precision NOT NULL CHECK (wind_speed_10m_max BETWEEN 0 AND 400),
    dataset_hash text NOT NULL,
    pipeline_run_id text NOT NULL REFERENCES bike_analytics.pipeline_runs(run_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    CHECK (temperature_2m_min <= temperature_2m_mean AND temperature_2m_mean <= temperature_2m_max),
    CHECK (mnth = EXTRACT(MONTH FROM date)),
    CHECK (yr = EXTRACT(YEAR FROM date)-2011),
    CHECK (weekday = EXTRACT(DOW FROM date)),
    CHECK (workingday = (weekday NOT IN (0,6) AND NOT holiday))
);
INSERT INTO bike_analytics.schema_migrations(version) VALUES (1) ON CONFLICT DO NOTHING;
