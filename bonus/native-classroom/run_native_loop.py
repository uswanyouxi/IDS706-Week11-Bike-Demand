"""Observe the completed original classroom graph on the actual DAG-published CSV."""
import hashlib,importlib.util,json,os,re,resource,sys,time
from datetime import datetime,timezone
from importlib.metadata import version
from pathlib import Path
for key in ["OPENROUTER_API_KEY","CURSOR_API_KEY"]:
    assert not os.environ.get(key),"Native no-key run must not receive external credentials"
    os.environ.pop(key,None)
ROOT=Path("/evidence/native_classroom_01")
DATA=Path("/repo/datasets/airflow/merged_latest.csv")
RUN_ID=os.environ.get("NATIVE_LOOP_RUN_ID","native_simple_01")
assert re.fullmatch(r"native_simple_[A-Za-z0-9_.-]{1,48}",RUN_ID),"Invalid native run ID"
OUT=ROOT/RUN_ID
def dump(name,value):
    with (OUT/name).open("x",encoding="utf-8") as f:json.dump(value,f,indent=2,allow_nan=False);f.write("\n")
def main():
    expected=json.loads((ROOT/"native_prep_01/report.json").read_text())
    data_hash=hashlib.sha256(DATA.read_bytes()).hexdigest()
    assert data_hash==expected["outputs"]["published"]["sha256"]
    pins=json.loads(Path("/harness/source-pins.json").read_text())
    for name in ["solution/langgraph/graph.py","loop_runtime.py"]:
        assert hashlib.sha256((Path("/reference")/name).read_bytes()).hexdigest()==pins["source_files"][name]["sha256"]
    OUT.mkdir(exist_ok=False)
    sys.path.insert(0,"/reference")
    spec=importlib.util.spec_from_file_location("native_completed_graph","/reference/solution/langgraph/graph.py")
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    import loop_runtime
    assert not loop_runtime.llm_configured()
    graph=module.build_graph();dump("graph.json",graph.get_graph().to_json())
    (OUT/"graph.mmd").write_text(graph.get_graph().draw_mermaid(),encoding="utf-8")
    parameters={"dataset_path":str(DATA),"target_column":"is_fraud","target_score":0.8,"max_cycles":3,"seed":42,"holdout_frac":0.2}
    dump("parameters.json",parameters)
    started=time.perf_counter();cpu=time.process_time();final=None
    with (OUT/"events.jsonl").open("x",encoding="utf-8") as f:
        for event in module.stream_solution_loop(**parameters):
            record={"observed_at_utc":datetime.now(timezone.utc).isoformat(),**event}
            f.write(json.dumps(record,allow_nan=False)+"\n");f.flush()
            if event["type"]=="error":raise RuntimeError(event.get("message"))
            if event["type"]=="run_completed":final=event["result"]
    assert final and 1<=final["cycles"]<=3
    steps=final["steps"]
    assert sum(s.get("node")=="holdout_eval" for s in steps)==1
    assert sum(s.get("node")=="ml_engineer" for s in steps)==final["cycles"]
    assert not any(s.get("used_llm") for s in steps)
    assert 0<=final["best_val_f1"]<=1
    assert final["holdout_metrics"]["n_holdout"]==400
    assert all(0<=final["holdout_metrics"][k]<=1 for k in ["f1","accuracy"])
    final.update(run_id=RUN_ID,status="success",source_commit=pins["commit"],native_source_modified=False,
        dataset_sha256=data_hash,dataset_origin="Actual solution_baseline_prep DAG publication",
        no_key_heuristic_mode=True,target_met=final["best_val_f1"]>=0.8,
        wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
        worker_rss_high_water_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        versions={p:version(p) for p in ["langgraph","scikit-learn","pandas","numpy","scipy"]},
        event_timing_note="Original stream emits node_started after an update; observation times are not independent per-agent execution timers.",
        scope="Native fraud classification; 60/20/20 selection split, then 80/20 final refit/holdout")
    dump("report.json",final)
    print(json.dumps({k:final[k] for k in ["run_id","status","cycles","best_val_f1","holdout_metrics","target_met","no_key_heuristic_mode","wall_seconds"]},indent=2))
if __name__=="__main__":
    try:main()
    except Exception as error:
        if OUT.exists() and not (OUT/"error.json").exists():dump("error.json",{"status":"failed","type":type(error).__name__,"message":str(error),"metrics_claimed":False})
        raise
