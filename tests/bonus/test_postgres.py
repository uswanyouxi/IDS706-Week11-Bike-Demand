"""Read-only integration; never writes, drops, creates or injects faults into SQL."""
import os
import pytest
pytest.importorskip("langgraph")

@pytest.mark.integration
def test_real_postgres_snapshot_is_unchanged():
    if os.environ.get("BONUS_DB_INTEGRATION")!="1":pytest.skip("Explicit real read-only database check not enabled")
    from bike_demand_ml.db import load_postgres_snapshot
    first,meta=load_postgres_snapshot();second,again=load_postgres_snapshot()
    assert len(first)==len(second)==731
    assert meta["dataset_hash"]==again["dataset_hash"]
    assert meta["transaction_read_only"]==again["transaction_read_only"]=="on"
    assert int(first.cnt.sum())==int(second.cnt.sum())==3292679
