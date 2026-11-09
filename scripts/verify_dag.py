"""Run with real Airflow 3.4.0 on Linux; never substitute stubs."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from airflow.dag_processing.dagbag import DagBag

parser=argparse.ArgumentParser()
parser.add_argument("--output",default="/opt/project/artifacts/verification/dag-parse.json")
args=parser.parse_args()
folder=os.environ.get("AIRFLOW__CORE__DAGS_FOLDER","/opt/airflow/dags")
bag=DagBag(dag_folder=folder,safe_mode=False)
if bag.import_errors:
    raise SystemExit("Real DagBag import errors: "+json.dumps(bag.import_errors))
dag=bag.dags.get("dc_bike_weather_daily")
assert dag is not None,"DAG missing"
assert not dag.catchup and dag.max_active_runs==1 and dag.max_active_tasks==2
assert str(dag.timezone)=="America/New_York"
assert dag.schedule=="0 6 * * *"
assert dag.get_task("validate_and_merge_dates").upstream_task_ids=={"clean_bike","clean_weather"}
assert dag.get_task("download_uci").downstream_task_ids=={"clean_bike"}
assert dag.get_task("fetch_era5_weather").downstream_task_ids=={"clean_weather"}
result=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),real_airflow_parse=True,
    dag_id=dag.dag_id,schedule="0 6 * * *",timezone=str(dag.timezone),catchup=dag.catchup,
    max_active_runs=dag.max_active_runs,max_active_tasks=dag.max_active_tasks,
    task_ids=sorted(dag.task_ids),edges={t.task_id:sorted(t.downstream_task_ids) for t in dag.tasks},
    task_retries={t.task_id:t.retries for t in dag.tasks},import_errors=bag.import_errors)
path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
