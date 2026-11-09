"""Transactional application PostgreSQL; never use Airflow metadata tables."""
from datetime import date
import os
from pathlib import Path
import pandas as pd
import psycopg
from psycopg.types.json import Jsonb
from bike_demand.contracts import FINAL_COLUMNS, dataset_hash, require, validate_final

TABLE = "bike_analytics.bike_daily"
SELECT_DATA = "SELECT "+", ".join(FINAL_COLUMNS)+" FROM "+TABLE+" ORDER BY date"

def app_connect():
    name = os.environ.get("APP_DB_NAME", "bike_demand")
    require(name != "airflow", "Application data must not use Airflow metadata DB")
    return psycopg.connect(host=os.environ.get("APP_DB_HOST", "app-db"),
        port=int(os.environ.get("APP_DB_PORT", "5432")), dbname=name,
        user=os.environ.get("APP_DB_USER", "bike_app"), password=os.environ["APP_DB_PASSWORD"],
        connect_timeout=10, options="-c statement_timeout=60000")

def read_frame(connection):
    with connection.cursor() as cursor:
        cursor.execute(SELECT_DATA)
        frame = pd.DataFrame(cursor.fetchall(), columns=FINAL_COLUMNS)
    if not frame.empty:
        frame["date"] = frame["date"].map(lambda v: v.isoformat())
        for c in ["cnt", "yr", "mnth", "weekday", "season"]:
            frame[c] = frame[c].astype("int64")
    return frame

def load_frame(frame, run_id, sources, validation, *, connect=app_connect):
    validate_final(frame)
    digest = dataset_hash(frame)
    migration = Path(__file__).resolve().parents[2]/"sql"/"001_application.sql"
    with connect() as connection:
        with connection.transaction():
            connection.execute("SELECT pg_advisory_xact_lock(7061101)")
            connection.execute(migration.read_text(encoding="utf-8"))
            connection.execute("""INSERT INTO bike_analytics.pipeline_runs
                (run_id,dataset_hash,row_count,sources,validation) VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (run_id) DO UPDATE SET dataset_hash=EXCLUDED.dataset_hash,
                row_count=EXCLUDED.row_count,sources=EXCLUDED.sources,validation=EXCLUDED.validation,
                loaded_at=now(),eda_summary=NULL""",
                (run_id, digest, len(frame), Jsonb(sources), Jsonb(validation)))
            columns = FINAL_COLUMNS+["dataset_hash", "pipeline_run_id"]
            update = ", ".join(f"{c}=EXCLUDED.{c}" for c in columns if c != "date")
            statement = (f"INSERT INTO {TABLE} ({', '.join(columns)}) VALUES "
                f"({', '.join(['%s']*len(columns))}) ON CONFLICT (date) DO UPDATE SET {update}, loaded_at=now()")
            records = frame.to_dict(orient="records")
            values = [(date.fromisoformat(r["date"]), *[r[c] for c in FINAL_COLUMNS[1:]], digest, run_id) for r in records]
            with connection.cursor() as cursor:
                cursor.executemany(statement, values)
            persisted = read_frame(connection)
            require(len(persisted) == len(frame), "Persisted row count mismatch")
            require(dataset_hash(persisted) == digest, "Persisted content hash mismatch")
            count, distinct_dates = connection.execute(
                f"SELECT count(*), count(DISTINCT date) FROM {TABLE}").fetchone()
            require(count == distinct_dates == len(frame), "Database duplicate/count mismatch")
    return dict(run_id=run_id, dataset_hash=digest, rows=int(count), distinct_dates=int(distinct_dates),
                database=os.environ.get("APP_DB_NAME", "bike_demand"), table=TABLE)

def read_snapshot(run_id, expected_hash, *, connect=app_connect):
    # Fresh connection and SELECT, not the caller's in-memory merged frame.
    with connect() as connection:
        with connection.transaction():
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            frame = read_frame(connection)
            require(dataset_hash(frame) == expected_hash, "EDA database hash mismatch")
            stored = connection.execute("""SELECT dataset_hash,row_count,sources,validation
                FROM bike_analytics.pipeline_runs WHERE run_id=%s""", (run_id,)).fetchone()
            require(stored is not None and stored[0] == expected_hash and stored[1] == len(frame),
                    "EDA run provenance mismatch")
            hashes = connection.execute(f"SELECT DISTINCT dataset_hash FROM {TABLE}").fetchall()
            require(hashes == [(expected_hash,)], "Mixed dataset versions in database")
    return frame, dict(run_id=run_id, dataset_hash=expected_hash, rows=len(frame),
        database=os.environ.get("APP_DB_NAME", "bike_demand"), table=TABLE,
        query=SELECT_DATA, sources=stored[2], validation=stored[3])

def record_analysis(run_id, summary):
    with app_connect() as connection:
        cursor = connection.execute("UPDATE bike_analytics.pipeline_runs SET eda_summary=%s WHERE run_id=%s",
                                   (Jsonb(summary), run_id))
        require(cursor.rowcount == 1, "EDA provenance update failed")
