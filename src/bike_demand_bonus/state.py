from operator import add
from typing import Annotated,Any,TypedDict

class BonusState(TypedDict,total=False):
    run_id:str
    output_dir:str
    policy:str
    scenario:str
    phase:str
    next_node:str
    reason:str
    frame:Any
    provenance:dict
    dataset_hash:str
    quality:dict
    X:Any
    y:Any
    splits:dict
    features:list[str]
    diagnostics:dict
    refined:bool
    load_attempts:int
    max_loads:int
    attempt:int
    max_attempts:int
    recoveries:int
    max_recoveries:int
    recovery_target:str
    issue:dict
    spec:dict
    tried:list
    model:Any
    baseline:dict
    best:dict
    trials:Annotated[list[dict],add]
    routes:Annotated[list[dict],add]
    final_metrics:dict
    predictions:Any
    test_stage_count:int
    status:str
