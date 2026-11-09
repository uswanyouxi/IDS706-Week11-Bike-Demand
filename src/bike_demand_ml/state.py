from operator import add
from typing import Annotated, Any, TypedDict

class MLState(TypedDict, total=False):
    run_id: str
    output_dir: str
    min_attempts: int
    max_attempts: int
    target_improvement: float
    attempt: int
    frame: Any
    provenance: dict
    dataset_hash: str
    X: Any
    y: Any
    splits: dict
    feature_names: list[str]
    baseline_metrics: dict
    candidate_spec: dict
    fitted_model: Any
    fit_error: str
    train_metrics: dict
    validation_metrics: dict
    best_spec: dict
    best_validation_rmse: float
    trials: Annotated[list[dict], add]
    routes: Annotated[list[dict], add]
    decision: str
    stop_reason: str
    error: str
    final_metrics: dict
    selected_model: Any
    predictions: Any
    test_stage_count: int
    artifacts: dict
    status: str
