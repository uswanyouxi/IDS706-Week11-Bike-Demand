"""Read-only runtime-reflective UI for the original compiled ML graph."""
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from bike_demand_ml.visuals import graph_dot

st.set_page_config(page_title="DC Bike Demand Model Lab",layout="wide")
st.title("DC Bike Demand Model Lab")
st.caption("Retrospective weather-conditioned regression • actual LangGraph events • validation-only model selection")
root=Path(os.environ.get("PROJECT_ARTIFACT_DIR","/opt/project/artifacts"))/"ml"
runs=sorted([p for p in root.glob("*") if p.is_dir() and (p/"graph.json").exists()],key=lambda p:p.name,reverse=True)
if not runs:
    st.info("No ML run artifacts yet. Start the database-fed runner using the README commands.")
    st.stop()
selected=st.selectbox("Recorded execution",[p.name for p in runs])
folder=root/selected
st.caption(f"Run: {selected} — read-only artifact view; this page cannot train or modify PostgreSQL.")

@st.fragment(run_every="2s")
def execution_view():
    events=[]
    if (folder/"events.jsonl").exists():
        for line in (folder/"events.jsonl").read_text(encoding="utf-8").splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:pass  # A final line may still be flushing.
    if not events:
        st.info("Waiting for recorded node events.")
        return
    follow=st.checkbox("Follow live execution",value=True,key=f"follow-{selected}")
    step=len(events) if follow else st.slider("Replay actual event",1,len(events),len(events),key=f"event-{selected}")
    visible=events[:step]
    last=visible[-1]
    graph=json.loads((folder/"graph.json").read_text(encoding="utf-8"))
    left,right=st.columns([3,2])
    with left:
        st.subheader("Original executable agent graph")
        st.graphviz_chart(graph_dot(graph,visible),width="stretch")
        st.caption(f"Event {step}/{len(events)} • {last['at_utc']} • {last['node']} • {last['kind']}")
    with right:
        st.subheader("Execution progress")
        st.metric("Candidate attempts",last.get("attempt",0))
        st.write("Latest route",last.get("decision") or "Not routed yet")
        st.write("Reason",last.get("stop_reason") or "In progress")
        if last.get("error"):st.error(last["error"])
        st.dataframe(pd.DataFrame([{k:e.get(k) for k in ["sequence","node","kind","attempt","decision","stop_reason"]} for e in visible]),
                     hide_index=True,width="stretch")
    report_path=folder/"report.json"
    if not report_path.exists():
        st.info("The run has not produced its final report yet.")
        return
    report=json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status")!="success":
        st.error("Run failed; no successful evaluation is claimed.")
        st.json({k:report.get(k) for k in ["status","error","provenance"]})
        return
    st.subheader("Held-out test — July–December 2012")
    st.caption("Selection was frozen before this one final test stage. Both estimators were refit on train+validation.")
    rows=[{"model":"Selected: "+report["best_spec"]["name"],**report["final_metrics"]["selected"]},
          {"model":"Dummy baseline",**report["final_metrics"]["dummy"]}]
    st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
    st.write("Selected model specification",report["best_spec"])
    st.write("Stop reason",report["stop_reason"])
    st.caption(f"Database: {report['provenance']['database']}.{report['provenance']['table']} • "
               f"rows: {report['provenance']['rows']} • dataset hash: {report['dataset_hash']}")
    st.subheader("Validation trials and conditional routing")
    trials=[]
    for trial in report["trials"]:
        trials.append({"attempt":trial["attempt"],"candidate":str(trial["candidate"]),"status":trial["status"],
            "validation_mae":trial.get("validation",{}).get("mae"),
            "validation_rmse":trial.get("validation",{}).get("rmse"),
            "train_rmse":trial.get("train",{}).get("rmse")})
    st.dataframe(pd.DataFrame(trials),hide_index=True,width="stretch")
    st.dataframe(pd.DataFrame(report["routes"]),hide_index=True,width="stretch")
    a,b=st.columns(2)
    for column,name in [(a,"test_predictions.png"),(b,"validation_rmse.png")]:
        if (folder/name).exists():
            with column:st.image(str(folder/name),width="stretch")
    with st.expander("Input features, chronological split and provenance"):
        for name in ["features.json","splits.json","provenance.json"]:
            if (folder/name).exists():st.json(json.loads((folder/name).read_text(encoding="utf-8")))
    st.caption("Observed historical weather is not a future weather forecast. No causal claim or test-driven tuning.")

execution_view()
