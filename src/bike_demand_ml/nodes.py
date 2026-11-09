"""Original specialist nodes and validation-only adaptive control policy."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from bike_demand.contracts import dataset_hash
from bike_demand.io_utils import write_json
from bike_demand_ml.models import prepare,make_model,score,FEATURES,FORBIDDEN,SEED
from bike_demand_ml.artifacts import safe_projection

def load_data(state,loader):
    frame,provenance=loader()
    digest=dataset_hash(frame)
    assert digest==provenance["dataset_hash"]
    folder=Path(state["output_dir"])
    frame.to_csv(folder/"database_snapshot.csv",index=False)
    write_json(folder/"provenance.json",provenance)
    return {"frame":frame,"provenance":provenance,"dataset_hash":digest,"status":"running"}

def feature_preparation(state):
    X,y,splits=prepare(state["frame"])
    manifest={}
    for name,index in splits.items():
        dates=state["frame"].sort_values("date").iloc[index]["date"]
        manifest[name]={"rows":len(index),"start":dates.iloc[0],"end":dates.iloc[-1]}
    folder=Path(state["output_dir"])
    write_json(folder/"splits.json",manifest)
    write_json(folder/"features.json",{"inputs":FEATURES,"excluded":sorted(FORBIDDEN),
        "derived":{"elapsed_day":"days since 2011-01-01; calendar-only","month_sin_cos":"calendar month cycle"},
        "preprocessing_fit_scope":"training partition only during candidate selection",
        "final_refit_scope":"train+validation only after frozen selection"})
    return {"X":X,"y":y,"splits":splits,"feature_names":list(X.columns)}

def baseline(state):
    train,val=state["splits"]["train"],state["splits"]["validation"]
    model=make_model({"name":"dummy"})
    model.fit(state["X"].iloc[train],state["y"].iloc[train])
    metrics={"train":score(state["y"].iloc[train],model.predict(state["X"].iloc[train])),
             "validation":score(state["y"].iloc[val],model.predict(state["X"].iloc[val]))}
    return {"baseline_metrics":metrics,"best_spec":{"name":"dummy"},
            "best_validation_rmse":metrics["validation"]["rmse"]}

def select_candidate(state):
    attempt=state.get("attempt",0)+1
    if attempt==1:
        spec={"name":"ridge","alpha":10.0}
    else:
        last=state["trials"][-1]
        train_rmse=last.get("train",{}).get("rmse")
        val_rmse=last.get("validation",{}).get("rmse")
        if train_rmse is not None and val_rmse is not None and val_rmse/max(train_rmse,1e-9)>1.5:
            spec={"name":"ridge","alpha":100.0}
        else:
            spec={"name":"random_forest","n_estimators":150,"max_depth":6,"min_samples_leaf":8,"seed":SEED}
    return {"attempt":attempt,"candidate_spec":spec,"fitted_model":None,"fit_error":None}

def train_model(state):
    try:
        model=make_model(state["candidate_spec"])
        train=state["splits"]["train"]
        model.fit(state["X"].iloc[train],state["y"].iloc[train])
        return {"fitted_model":model,"fit_error":None}
    except Exception as error:
        return {"fitted_model":None,"fit_error":type(error).__name__}

def evaluate_validation(state):
    trial={"attempt":state["attempt"],"candidate":state["candidate_spec"]}
    if state.get("fit_error"):
        trial.update(status="failed",error_type=state["fit_error"])
        return {"trials":[trial]}
    train,val=state["splits"]["train"],state["splits"]["validation"]
    model=state["fitted_model"]
    train_metrics=score(state["y"].iloc[train],model.predict(state["X"].iloc[train]))
    val_metrics=score(state["y"].iloc[val],model.predict(state["X"].iloc[val]))
    trial.update(status="success",train=train_metrics,validation=val_metrics,
                 validation_to_train_rmse=val_metrics["rmse"]/max(train_metrics["rmse"],1e-9))
    update={"trials":[trial],"train_metrics":train_metrics,"validation_metrics":val_metrics}
    if val_metrics["rmse"]<state["best_validation_rmse"]:
        update.update(best_validation_rmse=val_metrics["rmse"],best_spec=state["candidate_spec"])
    return update

def route(state):
    baseline_rmse=state["baseline_metrics"]["validation"]["rmse"]
    quality=state["best_validation_rmse"] <= (1-state["target_improvement"])*baseline_rmse
    attempts=state["attempt"]
    if quality and attempts>=state["min_attempts"]:
        decision,reason="finish","validation_target_met"
    elif attempts>=state["max_attempts"]:
        decision,reason="finish","max_attempts_reached"
    elif attempts<state["min_attempts"]:
        decision,reason="retry","predeclared_candidate_comparison"
    else:
        decision,reason="retry","validation_target_not_met"
    last=state["trials"][-1]
    gap=last.get("validation_to_train_rmse")
    next_policy=("stronger Ridge regularization because validation/train RMSE > 1.5"
                 if gap is not None and gap>1.5 else "nonlinear RandomForest or fallback after failed fit")
    record={"after_attempt":attempts,"decision":decision,"reason":reason,
        "validation_target_rmse":(1-state["target_improvement"])*baseline_rmse,
        "best_validation_rmse":state["best_validation_rmse"],"best_candidate":state["best_spec"],
        "next_candidate_reason":next_policy if decision=="retry" else None}
    return {"decision":decision,"stop_reason":reason,"routes":[record]}

def final_test(state):
    # Selection is frozen before this node; no edge returns to model selection.
    assert state.get("test_stage_count",0)==0,"Test stage must execute once"
    trainval=np.concatenate([state["splits"]["train"],state["splits"]["validation"]])
    test=state["splits"]["test"]
    model=make_model(state["best_spec"])
    dummy=make_model({"name":"dummy"})
    model.fit(state["X"].iloc[trainval],state["y"].iloc[trainval])
    dummy.fit(state["X"].iloc[trainval],state["y"].iloc[trainval])
    prediction=model.predict(state["X"].iloc[test])
    dummy_prediction=dummy.predict(state["X"].iloc[test])
    predictions=pd.DataFrame({"date":state["frame"].sort_values("date").iloc[test]["date"].values,
        "observed_cnt":state["y"].iloc[test].to_numpy(),"selected_prediction":prediction,
        "dummy_prediction":dummy_prediction})
    return {"selected_model":model,"predictions":predictions,"test_stage_count":1,
        "final_metrics":{"selected":score(state["y"].iloc[test],prediction),
                         "dummy":score(state["y"].iloc[test],dummy_prediction)},
        "status":"evaluated"}

def reporting(state):
    folder=Path(state["output_dir"])
    state["predictions"].to_csv(folder/"test_predictions.csv",index=False)
    joblib.dump(state["selected_model"],folder/"selected_model.joblib")
    report=safe_projection(state)
    report.update(status="success",target="cnt",seed=SEED,
        test_policy="One final stage after frozen validation selection; both selected model and Dummy refit on train+validation.",
        framing="Retrospective weather-conditioned backtest, not an operational future forecast.",
        model_artifact_note="Only load joblib artifacts you trust; dashboard never unpickles models.",
        artifacts={"report":"report.json","events":"events.jsonl","graph":"graph.json",
            "snapshot":"database_snapshot.csv","provenance":"provenance.json","features":"features.json",
            "splits":"splits.json","predictions":"test_predictions.csv","model":"selected_model.joblib",
            "test_plot":"test_predictions.png","validation_plot":"validation_rmse.png","graph_plot":"agent_graph.png"})
    write_json(folder/"report.json",report)
    write_json(folder/"trials.json",{"trials":state["trials"],"routes":state["routes"]})
    plot_results(state,folder)
    return {"status":"success","artifacts":report["artifacts"]}

def failure_reporting(state):
    report=safe_projection(state);report.update(status="failed",metrics_claimed=False)
    write_json(Path(state["output_dir"])/"report.json",report)
    return {"status":"failed"}

def plot_results(state,folder):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    data=state["predictions"]
    fig,ax=plt.subplots(figsize=(11,4.5))
    dates=pd.to_datetime(data["date"])
    ax.plot(dates,data["observed_cnt"],label="Observed",color="#243746",linewidth=1.3)
    ax.plot(dates,data["selected_prediction"],label="Selected model",color="#007f86",linewidth=1.2)
    ax.plot(dates,data["dummy_prediction"],label="Dummy baseline",color="#cf8b28",linestyle="--")
    ax.set(title="Held-out test: July–December 2012",ylabel="Daily rentals",xlabel="Date")
    ax.legend();fig.autofmt_xdate();fig.tight_layout()
    fig.savefig(folder/"test_predictions.png",dpi=150);plt.close(fig)
    trials=[r for r in state["trials"] if r["status"]=="success"]
    labels=["Dummy"]+[f"Trial {r['attempt']}: {r['candidate']['name']}" for r in trials]
    values=[state["baseline_metrics"]["validation"]["rmse"]]+[r["validation"]["rmse"] for r in trials]
    fig,ax=plt.subplots(figsize=(8,4.5))
    bars=ax.bar(labels,values,color=["#aab6be"]+["#007f86"]*len(trials))
    ax.bar_label(bars,fmt="%.1f");ax.set(ylabel="Validation RMSE (rentals)",title="Selection uses validation data only")
    ax.margins(y=0.15);fig.tight_layout();fig.savefig(folder/"validation_rmse.png",dpi=150);plt.close(fig)
