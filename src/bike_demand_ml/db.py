"""Every executable run starts with a consistent READ ONLY PostgreSQL snapshot."""
from bike_demand.storage import app_connect, read_frame, SELECT_DATA
from bike_demand.contracts import dataset_hash, require, validate_final

def load_postgres_snapshot():
    with app_connect() as connection:
        with connection.transaction():
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            readonly=connection.execute("SHOW transaction_read_only").fetchone()[0]
            require(readonly=="on","ML snapshot transaction must be read-only")
            frame=read_frame(connection)
            validate_final(frame)
            digest=dataset_hash(frame)
            versions=connection.execute(
                "SELECT DISTINCT dataset_hash,pipeline_run_id FROM bike_analytics.bike_daily").fetchall()
            require(len(versions)==1 and versions[0][0]==digest,"Mixed or invalid DB dataset version")
            parent=connection.execute("""SELECT row_count,dataset_hash,sources FROM bike_analytics.pipeline_runs
                WHERE run_id=%s""",(versions[0][1],)).fetchone()
            require(parent is not None and parent[0]==len(frame) and parent[1]==digest,
                    "Persisted pipeline provenance mismatch")
            database=connection.execute("SELECT current_database()").fetchone()[0]
            require(database!="airflow","ML cannot use the Airflow metadata database")
    return frame,dict(origin="application_postgresql",database=database,
        table="bike_analytics.bike_daily",query=SELECT_DATA,transaction_read_only=readonly,
        rows=len(frame),dataset_hash=digest,pipeline_run_id=versions[0][1],
        sources=parent[2],snapshot_isolation="repeatable read")
