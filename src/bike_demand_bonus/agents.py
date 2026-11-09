"""Meaningful data, feature, selection, training, evaluation and recovery roles."""
import numpy as np
import pandas as pd
from bike_demand.contracts import dataset_hash,validate_final,require
from bike_demand_ml.models import prepare,score,FORBIDDEN
from bike_demand_bonus.models import make_candidate

class TrainingInterrupted(RuntimeError):
    """Supported transient fit interruption, used by isolated fault tests."""

def quality(state):
    frame=state["frame"]
    validate_final(frame)
    digest=dataset_hash(frame)
    require(digest==state["provenance"]["dataset_hash"],"Snapshot provenance mismatch")
    require(state["provenance"].get("origin") in
        {"application_postgresql","isolated_evaluation_fixture","synthetic_unit_fixture"},
        "Unknown data origin")
    return {"dataset_hash":digest,"quality":{"rows":len(frame),"unique_dates":int(frame.date.nunique()),
        "start":min(frame.date),"end":max(frame.date),"dataset_hash":digest,"contract_valid":True},
        "phase":"quality_checked"}

def features(state):
    X,y,splits=prepare(state["frame"])
    train=splits["train"]
    training=X.iloc[train].astype(float)
    assert not FORBIDDEN.intersection(X.columns)
    corr=training.corr().abs()
    mean="temperature_2m_mean"
    collinear=[name for name in ["temperature_2m_max","temperature_2m_min"]
        if float(corr.loc[mean,name])>0.95]
    associations=training.loc[:,training.nunique()>1].corrwith(y.iloc[train]).abs().fillna(0)
    diagnostic={"scope":"2011 training partition only","collinear_weather":collinear,
        "maximum_target_correlation":float(associations.max()),
        "constant_features":[name for name in training if training[name].nunique()==1],
        "train_rows":len(train),"validation_rows":len(splits["validation"]),"test_rows":len(splits["test"])}
    model=make_candidate({"name":"dummy"},list(X.columns))
    model.fit(X.iloc[train],y.iloc[train])
    baseline=score(y.iloc[splits["validation"]],model.predict(X.iloc[splits["validation"]]))
    return {"X":X,"y":y,"splits":splits,"features":list(X.columns),"diagnostics":diagnostic,
        "baseline":baseline,"best":{"spec":{"name":"dummy"},"features":list(X.columns),
                                  "validation":baseline},"phase":"features_ready"}

def refine(state):
    drop=state["diagnostics"]["collinear_weather"]
    selected=[c for c in state["features"] if c not in drop]
    assert selected and not FORBIDDEN.intersection(selected)
    return {"features":selected,"refined":True,"phase":"features_refined"}

def select(state):
    policy=state["policy"]
    previous=state["trials"][-1] if state["trials"] else {}
    gap=previous.get("gap",0)
    if state["scenario"]=="weak_model":spec={"name":"dummy"}
    elif state["scenario"]=="invalid_model":spec={"name":"unsupported"}
    elif policy=="fixed_port":spec={"name":"ridge","alpha":10.0}
    elif policy=="simple_port":
        spec=([{"name":"ridge","alpha":10.0},{"name":"forest"},{"name":"ridge","alpha":100.0}]
              [state["attempt"]%3])
    elif not state["attempt"]:
        spec=({"name":"ridge","alpha":10.0} if state["diagnostics"]["maximum_target_correlation"]>=0.3
              else {"name":"forest"})
    elif gap>1.5:spec={"name":"ridge","alpha":100.0}
    else:spec={"name":"forest"}
    tried=state.get("tried",[])
    identity={"spec":spec,"features":state["features"]}
    if identity in tried and policy=="adaptive" and state["scenario"]!="weak_model":
        spec=({"name":"forest"} if spec["name"]!="forest" else {"name":"ridge","alpha":1000.0})
        identity={"spec":spec,"features":state["features"]}
    return {"spec":spec,"attempt":state["attempt"]+1,"tried":tried+[identity],
            "issue":None,"phase":"candidate_selected"}

def train(state,trainer=None):
    if trainer:
        model=trainer(state)
    else:
        model=make_candidate(state["spec"],state["features"])
        train=state["splits"]["train"]
        model.fit(state["X"].iloc[train],state["y"].iloc[train])
    return {"model":model,"phase":"trained"}

