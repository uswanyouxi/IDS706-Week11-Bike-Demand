-- Execute against app-db / bike_demand, never airflow-db.
SELECT count(*) AS rows, count(DISTINCT date) AS unique_dates,
       min(date) AS first_date, max(date) AS last_date,
       count(DISTINCT dataset_hash) AS dataset_versions
FROM bike_analytics.bike_daily;
SELECT run_id, row_count, dataset_hash, loaded_at,
       validation->'matched' AS matched_dates,
       validation->'bike_only' AS bike_only,
       validation->'weather_only' AS weather_only,
       eda_summary IS NOT NULL AS analysis_complete
FROM bike_analytics.pipeline_runs ORDER BY loaded_at DESC;
