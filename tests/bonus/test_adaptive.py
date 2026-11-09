import copy,json
from pathlib import Path
import pytest
pytest.importorskip("langgraph")
from bike_demand_bonus import agents
from bike_demand_bonus.graph import build_graph
from bike_demand_bonus.runner import execute,fault_trainer
from bike_demand_bonus.evaluation import evaluate_suite,expected_status
from bike_demand_bonus.models import make_candidate
from bike_demand_ml.models import FORBIDDEN,NUMERICAL

def control(**patch):
    state={"policy":"adaptive","scenario":"normal","phase":"evaluated",
        "attempt":1,"max_attempts":3,"load_attempts":1,"max_loads":2,
        "recoveries":0,"max_recoveries":2,"issue":None,"refined":False,
        "trials":[{"gap":1.2}],"best":{"validation":{"rmse":400}},
        "baseline":{"rmse":600},"diagnostics":{"collinear_weather":["temperature_2m_max"]}}
    state.update(patch);return state

def test_graph_has_distinct_roles_and_conditional_edges(tmp_path,snapshot):
    graph=build_graph(tmp_path,snapshot).get_graph().to_json()
    names={n["id"] for n in graph["nodes"]}
    assert {"data_quality","feature_analysis","feature_refinement","model_selection",
            "training","evaluation","coordinator","recovery","reporting"}<=names
    assert any(e["source"]=="coordinator" and e["target"]=="feature_refinement" for e in graph["edges"])

def test_success_route():
    assert agents.decision(control())==("final_test","validation_target_met")

def test_results_can_select_refinement():
    state=control(trials=[{"gap":2.1}])
    assert agents.decision(state)[0]=="feature_refinement"
    state["refined"]=True
    assert agents.decision(state)[0]=="model_selection"

def test_weak_performance_selects_another_model():
    assert agents.decision(control(best={"validation":{"rmse":700}}))[0]=="model_selection"

def test_maximum_attempts_terminate():
    assert agents.decision(control(attempt=3,best={"validation":{"rmse":700}}))[0]=="final_test"

@pytest.mark.parametrize("stage",["training","data_loader"])
def test_recoverable_error_routes(stage):
    state=control(issue={"stage":stage,"type":"TrainingInterrupted","recoverable":True})
    assert agents.decision(state)[0]=="recovery"

@pytest.mark.parametrize("patch",[{"recoveries":2},{"load_attempts":2}])
def test_recovery_budget_exhaustion(patch):
    state=control(issue={"stage":"data_loader","type":"OperationalError","recoverable":True},**patch)
    assert agents.decision(state)[0]=="failure_report"

def test_unrecoverable_never_retries():
    state=control(issue={"stage":"training","type":"ValueError","recoverable":False})
    assert agents.decision(state)[0]=="failure_report"

def test_final_test_cannot_change_selection():
    a=control();b=copy.deepcopy(a);b["final_metrics"]={"selected":{"rmse":9999999}}
    assert agents.decision(a)==agents.decision(b)

def test_model_selection_depends_on_training_diagnostics():
    base={"policy":"adaptive","scenario":"normal","attempt":0,"trials":[],"features":["weekday"],
          "diagnostics":{"maximum_target_correlation":0.8},"tried":[]}
    assert agents.select(base)["spec"]["name"]=="ridge"
    base["diagnostics"]["maximum_target_correlation"]=0.1
    assert agents.select(base)["spec"]["name"]=="forest"

def test_data_quality_and_feature_transformer_fit(frame,snapshot):
    state={"frame":frame,"provenance":snapshot()[1]}
    assert agents.quality(state)["quality"]["contract_valid"]
    prepared=agents.features(state)
    assert not FORBIDDEN.intersection(prepared["features"])
    assert [len(prepared["splits"][p]) for p in ["train","validation","test"]]==[365,182,184]
    model=make_candidate({"name":"ridge","alpha":10},prepared["features"])
    train=prepared["splits"]["train"];model.fit(prepared["X"].iloc[train],prepared["y"].iloc[train])
    scaler=model.named_steps["features"].named_transformers_["numeric"]
    assert scaler.mean_[NUMERICAL.index("elapsed_day")]==182

