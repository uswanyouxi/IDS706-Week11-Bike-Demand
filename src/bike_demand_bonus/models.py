"""Shared fair regression harness; no classroom classification scores relabeled."""
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from bike_demand_ml.models import CATEGORICAL,NUMERICAL,SEED

def make_candidate(spec,features):
    if spec["name"]=="dummy":return DummyRegressor(strategy="mean")
    cat=[c for c in CATEGORICAL if c in features]
    num=[c for c in NUMERICAL if c in features]
    transform=ColumnTransformer([
        ("calendar",OneHotEncoder(handle_unknown="ignore",sparse_output=False),cat),
        ("numeric",StandardScaler(),num)],remainder="drop")
    if spec["name"]=="ridge":estimator=Ridge(alpha=float(spec["alpha"]))
    elif spec["name"]=="forest":
        estimator=RandomForestRegressor(n_estimators=120,max_depth=6,min_samples_leaf=8,
                                         random_state=SEED,n_jobs=1)
    else:raise ValueError("Unsupported model family")
    return Pipeline([("features",transform),("regressor",estimator)])
