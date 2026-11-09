"""Immutable bonus runs with real graph events, metrics and process measurements."""
import json,os,re,time
try:import resource
except ImportError:resource=None
from pathlib import Path
from bike_demand.io_utils import write_json
from bike_demand_ml.db import load_postgres_snapshot
from bike_demand_ml.visuals import graph_dot
from bike_demand_bonus.graph import build_graph
from bike_demand_bonus.agents import TrainingInterrupted
from bike_demand_bonus.models import make_candidate

def execute(run_id,root,*,loader=load_postgres_snapshot,policy="adaptive",scenario="normal",trainer=None,
            max_attempts=3,max_loads=2,max_recoveries=2):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}",run_id):raise ValueError("Unsafe run ID")
    if policy not in {"adaptive","fixed_port","simple_port"}:raise ValueError("Unknown policy")
    if not 1<=max_attempts<=3 or not 1<=max_loads<=2 or not 0<=max_recoveries<=2:
        raise ValueError("Finite budgets exceeded")
    folder=Path(root)/run_id;folder.mkdir(parents=True,exist_ok=False)
    graph=build_graph(folder,loader,trainer)
    topology=graph.get_graph().to_json()
    write_json(folder/"graph.json",topology)
    (folder/"graph.mmd").write_text(graph.get_graph().draw_mermaid(),encoding="utf-8")
    initial={"run_id":run_id,"output_dir":str(folder),"policy":policy,"scenario":scenario,
        "attempt":0,"max_attempts":max_attempts,"load_attempts":0,"max_loads":max_loads,
        "recoveries":0,"max_recoveries":max_recoveries,"trials":[],"routes":[],
        "tried":[],"refined":False,"issue":None,"status":"running","test_stage_count":0}
    started=time.perf_counter();cpu=time.process_time()
    final=None
    try:
        for state in graph.stream(initial,stream_mode="values",config={"recursion_limit":100}):final=state
        if not (folder/"report.json").exists():raise RuntimeError("Graph did not report")
        if final.get("status") not in {"success","failed"}:raise RuntimeError("Graph did not terminate")
    except Exception as error:
        write_json(folder/"report.json",{"run_id":run_id,"policy":policy,"scenario":scenario,
            "status":"failed","metrics_claimed":False,"issue":{"stage":"graph_runtime","type":type(error).__name__}})
    result=json.loads((folder/"report.json").read_text())
    result.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
        worker_rss_high_water_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource else None,
        memory_scope="Linux worker process lifetime high-water RSS, not isolated per-run peak")
    events=[json.loads(s) for s in (folder/"events.jsonl").read_text().splitlines()]
    result["node_operations"]=sum(e["kind"]=="node_completed" for e in events)
    agents={}
    for event in events:
        if event["kind"]!="node_completed":continue
        record=agents.setdefault(event["node"],{"calls":0,"seconds":0.0,"errors":0})
        record["calls"]+=1;record["seconds"]+=event.get("duration_seconds") or 0.0
        record["errors"]+=int((event.get("issue") or {}).get("stage")==event["node"])
    result["agent_metrics"]=agents
    result["graph_source"]="compiled StateGraph.get_graph().to_json()"
    write_json(folder/"report.json",result)
    (folder/"graph.dot").write_text(graph_dot(topology,events),encoding="utf-8")
    return result

def fault_trainer(scenario):
    def train(state):
        if scenario=="transient_training" and state["attempt"]==1:
            raise TrainingInterrupted("isolated fault fixture")
        if scenario=="exhaust_training":raise TrainingInterrupted("isolated fault fixture")
        model=make_candidate(state["spec"],state["features"])
        part=state["splits"]["train"]
        model.fit(state["X"].iloc[part],state["y"].iloc[part])
        return model
    return train
