import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import uuid
from bike_demand_ml.runner import execute_run

def main():
    parser=argparse.ArgumentParser(description="Original DC bike LangGraph regression workflow")
    parser.add_argument("--run-id",default="ml_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"_"+uuid.uuid4().hex[:6])
    parser.add_argument("--min-attempts",type=int,default=2)
    parser.add_argument("--max-attempts",type=int,default=2)
    parser.add_argument("--target-improvement",type=float,default=0.05)
    args=parser.parse_args()
    root=Path(os.environ.get("PROJECT_ARTIFACT_DIR","/opt/project/artifacts"))/"ml"
    try:
        result=execute_run(args.run_id,root,min_attempts=args.min_attempts,max_attempts=args.max_attempts,
                           target_improvement=args.target_improvement)
    except Exception as error:
        print(json.dumps({"status":"failed","error_type":type(error).__name__,"metrics_claimed":False}))
        return 1
    print(json.dumps({k:result.get(k) for k in ["run_id","status","attempt","best_spec","stop_reason","final_metrics","error"]},indent=2))
    return 0 if result["status"]=="success" else 1
