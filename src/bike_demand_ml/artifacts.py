"""Run-specific observable state; no estimator/DataFrame/credentials in JSON events."""
from datetime import datetime,timezone
import json
from pathlib import Path
import threading
from bike_demand.io_utils import write_json

def now():
    return datetime.now(timezone.utc).isoformat()

class EventLog:
    def __init__(self,folder):
        self.folder=Path(folder)
        self.path=self.folder/"events.jsonl"
        self.seq=0
        self.previous_node=None

    def emit(self,kind,node,state=None):
        state=state or {}
        self.seq+=1
        payload={"sequence":self.seq,"at_utc":now(),"kind":kind,"node":node,
                 "from_node":self.previous_node if kind=="node_started" else None,
                 "attempt":state.get("attempt",0),"decision":state.get("decision"),
                 "stop_reason":state.get("stop_reason"),"status":state.get("status"),
                 "error":state.get("error"),"candidate":state.get("candidate_spec"),
                 "trials":state.get("trials",[]),"routes":state.get("routes",[])}
        with self.path.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(payload,allow_nan=False)+"\n")
            handle.flush()
        if kind=="node_completed":
            self.previous_node=node
        write_json(self.folder/"progress.json",payload)

def safe_projection(state):
    keys=["run_id","dataset_hash","provenance","feature_names","attempt","min_attempts",
          "max_attempts","target_improvement","baseline_metrics","best_spec","best_validation_rmse","trials",
          "routes","decision","stop_reason","error","final_metrics","test_stage_count",
          "status","artifacts"]
    return {k:state[k] for k in keys if k in state}
