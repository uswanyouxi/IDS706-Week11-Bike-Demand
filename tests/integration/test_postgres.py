"""Real PostgreSQL tests only; synthetic rows are not production evidence."""
import os
import uuid
import psycopg
import pytest
from bike_demand import storage
from bike_demand.contracts import dataset_hash

pytestmark=pytest.mark.integration

@pytest.fixture
def test_database(monkeypatch):
    name=os.environ.get("BIKE_TEST_DB_NAME","")
    if not name:
        pytest.skip("Set BIKE_TEST_DB_NAME to an existing disposable *_test PostgreSQL database")
    if not name.endswith("_test") or name=="airflow":
        pytest.fail("Refusing integration tests outside a disposable *_test database")
    monkeypatch.setenv("APP_DB_NAME",name)

def test_real_upsert_and_snapshot(test_database,merged_frame):
    run="integration_"+uuid.uuid4().hex
    first=storage.load_frame(merged_frame,run,{"mode":"synthetic integration fixture"},{})
    second=storage.load_frame(merged_frame,run+"_rerun",{"mode":"synthetic integration fixture"},{})
    frame,provenance=storage.read_snapshot(second["run_id"],second["dataset_hash"])
    assert first["rows"]==second["rows"]==first["distinct_dates"]==second["distinct_dates"]==731
    assert dataset_hash(frame)==first["dataset_hash"]==provenance["dataset_hash"]

def test_real_transaction_rollback(test_database,merged_frame,monkeypatch):
    run="rollback_"+uuid.uuid4().hex
    baseline=storage.load_frame(merged_frame,run,{"mode":"synthetic integration fixture"},{})
    changed=merged_frame.copy(); changed["cnt"]+=10
    failed_run=run+"_must_rollback"
    original_read=storage.read_frame
    def force_database_error(connection):
        connection.execute("SELECT 1/0")
    with monkeypatch.context() as context:
        context.setattr(storage,"read_frame",force_database_error)
        with pytest.raises(psycopg.errors.DivisionByZero):
            storage.load_frame(changed,failed_run,{"mode":"injected SQL failure"},{})
    with storage.app_connect() as connection:
        assert dataset_hash(original_read(connection))==baseline["dataset_hash"]
        assert connection.execute("SELECT count(*) FROM bike_analytics.pipeline_runs WHERE run_id=%s",(failed_run,)).fetchone()[0]==0