def evaluate(state):
    train,val=state["splits"]["train"],state["splits"]["validation"]
    model=state["model"]
    train_metrics=score(state["y"].iloc[train],model.predict(state["X"].iloc[train]))
    metrics=score(state["y"].iloc[val],model.predict(state["X"].iloc[val]))
    trial={"attempt":state["attempt"],"spec":state["spec"],"features":state["features"],
           "status":"success","train":train_metrics,"validation":metrics,
           "gap":metrics["rmse"]/max(train_metrics["rmse"],1e-9)}
    best=state["best"]
    if metrics["rmse"]<best["validation"]["rmse"]:
        best={"spec":state["spec"],"features":state["features"],"validation":metrics}
    return {"trials":[trial],"best":best,"phase":"evaluated"}

def decision(state):
    """Pure coordinator: no held-out metrics are read here."""
    issue=state.get("issue")
    phase=state.get("phase")
    if issue:
        can_retry=(issue["recoverable"] and state["recoveries"]<state["max_recoveries"] and
            ((issue["stage"]=="data_loader" and state["load_attempts"]<state["max_loads"]) or
             (issue["stage"]=="training" and state["attempt"]<state["max_attempts"])))
        if state["policy"]=="simple_port":can_retry=False
        return ("recovery","supported_transient_failure") if can_retry else ("failure_report","unrecoverable_or_retry_exhausted")
    forward={"loaded":"data_quality","quality_checked":"feature_analysis",
        "features_ready":"model_selection","features_refined":"model_selection",
        "candidate_selected":"training","trained":"evaluation","tested":"reporting"}
    if phase in forward:return forward[phase],"validated_"+phase
    if phase=="recovered":return state["recovery_target"],"resume_after_bounded_recovery"
    if phase=="evaluated":
        if state["policy"]=="fixed_port":return "final_test","fixed_workflow_single_candidate"
        if state["attempt"]>=state["max_attempts"]:return "final_test","attempt_budget_exhausted"
        trial=state["trials"][-1]
        met=state["best"]["validation"]["rmse"]<=0.95*state["baseline"]["rmse"]
        if met and (state["policy"]=="simple_port" or trial["gap"]<=1.5):
            return "final_test","validation_target_met"
        if (state["policy"]=="adaptive" and not state.get("refined") and trial["gap"]>1.5
                and state["diagnostics"]["collinear_weather"]):
            return "feature_refinement","train_validation_gap_and_collinear_weather"
        return "model_selection","validation_gap_requires_another_candidate"
    return "failure_report","invalid_coordinator_phase"

def coordinate(state):
    target,reason=decision(state)
    record={"from_phase":state.get("phase"),"destination":target,"reason":reason,
        "attempt":state["attempt"],"recoveries":state["recoveries"],
        "issue_type":(state.get("issue") or {}).get("type"),
        "issue_stage":(state.get("issue") or {}).get("stage"),
        "recoverable":(state.get("issue") or {}).get("recoverable",False),
        "load_attempts":state["load_attempts"],"max_loads":state["max_loads"],
        "max_attempts":state["max_attempts"],"max_recoveries":state["max_recoveries"],
        "refined":state.get("refined",False),
        "has_collinear_weather":bool(state.get("diagnostics",{}).get("collinear_weather")),
        "last_gap":(state.get("trials") or [{}])[-1].get("gap"),
        "validation_target_met":bool(state.get("best") and state["best"]["validation"]["rmse"]<=0.95*state["baseline"]["rmse"]),
        "uses_heldout_metrics":False}
    return {"next_node":target,"reason":reason,"routes":[record]}

def recover(state):
    issue=state["issue"]
    return {"recoveries":state["recoveries"]+1,"recovery_target":
        "data_loader" if issue["stage"]=="data_loader" else "model_selection",
        "issue":None,"phase":"recovered"}

def final_test(state):
    assert state.get("test_stage_count",0)==0
    joined=np.concatenate([state["splits"]["train"],state["splits"]["validation"]])
    test=state["splits"]["test"]
    spec=state["best"]["spec"];features=state["best"]["features"]
    model=make_candidate(spec,features)
    model.fit(state["X"].iloc[joined],state["y"].iloc[joined])
    dummy=make_candidate({"name":"dummy"},features)
    dummy.fit(state["X"].iloc[joined],state["y"].iloc[joined])
    prediction=model.predict(state["X"].iloc[test])
    comparison=dummy.predict(state["X"].iloc[test])
    output=pd.DataFrame({"date":state["frame"].sort_values("date").iloc[test].date.values,
        "observed_cnt":state["y"].iloc[test].to_numpy(),"prediction":prediction,"dummy_prediction":comparison})
    return {"model":model,"predictions":output,"final_metrics":{
        "selected":score(state["y"].iloc[test],prediction),"dummy":score(state["y"].iloc[test],comparison)},
        "test_stage_count":1,"phase":"tested"}
