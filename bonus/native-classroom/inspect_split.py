"""Derive row splits from native source contracts; never trains a model."""
import json,sys
from importlib.metadata import version
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
ROOT=Path("/evidence/native_classroom_01")
mode=sys.argv[1];assert mode in {"dag","loop"}
frame=pd.read_csv("/repo/datasets/airflow/merged_latest.csv")
indices=list(range(len(frame)))
trainpool,evaluation=train_test_split(indices,test_size=0.2,random_state=42,stratify=frame.is_fraud)
result={"mode":mode,"derivation":"Recomputed row indices from the unchanged source split contract and actual published sample; no estimator fit",
        "sklearn":version("scikit-learn"),"numpy":version("numpy"),"first_train_indices":sorted(trainpool),"first_eval_indices":sorted(evaluation)}
if mode=="loop":
    train,validation=train_test_split(trainpool,test_size=0.25,random_state=42,stratify=frame.is_fraud.iloc[trainpool])
    result.update(selection_training_indices=sorted(train),selection_validation_indices=sorted(validation))
with (ROOT/("derived-"+mode+"-split.json")).open("x",encoding="utf-8") as f:json.dump(result,f,indent=2);f.write("\n")
print(json.dumps({k:v for k,v in result.items() if not k.endswith("indices")}))
