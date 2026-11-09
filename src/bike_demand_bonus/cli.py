import argparse,json,os
from pathlib import Path
from datetime import datetime,timezone
from bike_demand_bonus.runner import execute
from bike_demand_bonus.evaluation import evaluate_suite
from bike_demand_bonus.classroom import probe

def main():
    parser=argparse.ArgumentParser(description="Original optional adaptive bike-demand system")
    parser.add_argument("command",choices=["run","evaluate","classroom"])
    parser.add_argument("--id",default="bonus_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
    args=parser.parse_args()
    root=Path(os.environ.get("PROJECT_ARTIFACT_DIR","/opt/project/artifacts"))/"bonus"
    if args.command=="run":
        result=execute(args.id,root/"runs")
        print(json.dumps({k:result.get(k) for k in ["run_id","status","attempt","recoveries","best","final_metrics","issue"]},indent=2))
        return 0 if result["status"]=="success" else 1
    if args.command=="evaluate":
        result=evaluate_suite(args.id,root);print(json.dumps(result,indent=2))
        return 0 if result["failed"]==0 else 1
    result=probe(args.id,root,os.environ.get("CLASSROOM_ROOT","/opt/project/classroom-reference"))
    print(json.dumps(result,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
