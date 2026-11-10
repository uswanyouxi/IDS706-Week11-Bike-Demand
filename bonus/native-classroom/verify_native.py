"""Validate native execution evidence without refitting either classifier."""
import csv,hashlib,json,math
from pathlib import Path
TASKS={"validate_customers","validate_transactions","merge_csvs","make_subset","profile_light","train_baseline","publish_merged"}
def load(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_native(artifacts):
    root=Path(artifacts)
    prep=load(root/"native_prep_01/report.json")
    completed=[p.parent for p in root.glob("native_simple_*/report.json") if load(p).get("status")=="success"]
    assert len(completed)==1,"Require exactly one completed native graph experiment"
    loop_folder=completed[0];loop=load(loop_folder/"report.json")
    states=load(root/"native_prep_01/task-states.json");xcom=load(root/"native_prep_01/xcom.json")
    topology=load(loop_folder/"graph.json")
    events=[json.loads(line) for line in (loop_folder/"events.jsonl").read_text().splitlines()]
    assert prep["actual_airflow_dag_executed"] and prep["all_seven_tasks_success"]
    assert prep["run_id"]=="native_prep_01" and prep["state"]=="success"
    assert len(states)==7 and {t["task_id"] for t in states}==TASKS and all(t["state"]=="success" for t in states)
    assert prep["baseline_validation"]==xcom["train_baseline"]
    assert 0<=prep["baseline_validation"]["f1"]<=1
    assert (prep["baseline_validation"]["n_train"],prep["baseline_validation"]["n_val"])==(1600,400)
    assert prep["heldout_metrics"] is None
    subset=root/"native_prep_01/subset.csv";published=root/"native_prep_01/published.csv"
    assert subset.read_bytes()==published.read_bytes()
    assert digest(published)==prep["outputs"]["published"]["sha256"]==loop["dataset_sha256"]
    with subset.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    assert len(rows)==2000 and set(r["is_fraud"] for r in rows)=={"0","1"}
    assert loop["status"]=="success" and loop["no_key_heuristic_mode"]
    assert not loop["native_source_modified"] and not prep["native_source_modified"]
    assert 1<=loop["cycles"]<=3
    steps=loop["steps"]
    engineer=[s for s in steps if s["node"]=="ml_engineer"]
    assert len(engineer)==loop["cycles"]
    assert sum(s["node"]=="holdout_eval" for s in steps)==1 and steps[-1]["node"]=="holdout_eval"
    assert not any(s.get("used_llm") for s in steps)
    assert sum(s["node"]=="memory_writer" for s in steps)==loop["cycles"]-1
    assert sum(s["node"]=="context_builder" for s in steps)==loop["cycles"]-1
    valid=[s["validation_metrics"]["f1"] for s in engineer if s.get("status")=="succeeded"]
    assert valid and math.isclose(max(valid),loop["best_val_f1"],rel_tol=1e-12,abs_tol=1e-12)
    assert loop["holdout_metrics"]["n_holdout"]==400
    assert all(math.isfinite(loop["holdout_metrics"][k]) and 0<=loop["holdout_metrics"][k]<=1 for k in ["f1","accuracy"])
    assert sum(e["type"]=="run_completed" for e in events)==1 and not any(e["type"]=="error" for e in events)
    graph_nodes={n["id"] for n in topology["nodes"]}
    assert {"data_scientist","hypothesis_generator","ml_engineer","judge","memory_writer","context_builder","holdout_eval"}<=graph_nodes
    return {"status":"verified","native_airflow_run":prep["run_id"],"native_airflow_task_successes":7,
        "native_airflow_validation":prep["baseline_validation"],"native_airflow_holdout":None,
        "native_langgraph_run":loop["run_id"],"native_langgraph_cycles":loop["cycles"],
        "native_langgraph_validation_f1":loop["best_val_f1"],"native_langgraph_holdout":loop["holdout_metrics"],
        "same_published_fraud_sample":True,"sample_sha256":digest(published),"no_paid_llm":True,
        "scores_recomputed_by_verifier":False,"scope":"Actual native classifier outputs; consistency checks, not independent classifier refits"}
if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("artifacts",type=Path)
    args=parser.parse_args();print(json.dumps(verify_native(args.artifacts),indent=2))
