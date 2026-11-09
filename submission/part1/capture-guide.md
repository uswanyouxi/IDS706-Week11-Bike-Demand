# Airflow 3.4.0 screenshot and page guide

The required real Airflow captures are complete and visually reviewed. The current [six-image submission index](../../screenshots/README.md) supersedes the old capture plan.

- [01_airflow_dag_success.png](../../screenshots/01_airflow_dag_success.png): DAG overview/Grid with all nine task rows green for three runs.
- [02_airflow_graph.png](../../screenshots/02_airflow_graph.png): actual DAG graph with independent download/clean branches, merge, PostgreSQL load and database-fed analysis.

DAG ID: dc_bike_weather_daily. Verified manual evidence run: phase_b_manual_02. Screenshot 01 shows the all-runs overview rather than an individual run selector; the exported CLI records separately establish each successful run and its nine task states. Screenshot 02 is a dependency graph and does not alone prove measured task overlap.

## Exact page locations

| Page | URL |
| --- | --- |
| DAG list | http://localhost:8080/dags |
| DAG overview / Grid or Graph pane | http://localhost:8080/dags/dc_bike_weather_daily |
| Run history | http://localhost:8080/dags/dc_bike_weather_daily/runs |
| Successful run / Task Instances | http://localhost:8080/dags/dc_bike_weather_daily/runs/phase_b_manual_02 |
| Run metadata | http://localhost:8080/dags/dc_bike_weather_daily/runs/phase_b_manual_02/details |
| DAG schedule/configuration | http://localhost:8080/dags/dc_bike_weather_daily/details |

Log in privately with the existing local admin credentials. Grid/Graph are visualization controls within the DAG/run layout; use the square-grid or branching icon and widen/zoom the pane for readable names.

Task IDs are start, download_uci, fetch_era5_weather, clean_bike, clean_weather, validate_and_merge_dates, load_application_postgres, read_database_and_make_eda and end. The graph splits after start into two independent ingestion/cleaning paths and converges at merge.

Daily schedule: cron 0 6 * * *, America/New_York, catchup=False. Browser display timezone may differ; winter 06:00 New York corresponds to 11:00 UTC.

## SQL and EDA evidence

No separate SQL/EDA/schedule screenshot is claimed in the six-image set. Original [PostgreSQL verification](postgres_report.md), [read-only SQL](postgres_verify.sql), and [EDA summary](eda/summary.json) remain real exported evidence. Screenshot 01 includes Grid and cron; supporting source/runtime records establish schedule and observed overlap.

Only the six exact reviewed image filenames are allowlisted by .gitignore. Use [the final staging manifest and commands](../../docs/submission.md); forced staging is unnecessary. Nothing has been staged, committed or pushed.

## Navigation references

These official release references were consulted during the original evidence preparation:

- [Airflow 3.4 UI overview](https://airflow.apache.org/docs/apache-airflow/3.4.0/ui.html)
- [3.4 release routes](https://github.com/apache/airflow/blob/3.4.0/airflow-core/src/airflow/ui/src/router.tsx)
- [Details layout with Grid/Graph panels](https://github.com/apache/airflow/blob/3.4.0/airflow-core/src/airflow/ui/src/layouts/Details/DetailsLayout.tsx)
