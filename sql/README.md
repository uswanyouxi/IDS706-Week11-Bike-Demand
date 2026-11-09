001_application.sql is applied by the loader inside the same application-DB
transaction as the run-provenance insert, date-keyed upsert and verification.
An advisory transaction lock serializes concurrent loaders. No tables are dropped.
verify_rows.sql provides read-only row-count, date coverage and provenance queries.
Never execute these scripts against Airflow's metadata database.
