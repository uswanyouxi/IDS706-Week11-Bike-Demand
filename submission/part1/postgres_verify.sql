BEGIN TRANSACTION READ ONLY;
SELECT json_build_object(
    'checked_at_utc', transaction_timestamp(),
    'transaction_read_only', current_setting('transaction_read_only'),
    'database', current_database(),
    'table', 'bike_analytics.bike_daily',
    'final_counts', (SELECT json_build_object(
        'rows',count(*),'unique_dates',count(DISTINCT date),
        'first_date',min(date),'last_date',max(date),
        'total_rentals',sum(cnt),'dataset_versions',count(DISTINCT dataset_hash),
        'dataset_hash',min(dataset_hash))
        FROM bike_analytics.bike_daily),
    'runs', (SELECT json_agg(r ORDER BY loaded_at) FROM (
        SELECT run_id,row_count,dataset_hash,loaded_at,
            validation->'matched' AS matched_dates,
            validation->'bike_only' AS bike_only,
            validation->'weather_only' AS weather_only,
            eda_summary IS NOT NULL AS eda_complete,
            eda_summary->>'query' AS analysis_query
        FROM bike_analytics.pipeline_runs) r)
);
COMMIT;
