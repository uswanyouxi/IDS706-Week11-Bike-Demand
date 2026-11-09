from unittest.mock import MagicMock,patch
import pytest
pytest.importorskip("langgraph")
from bike_demand_ml.db import load_postgres_snapshot
from bike_demand.contracts import dataset_hash

def test_loader_is_readonly_postgres_not_file(synthetic_frame):
    digest=dataset_hash(synthetic_frame)
    connection=MagicMock()
    connection.__enter__.return_value=connection
    result=lambda **kwargs:MagicMock(**kwargs)
    connection.execute.side_effect=[
        result(),result(fetchone=lambda:("on",)),
        result(fetchall=lambda:[(digest,"test_parent")]),
        result(fetchone=lambda:(731,digest,{"scope":"unit fixture"})),
        result(fetchone=lambda:("bike_demand",))]
    with patch("bike_demand_ml.db.app_connect",return_value=connection) as connect,\
         patch("bike_demand_ml.db.read_frame",return_value=synthetic_frame),\
         patch("pandas.read_csv",side_effect=AssertionError("File input forbidden")) as files:
        frame,provenance=load_postgres_snapshot()
    connect.assert_called_once()
    files.assert_not_called()
    assert provenance["origin"]=="application_postgresql" and provenance["transaction_read_only"]=="on"
    assert provenance["dataset_hash"]==digest and len(frame)==731
    sql=[c.args[0] for c in connection.execute.call_args_list]
    assert sql[0]=="SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
    assert not any(s.lstrip().upper().startswith(("INSERT","UPDATE","DELETE","CREATE")) for s in sql)

def test_database_failure_has_no_raw_cache_fallback():
    with patch("bike_demand_ml.db.app_connect",side_effect=ConnectionError("database unavailable")),\
         patch("pandas.read_csv") as files:
        with pytest.raises(ConnectionError):load_postgres_snapshot()
    files.assert_not_called()
