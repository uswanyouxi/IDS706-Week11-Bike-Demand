"""Date-safe features, lightweight deterministic regressors, regression metrics."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from bike_demand.contracts import WEATHER_COLUMNS, validate_final

SEED=706
CATEGORICAL=["weekday","season"]
NUMERICAL=WEATHER_COLUMNS+["month_sin","month_cos","holiday","workingday","elapsed_day"]
FEATURES=CATEGORICAL+NUMERICAL
FORBIDDEN={"cnt","casual","registered","instant","temp","atemp","hum","windspeed","weathersit"}

def prepare(frame):
    validate_final(frame)
    data=frame.sort_values("date").reset_index(drop=True)
    dates=pd.to_datetime(data["date"],format="%Y-%m-%d")
    X=data[CATEGORICAL+WEATHER_COLUMNS+["holiday","workingday"]].copy()
    X["month_sin"]=np.sin(2*np.pi*dates.dt.month/12)
    X["month_cos"]=np.cos(2*np.pi*dates.dt.month/12)
    X["elapsed_day"]=(dates-pd.Timestamp("2011-01-01")).dt.days
    X=X[FEATURES]
    assert not FORBIDDEN & set(X.columns)
    assert np.isfinite(X.to_numpy(dtype=float)).all()
    y=data["cnt"].astype(float)
    splits={
        "train":np.flatnonzero(dates<"2012-01-01"),
        "validation":np.flatnonzero((dates>="2012-01-01") & (dates<"2012-07-01")),
        "test":np.flatnonzero(dates>="2012-07-01")}
    assert [len(splits[k]) for k in ["train","validation","test"]]==[365,182,184]
    return X,y,splits

def make_model(spec):
    if spec["name"]=="dummy":
        return DummyRegressor(strategy="mean")
    transform=ColumnTransformer([
        ("calendar",OneHotEncoder(handle_unknown="ignore",sparse_output=False),CATEGORICAL),
        ("numerical",StandardScaler(),NUMERICAL)],remainder="drop")
    if spec["name"]=="ridge":
        estimator=Ridge(alpha=spec["alpha"])
    elif spec["name"]=="random_forest":
        estimator=RandomForestRegressor(n_estimators=150,max_depth=6,min_samples_leaf=8,
                                        random_state=SEED,n_jobs=1)
    else:
        raise ValueError("Unknown candidate")
    return Pipeline([("features",transform),("regressor",estimator)])

def score(y,prediction):
    if not np.isfinite(prediction).all():
        raise ValueError("Nonfinite predictions")
    return {"mae":float(mean_absolute_error(y,prediction)),
            "rmse":float(root_mean_squared_error(y,prediction)),
            "r2":float(r2_score(y,prediction))}
