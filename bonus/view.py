"""Read-only bonus execution and evaluation view; no simulated status/metrics."""
import json,os
from pathlib import Path
import pandas as pd
import streamlit as st
from bike_demand_ml.visuals import graph_dot

st.set_page_config(page_title="Optional Adaptive Bike Demand",layout="wide")
st.title("Optional Part 3: Adaptive Bike-Demand Agents")
st.caption("Separate bonus branch; original Part 2 is available in navigation. Retrospective observed-weather backtest.")
root=Path(os.environ.get("PROJECT_ARTIFACT_DIR","/opt/project/artifacts"))/"bonus"
runs=sorted([p for p in (root/"runs").glob("*") if (p/"graph.json").is_file()],reverse=True)
if not runs:
    st.info("No bonus execution records yet. Run the approved bonus commands.");st.stop()
names=[p.name for p in runs]
selected=st.selectbox("Bonus recorded run",names,index=names.index("bonus_main_01") if "bonus_main_01" in names else 0)
folder=root/"runs"/selected

@st.fragment(run_every="2s")
def show_run():
    events=[]
    if (folder/"events.jsonl").exists():
        for line in (folder/"events.jsonl").read_text().splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:pass
    if not events:return
    live=st.checkbox("Follow bonus execution",value=True)
    point=len(events) if live else st.slider("Replay actual bonus event",1,len(events),len(events))
    visible=events[:point];last=visible[-1]
    left,right=st.columns([3,2])
    with left:
        st.graphviz_chart(graph_dot(json.loads((folder/"graph.json").read_text()),visible),width="stretch")
    with right:
        st.metric("Candidate attempts",last.get("attempt",0))
        st.metric("Recoveries",last.get("recoveries",0))
        st.write("Next agent",last.get("next_node"));st.write("Routing explanation",last.get("reason"))
        st.dataframe(pd.DataFrame([{k:e.get(k) for k in ["sequence","node","kind","attempt","next_node","reason"]} for e in visible]),hide_index=True,width="stretch")
    if not (folder/"report.json").exists():return
    result=json.loads((folder/"report.json").read_text())
    st.subheader("Recorded final report")
    st.write("Status",result["status"])
    if result["status"]=="success":
        st.dataframe(pd.DataFrame([{"model":name,**metrics} for name,metrics in result["final_metrics"].items()]),hide_index=True,width="stretch")
        st.write("Selected by validation",result["best"])
        st.write("Negative held-out predictions",result["negative_predictions"])
    else:st.error("No successful held-out evaluation claimed.");st.json(result.get("issue"))
    st.subheader("Agent-level validation and decisions")
    st.dataframe(pd.DataFrame(result.get("agent_metrics",{})).T,width="stretch")
    st.json(result.get("quality"));st.json(result.get("diagnostics"))
    st.dataframe(pd.json_normalize(result.get("trials",[])),width="stretch",hide_index=True)
    st.dataframe(pd.DataFrame(result.get("routes",[])),width="stretch",hide_index=True)
show_run()
st.subheader("Evaluation suite and baseline comparison")
suites=sorted([p for p in (root/"evaluations").glob("*") if (p/"summary.json").exists()],reverse=True)
if suites:
    suite=st.selectbox("Recorded evaluation suite",[p.name for p in suites])
    path=root/"evaluations"/suite
    summary=json.loads((path/"summary.json").read_text())
    comparison=[]
    for row in summary:
        comparison.append({"policy":row["policy"],**row["normal_test"]["selected"],
            **{k:row[k] for k in ["completion_rate","expected_behavior_pass_rate","incorrect_routing_rate",
                                "total_attempts","total_recoveries","total_wall_seconds"]}})
    st.dataframe(pd.DataFrame(comparison),hide_index=True,width="stretch")
    results=json.loads((path/"results.json").read_text())
    columns=["case","policy","observed_status","expected","score","threshold","passed",
             "attempts","recoveries","incorrect_routes","wall_seconds"]
    st.dataframe(pd.DataFrame(results)[columns],hide_index=True,width="stretch")
    with st.expander("Full per-case criteria and intermediate checks"):
        st.json(results)
    rates=pd.DataFrame(json.loads((path/"summary.json").read_text())).set_index("policy")
    st.bar_chart(rates[["completion_rate","expected_behavior_pass_rate"]])
    with st.expander("Explicit inputs, expected outcomes, criteria and thresholds"):
        st.json(json.loads((path/"case_definitions.json").read_text()))
else:st.info("No completed evaluation suite available.")
st.warning("Fixed/simple rows are explicit bike-demand regression ports of classroom control patterns. They are not unmodified classroom executions or evidence of a classroom Airflow DAG run.")
for path in sorted((root/"classroom").glob("*/summary.json")):
    st.subheader("Unmodified classroom reference probes")
    st.json(json.loads(path.read_text()))
st.caption("Only real recorded results are shown. Failures/rejections count separately from expected-behavior passes. No paid API is required.")
