"""Read-only viewer of real native baseline artifacts; no execution controls."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
ROOT=Path("/evidence/native_classroom_01")
def read(path):return json.loads(Path(path).read_text())
def dot(topology,visited=()):
    lines=["digraph native {","rankdir=LR;"]
    for n in topology["nodes"]:
        name=str(n["id"]);color="#bde6d2" if name in visited else "#e8edf3"
        lines.append(json.dumps(name)+" [style=filled,fillcolor="+json.dumps(color)+"];")
    for edge in topology["edges"]:
        lines.append(json.dumps(str(edge["source"]))+" -> "+json.dumps(str(edge["target"]))+";")
    return "\n".join(lines+["}"])
def main():
    st.set_page_config(page_title="Native Classroom Baselines",layout="wide")
    st.title("Native classroom baseline reproduction")
    st.caption("Original instructor code at a294145ea9aa4225908ce701c06160c33213335d. Recorded executions; no paid LLM.")
    if not (ROOT/"native_prep_01/report.json").exists():
        st.info("Awaiting actual native DAG evidence; no metrics claimed.");return
    airflow=read(ROOT/"native_prep_01/report.json")
    completed=sorted(p.parent for p in ROOT.glob("native_simple_*/report.json") if read(p).get("status")=="success")
    loop_folder=completed[-1] if completed else ROOT/"native_simple_01"
    tabs=st.tabs(["Native Airflow","Native LangGraph","Comparison scopes"])
    with tabs[0]:
        st.subheader("Actual Airflow DAG: solution_baseline_prep")
        st.write("Run ID: "+airflow["run_id"])
        st.success("Seven successful tasks; actual Airflow scheduler execution.")
        st.dataframe(pd.DataFrame(read(ROOT/"native_prep_01/task-states.json")),hide_index=True)
        metric=airflow["baseline_validation"]
        cols=st.columns(3);cols[0].metric("Native validation F1",f"{metric['f1']:.6f}")
        cols[1].metric("Training rows",metric["n_train"]);cols[2].metric("Validation rows",metric["n_val"])
        st.warning("Native DAG uses numeric-only 80/20 classification. It does not emit held-out metrics or accuracy.")
        st.code(airflow["outputs"]["published"]["sha256"],language=None)
        st.write("Dataset: original customers/transactions; 2,000-row published sample.")
        st.json(airflow["outputs"])
    with tabs[1]:
        path=loop_folder/"report.json"
        if not path.exists():st.info("Awaiting native graph run.")
        else:
            r=read(path);st.subheader("Completed native LangGraph: "+r["run_id"])
            st.caption("The instructor's exact graph; heuristic fallback because external credentials are absent.")
            topology=read(loop_folder/"graph.json")
            visited={s["node"] for s in r["steps"]}
            st.graphviz_chart(dot(topology,visited),use_container_width=True)
            cols=st.columns(4)
            cols[0].metric("Cycles",r["cycles"]);cols[1].metric("Best validation F1",f"{r['best_val_f1']:.6f}")
            cols[2].metric("Held-out F1",f"{r['holdout_metrics']['f1']:.6f}")
            cols[3].metric("Held-out accuracy",f"{r['holdout_metrics']['accuracy']:.6f}")
            st.write({"no_key_heuristics":r["no_key_heuristic_mode"],"validation_target":0.8,"target_met":r["target_met"],"stop_reason":r["stop_reason"]})
            records=[{k:s.get(k) for k in ["node","note","status","f1","used_llm","repaired"]} for s in r["steps"]]
            st.dataframe(pd.DataFrame(records),hide_index=True)
            st.caption("Native split: 60/20/20 during selection, refit on 80% for sealed 20% holdout.")
            st.code(r["dataset_sha256"],language=None)
            with st.expander("Native chosen specification and recorded events"):
                st.json(r["best_spec"])
                st.dataframe(pd.DataFrame([json.loads(line) for line in (loop_folder/"events.jsonl").read_text().splitlines()]))
    with tabs[2]:
        st.subheader("A. Native classroom classification")
        rows=[{"system":"Actual native Airflow DAG","stage":"80/20 validation","f1":airflow["baseline_validation"]["f1"],"accuracy":None}]
        if (loop_folder/"report.json").exists():
            r=read(loop_folder/"report.json")
            rows.extend([{"system":"Actual native simple LangGraph","stage":"60/20/20 validation","f1":r["best_val_f1"],"accuracy":None},
                         {"system":"Actual native simple LangGraph","stage":"Sealed 20% holdout","f1":r["holdout_metrics"]["f1"],"accuracy":r["holdout_metrics"]["accuracy"]}])
        st.dataframe(pd.DataFrame(rows),hide_index=True)
        st.warning("Same fraud sample, different split/preprocessing contracts and package versions. No direct F1 ranking.")
        st.subheader("B. Bike Demand regression adaptations")
        summary=Path("/bike-suite/summary.json")
        if summary.exists():
            rows=[]
            for r in read(summary):
                rows.append({"policy":r["policy"],**r["normal_test"]["selected"],
                    "completion_rate":r["completion_rate"],"expected_behavior_pass_rate":r["expected_behavior_pass_rate"]})
            st.dataframe(pd.DataFrame(rows),hide_index=True)
        st.warning("fixed_port and simple_port are explicit regression adaptations. F1 cannot be ranked against RMSE; equal normal-case regression metrics show no predictive advantage.")
        st.caption("Original Bike Demand results are read-only frozen records. These views cannot train models or modify SQL.")
main()
