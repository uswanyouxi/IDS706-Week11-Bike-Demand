import json
from pathlib import Path
import pytest
pytest.importorskip("langgraph")
from bike_demand_ml.runner import execute_run

def test_original_graph_bounded_loop_and_artifacts(tmp_path,synthetic_loader):
    report=execute_run("synthetic_success",tmp_path,loader=synthetic_loader)
    folder=tmp_path/"synthetic_success"
    assert report["status"]=="success"
    assert report["provenance"]["origin"]=="synthetic_unit_fixture"
    assert report["attempt"]==2 and len(report["trials"])==2
    assert [r["decision"] for r in report["routes"]]==["retry","finish"]
    assert report["test_stage_count"]==1
    assert set(report["final_metrics"])=={"dummy","selected"}
    assert all(k in report["final_metrics"]["selected"] for k in ["mae","rmse","r2"])
    for name in ["report.json","trials.json","events.jsonl","graph.json","graph.mmd","graph.dot",
                 "agent_graph.png","test_predictions.png","validation_rmse.png","database_snapshot.csv",
                 "selected_model.joblib","test_predictions.csv","splits.json","features.json","provenance.json"]:
        assert (folder/name).is_file(),name
    graph=json.loads((folder/"graph.json").read_text())
    assert any(e["source"]=="conditional_router" and e["target"]=="choose_candidate" for e in graph["edges"])
    events=[json.loads(s) for s in (folder/"events.jsonl").read_text().splitlines()]
    assert sum(e["node"]=="final_test_once" and e["kind"]=="node_started" for e in events)==1
    assert sum(e["node"]=="train_model" and e["kind"]=="node_started" for e in events)==2

def test_early_success_graph_route(tmp_path,synthetic_loader):
    report=execute_run("synthetic_early",tmp_path,loader=synthetic_loader,min_attempts=1,max_attempts=2)
    assert report["status"]=="success"
    assert report["attempt"]==1
    assert report["routes"][0]["decision"]=="finish"

def test_failure_graph_reports_no_metrics(tmp_path):
    def broken():raise ConnectionError("password=do-not-log")
    report=execute_run("synthetic_failure",tmp_path,loader=broken)
    assert report["status"]=="failed" and report["metrics_claimed"] is False
    assert "final_metrics" not in report
    text=(tmp_path/"synthetic_failure"/"events.jsonl").read_text()
    assert "do-not-log" not in text
    assert "failure_report" in text and "ConnectionError" in text

def test_never_overwrite_evidence(tmp_path,synthetic_loader):
    (tmp_path/"existing").mkdir()
    with pytest.raises(FileExistsError):
        execute_run("existing",tmp_path,loader=synthetic_loader)

@pytest.mark.parametrize("minimum,maximum",[(1,3),(2,1),(0,2)])
def test_attempt_budget_constraints(tmp_path,synthetic_loader,minimum,maximum):
    with pytest.raises(ValueError):
        execute_run("invalid",tmp_path,loader=synthetic_loader,min_attempts=minimum,max_attempts=maximum)

def test_run_path_cannot_escape(tmp_path,synthetic_loader):
    with pytest.raises(ValueError):
        execute_run("../escape",tmp_path,loader=synthetic_loader)

def test_seeded_results_repeat(tmp_path,synthetic_loader):
    a=execute_run("repeat_a",tmp_path,loader=synthetic_loader,min_attempts=1)
    b=execute_run("repeat_b",tmp_path,loader=synthetic_loader,min_attempts=1)
    assert a["final_metrics"]==b["final_metrics"]
    assert a["best_spec"]==b["best_spec"]
