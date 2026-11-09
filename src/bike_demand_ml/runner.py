"""Execute the real graph once, stream events, preserve every run's artifacts."""
import importlib.metadata
import json
import os
from pathlib import Path
import re
from bike_demand.io_utils import write_json
from bike_demand_ml.artifacts import EventLog
from bike_demand_ml.db import load_postgres_snapshot
from bike_demand_ml.graph import build_graph
from bike_demand_ml.visuals import graph_dot,save_graph_png

def execute_run(run_id,output_root,*,min_attempts=2,max_attempts=2,target_improvement=0.05,
                loader=load_postgres_snapshot):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}",run_id):
        raise ValueError("Run ID must be a simple safe identifier")
    if not 1<=min_attempts<=max_attempts<=2 or not 0<=target_improvement<1:
        raise ValueError("Require 1 <= min_attempts <= max_attempts <= 2 and 0 <= improvement < 1")
    folder=Path(output_root)/run_id
    folder.mkdir(parents=True,exist_ok=False)
    events=EventLog(folder)
    compiled=build_graph(events,loader=loader)
    topology=compiled.get_graph().to_json()
    write_json(folder/"graph.json",topology)
    (folder/"graph.mmd").write_text(compiled.get_graph().draw_mermaid(),encoding="utf-8")
    initial={"run_id":run_id,"output_dir":str(folder),"min_attempts":min_attempts,
        "max_attempts":max_attempts,"target_improvement":target_improvement,"attempt":0,
        "trials":[],"routes":[],"test_stage_count":0,"error":None,"status":"starting"}
    final=initial
    try:
        for value in compiled.stream(initial,config={"recursion_limit":40},stream_mode="values"):
            final=value
    except Exception as error:
        write_json(folder/"report.json",{"run_id":run_id,"status":"failed",
            "error":f"graph_runtime: {type(error).__name__}","metrics_claimed":False})
        final={"status":"failed"}
    recorded=[json.loads(line) for line in (folder/"events.jsonl").read_text(encoding="utf-8").splitlines()]
    (folder/"graph.dot").write_text(graph_dot(topology,recorded),encoding="utf-8")
    save_graph_png(topology,recorded,folder/"agent_graph.png")
    report=json.loads((folder/"report.json").read_text(encoding="utf-8"))
    report["versions"]={p:importlib.metadata.version(p) for p in
        ["langgraph","scikit-learn","pandas","numpy","psycopg","streamlit"]}
    report["graph_source"]="compiled StateGraph.get_graph().to_json()"
    report["events_recorded"]=len(recorded)
    write_json(folder/"report.json",report)
    return report
