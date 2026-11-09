"""Counterexamples prove the independent audit can reject bad reports/artifacts."""
import copy,csv,json
import pytest
pytest.importorskip("langgraph")
from bike_demand_bonus.audit import audit_saved_run
from bike_demand_bonus.runner import execute,fault_trainer

@pytest.fixture
def saved(tmp_path,snapshot):
    report=execute("audited_fixture",tmp_path,loader=snapshot)
    folder=tmp_path/"audited_fixture"
    assert audit_saved_run(folder,"normal","adaptive",require_database=False)["passed"]
    return folder,report

def write_report(folder,report):
    (folder/"report.json").write_text(json.dumps(report),encoding="utf-8")

@pytest.mark.parametrize("mutation",[
    "empty_routes","empty_features","negative_counters","wrong_best_spec","false_quality",
    "wrong_split_counts","wrong_baseline","forged_trial","fake_agent_timing","fake_status"])
def test_report_mutations_are_rejected(saved,mutation):
    folder,report=saved;report=copy.deepcopy(report)
    if mutation=="empty_routes":report["routes"]=[]
    elif mutation=="empty_features":report["features"]=[]
    elif mutation=="negative_counters":report["attempt"]=-1
    elif mutation=="wrong_best_spec":report["best"]["spec"]={"name":"unsupported"}
    elif mutation=="false_quality":report["quality"]["rows"]=1
    elif mutation=="wrong_split_counts":report["diagnostics"]["test_rows"]=1
    elif mutation=="wrong_baseline":report["baseline"]["rmse"]*=2
    elif mutation=="forged_trial":report["trials"][0]["gap"]=999
    elif mutation=="fake_agent_timing":report["agent_metrics"]["training"]["seconds"]+=10
    elif mutation=="fake_status":report["status"]="failed"
    write_report(folder,report)
    assert not audit_saved_run(folder,"normal","adaptive",require_database=False)["passed"]

def test_predictions_are_independently_scored(saved):
    folder,_=saved
    path=folder/"test_predictions.csv"
    with path.open(newline="") as handle:
        reader=csv.DictReader(handle);columns=reader.fieldnames;rows=list(reader)
    rows[0]["prediction"]=str(float(rows[0]["prediction"])+100)
    with path.open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    grade=audit_saved_run(folder,"normal","adaptive",require_database=False)
    assert not grade["assertions"]["recomputed_selected_metrics"]

def test_missing_events_cannot_pass_vacuously(saved):
    folder,_=saved;(folder/"events.jsonl").write_text("")
    grade=audit_saved_run(folder,"normal","adaptive",require_database=False)
    assert not grade["passed"] and not grade["assertions"]["nonempty_trace"]

@pytest.mark.parametrize("policy",["adaptive","fixed_port","simple_port"])
def test_exhaustion_requires_actual_attempts(tmp_path,snapshot,policy):
    report=execute("exhaust_"+policy,tmp_path,loader=snapshot,policy=policy,
        scenario="exhaust_training",trainer=fault_trainer("exhaust_training"))
    folder=tmp_path/("exhaust_"+policy)
    assert audit_saved_run(folder,"exhaust_training",policy,require_database=False)["passed"]
    report["attempt"]=0;write_report(folder,report)
    grade=audit_saved_run(folder,"exhaust_training",policy,require_database=False)
    assert not grade["assertions"]["exact_scenario_attempt_count"]

def test_audit_never_fits_models(saved,monkeypatch):
    import bike_demand_bonus.models
    def forbidden(*args,**kwargs):raise AssertionError("Audit must not train")
    monkeypatch.setattr(bike_demand_bonus.models,"make_candidate",forbidden)
    assert audit_saved_run(saved[0],"normal","adaptive",require_database=False)["passed"]


def test_suite_grading_includes_independent_artifact_gate(tmp_path,snapshot,monkeypatch):
    import bike_demand_bonus.evaluation as evaluation
    original=evaluation.execute
    def tampered(*args,**kwargs):
        report=original(*args,**kwargs)
        if report["scenario"]=="normal" and report["policy"]=="adaptive":
            (tmp_path/"runs"/report["run_id"]/"events.jsonl").write_text("")
        return report
    monkeypatch.setattr(evaluation,"execute",tampered)
    result=evaluation.evaluate_suite("counterexample_suite",tmp_path,loader=snapshot)
    assert result["failed"]==1 and result["passed"]==26
