import copy
import pytest
pytest.importorskip("langgraph")
from bike_demand_ml.nodes import route,select_candidate,train_model
from bike_demand_ml.models import prepare,make_model,FEATURES,FORBIDDEN,NUMERICAL

def state(attempt=1,minimum=1,maximum=2,best=400):
    return {"attempt":attempt,"min_attempts":minimum,"max_attempts":maximum,
        "target_improvement":0.05,"baseline_metrics":{"validation":{"rmse":600}},
        "best_validation_rmse":best,"best_spec":{"name":"ridge","alpha":10.0},
        "trials":[{"status":"success","train":{"rmse":300},"validation":{"rmse":400},
                   "validation_to_train_rmse":4/3}]}

def test_success_route():
    update=route(state())
    assert update["decision"]=="finish" and update["stop_reason"]=="validation_target_met"

def test_retry_comparison_route():
    update=route(state(minimum=2))
    assert update["decision"]=="retry" and update["stop_reason"]=="predeclared_candidate_comparison"

def test_retry_underperforming_route():
    update=route(state(best=650))
    assert update["decision"]=="retry" and update["stop_reason"]=="validation_target_not_met"

def test_max_attempts_stops_even_without_target():
    update=route(state(attempt=2,minimum=2,best=650))
    assert update["decision"]=="finish" and update["stop_reason"]=="max_attempts_reached"

def test_router_cannot_see_test_metrics():
    original=state();modified=copy.deepcopy(original)
    modified["final_metrics"]={"selected":{"rmse":999999999}}
    assert route(original)==route(modified)

def test_adaptive_regularization_vs_nonlinearity():
    s=state()
    assert select_candidate(s)["candidate_spec"]["name"]=="random_forest"
    s["trials"][0]["train"]["rmse"]=100
    spec=select_candidate(s)["candidate_spec"]
    assert spec=={"name":"ridge","alpha":100.0}

def test_temporal_splits_and_target_exclusion(synthetic_frame):
    X,y,splits=prepare(synthetic_frame)
    assert list(X)==FEATURES and not set(X)&FORBIDDEN
    assert [len(splits[k]) for k in ["train","validation","test"]]==[365,182,184]
    assert max(splits["train"])<min(splits["validation"])<min(splits["test"])

def test_transformer_fit_only_training(synthetic_frame):
    X,y,splits=prepare(synthetic_frame);train=splits["train"]
    fitted=make_model({"name":"ridge","alpha":10}).fit(X.iloc[train],y.iloc[train])
    scaler=fitted.named_steps["features"].named_transformers_["numerical"]
    assert scaler.mean_[NUMERICAL.index("elapsed_day")]==182.0
    assert scaler.mean_[NUMERICAL.index("elapsed_day")]!=X["elapsed_day"].mean()
