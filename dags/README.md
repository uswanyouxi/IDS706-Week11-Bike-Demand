The original executable Part 1 DAG is dc_bike_weather.py.
It uses the Airflow 3.4 SDK, a real 06:00 America/New_York cron, two task slots,
catchup=False, bounded retries and independent real-source ingestion/cleaning.
No network/DB IO occurs during parsing. Real import/runtime evidence is recorded
under docs/verification/phase-b; static parsing or host mocks are not DAG success.
