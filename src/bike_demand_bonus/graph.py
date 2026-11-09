"""Original compiled adaptive specialist graph; existing Part 2 graph is never edited."""
from pathlib import Path
import json,time
import psycopg
from langgraph.graph import StateGraph,START,END
from bike_demand.io_utils import write_json
from bike_demand_bonus.state import BonusState
from bike_demand_bonus import agents

class EventLog:
    def __init__(self,folder):self.folder=Path(folder);self.previous=None;self.sequence=0
    def emit(self,kind,node,state):
        self.sequence+=1
        payload={k:state.get(k) for k in ["attempt","max_attempts","recoveries","load_attempts",
            "phase","issue","next_node","reason","spec","quality","diagnostics","trials",
            "routes","final_metrics","test_stage_count","status"]}
        payload.update(sequence=self.sequence,kind=kind,node=node,from_node=self.previous if kind=="node_started" else None,
                       at_unix=time.time(),duration_seconds=state.get("_node_duration_seconds"))
        with (self.folder/"events.jsonl").open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(payload,allow_nan=False)+"\n")
        write_json(self.folder/"progress.json",payload)
        if kind=="node_completed":self.previous=node

def projection(state):
    return {key:state.get(key) for key in ["run_id","policy","scenario","dataset_hash",
        "provenance","quality","features","diagnostics","refined","attempt","max_attempts",
        "load_attempts","max_loads","recoveries","max_recoveries","issue","tried","baseline",
        "best","trials","routes","reason","final_metrics","test_stage_count","status"]}

def build_graph(folder,loader,trainer=None):
    log=EventLog(folder)
    def load(state):
        frame,provenance=loader()
        return {"frame":frame,"provenance":provenance,"load_attempts":state["load_attempts"]+1,"phase":"loaded"}
    def report(state):
        state["frame"].to_csv(Path(folder)/"database_snapshot.csv",index=False)
        state["predictions"].to_csv(Path(folder)/"test_predictions.csv",index=False)
        body=projection(state);body.update(status="success",framing="Retrospective observed-weather backtest",
            final_refit_rows=547,heldout_rows=184,negative_predictions=int((state["predictions"].prediction<0).sum()))
        write_json(Path(folder)/"report.json",body)
        return {"status":"success"}
    def failure(state):
        body=projection(state);body.update(status="failed",metrics_claimed=False,final_metrics=None)
        write_json(Path(folder)/"report.json",body)
        return {"status":"failed"}
    operations={"data_loader":load,"data_quality":agents.quality,
        "feature_analysis":agents.features,"feature_refinement":agents.refine,
        "model_selection":agents.select,"training":lambda s:agents.train(s,trainer),
        "evaluation":agents.evaluate,"coordinator":agents.coordinate,
        "recovery":agents.recover,"final_test":agents.final_test,"reporting":report,"failure_report":failure}
    graph=StateGraph(BonusState)
    def wrap(name,function):
        def execute(state):
            log.emit("node_started",name,state)
            started=time.perf_counter()
            try:patch=function(state)
            except Exception as error:
                recoverable=isinstance(error,(psycopg.OperationalError,TimeoutError,agents.TrainingInterrupted))
                patch={"issue":{"stage":name,"type":type(error).__name__,"recoverable":recoverable}}
                if name=="data_loader":patch["load_attempts"]=state["load_attempts"]+1
                if name=="training":
                    patch["trials"]=[{"attempt":state["attempt"],"spec":state["spec"],
                        "features":state["features"],"status":"failed","error_type":type(error).__name__}]
            merged=dict(state)
            for key,value in patch.items():
                merged[key]=state.get(key,[])+value if key in {"routes","trials"} else value
            merged["_node_duration_seconds"]=time.perf_counter()-started
            log.emit("node_completed",name,merged)
            return patch
        return execute
    for name,function in operations.items():graph.add_node(name,wrap(name,function))
    graph.add_edge(START,"data_loader")
    destinations={name:name for name in operations if name!="coordinator"}
    graph.add_conditional_edges("coordinator",lambda s:s["next_node"],destinations)
    for name in operations:
        if name in {"reporting","failure_report"}:graph.add_edge(name,END)
        elif name!="coordinator":graph.add_edge(name,"coordinator")
    return graph.compile()