def test_actual_graph_success_and_artifacts(tmp_path,snapshot):
    report=execute("fixture_success",tmp_path,loader=snapshot)
    assert report["status"]=="success" and report["test_stage_count"]==1
    folder=tmp_path/"fixture_success"
    for name in ["graph.json","graph.mmd","graph.dot","events.jsonl","report.json",
                 "database_snapshot.csv","test_predictions.csv","progress.json"]:
        assert (folder/name).exists()
    events=[json.loads(s) for s in (folder/"events.jsonl").read_text().splitlines()]
    assert sum(e["node"]=="final_test" and e["kind"]=="node_started" for e in events)==1
    assert all(r["reason"] for r in report["routes"])

def test_fixed_port_retry_does_not_change_model(tmp_path,snapshot):
    report=execute("fixed_retry",tmp_path,policy="fixed_port",scenario="transient_training",
        loader=snapshot,trainer=fault_trainer("transient_training"))
    assert report["status"]=="success" and report["recoveries"]==1
    assert all(t["spec"]=={"name":"ridge","alpha":10.0} for t in report["trials"])

def test_failure_secret_not_recorded(tmp_path):
    def failure():raise PermissionError("password=never-record-this")
    report=execute("failure",tmp_path,loader=failure)
    assert report["status"]=="failed" and report["metrics_claimed"] is False
    assert "never-record-this" not in (tmp_path/"failure/events.jsonl").read_text()

@pytest.mark.parametrize("run_id",["../escape","/absolute",""])
def test_paths_are_safe(tmp_path,snapshot,run_id):
    with pytest.raises(ValueError):execute(run_id,tmp_path,loader=snapshot)

def test_evidence_never_overwritten(tmp_path,snapshot):
    (tmp_path/"existing").mkdir()
    with pytest.raises(FileExistsError):execute("existing",tmp_path,loader=snapshot)

def test_deterministic_metrics(tmp_path,snapshot):
    a=execute("repeat_a",tmp_path,loader=snapshot)
    b=execute("repeat_b",tmp_path,loader=snapshot)
    assert a["final_metrics"]==b["final_metrics"] and a["best"]==b["best"]

def test_full_explicit_evaluation_suite_on_labeled_fixture(tmp_path,snapshot):
    result=evaluate_suite("unit_suite",tmp_path,loader=snapshot)
    assert result["executions"]==27 and result["failed"]==0
    assert result["passed"]==27
    rows=json.loads((tmp_path/"evaluations/unit_suite/results.json").read_text())
    assert all(all(k in row for k in ["input","expected","criteria","threshold","observed_status","passed"]) for row in rows)

def test_suite_path_safety(tmp_path,snapshot):
    with pytest.raises(ValueError):evaluate_suite("../escape",tmp_path,loader=snapshot)


def test_oracle_rejects_wrong_recovery_destination(tmp_path,snapshot):
    from bike_demand_bonus.evaluation import loader_for,assess
    frame,provenance=snapshot()
    report=execute("oracle_recovery",tmp_path,loader=loader_for(frame,provenance,"transient_database"),
                   scenario="transient_database")
    assert assess(report,"transient_database","adaptive")["passed"]
    wrong=copy.deepcopy(report)
    next(r for r in wrong["routes"] if r["from_phase"]=="recovered")["destination"]="model_selection"
    assert not assess(wrong,"transient_database","adaptive")["assertions"]["legal_routes"]


def test_oracle_rejects_nonbest_validation_selection(tmp_path,snapshot):
    from bike_demand_bonus.evaluation import assess
    report=execute("oracle_selection",tmp_path,loader=snapshot)
    wrong=copy.deepcopy(report)
    wrong["best"]["validation"]["rmse"]+=100
    assert not assess(wrong,"normal","adaptive")["assertions"]["validation_selection"]
