"""An original executable LangGraph with explicit error and bounded-loop edges."""
from langgraph.graph import StateGraph, START, END
from bike_demand_ml.state import MLState
from bike_demand_ml import nodes
from bike_demand_ml.db import load_postgres_snapshot

def build_graph(event_log,loader=load_postgres_snapshot):
    def wrapped(name,function):
        def execute(state):
            event_log.emit("node_started",name,state)
            try:
                update=function(state)
            except Exception as error:
                update={"error":f"{name}: {type(error).__name__}","status":"failed"}
            visible=dict(state)
            for key,value in update.items():
                visible[key]=state.get(key,[])+value if key in ["trials","routes"] else value
            event_log.emit("node_completed",name,visible)
            return update
        return execute
    graph=StateGraph(MLState)
    operations={
        "load_postgres":lambda s:nodes.load_data(s,loader),
        "prepare_features":nodes.feature_preparation,
        "dummy_baseline":nodes.baseline,
        "choose_candidate":nodes.select_candidate,
        "train_model":nodes.train_model,
        "evaluate_validation":nodes.evaluate_validation,
        "conditional_router":nodes.route,
        "final_test_once":nodes.final_test,
        "report":nodes.reporting,
        "failure_report":nodes.failure_reporting}
    for name,function in operations.items():
        graph.add_node(name,wrapped(name,function))
    graph.add_edge(START,"load_postgres")
    def checked(source,destination):
        graph.add_conditional_edges(source,lambda s:"failed" if s.get("error") else "ok",
                                    {"ok":destination,"failed":"failure_report"})
    checked("load_postgres","prepare_features")
    checked("prepare_features","dummy_baseline")
    checked("dummy_baseline","choose_candidate")
    checked("choose_candidate","train_model")
    checked("train_model","evaluate_validation")
    checked("evaluate_validation","conditional_router")
    graph.add_conditional_edges("conditional_router",
        lambda s:"failure" if s.get("error") else s["decision"],
        {"retry":"choose_candidate","finish":"final_test_once","failure":"failure_report"})
    checked("final_test_once","report")
    graph.add_conditional_edges("report",lambda s:"failed" if s.get("error") else "done",
                                {"failed":"failure_report","done":END})
    graph.add_edge("failure_report",END)
    return graph.compile()
