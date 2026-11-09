"""Read-only live checks + genuine exports; never triggers DAGs or writes SQL data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"submission"/"part1"
DAG="dc_bike_weather_daily"
RUN="phase_b_manual_02"
KEY=hashlib.sha256(RUN.encode()).hexdigest()[:24]
OUT.mkdir(parents=True,exist_ok=True)

def docker(arguments, *, input_text=None):
    result=subprocess.run(["docker","compose",*arguments],cwd=ROOT,input=input_text,
        capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=90)
    if result.returncode:
        raise RuntimeError("Evidence command failed: "+result.stderr[-1500:])
    return result.stdout

def save(name,body):
    path=OUT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(body,indent=2)+"\n",encoding="utf-8")

checked=datetime.now(timezone.utc).isoformat()
runs=json.loads(docker(["exec","-T","airflow-scheduler","airflow","dags","list-runs",DAG,"--output","json"]))
save("airflow/live-runs.json",{"checked_at_utc":checked,"runs":runs})
required=["scheduled__2026-11-08T11:00:00+00:00","phase_b_manual_01",RUN]
run_checks=[]
for run_id in required:
    record=next((r for r in runs if r["run_id"]==run_id),None)
    assert record and record["state"]=="success",f"Expected successful run missing: {run_id}"
    tasks=json.loads(docker(["exec","-T","airflow-scheduler","airflow","tasks",
                            "states-for-dag-run",DAG,run_id,"--output","json"]))
    assert len(tasks)==9 and all(t["state"]=="success" for t in tasks),f"Task states changed: {run_id}"
    run_key=hashlib.sha256(run_id.encode()).hexdigest()[:24]
    save(f"airflow/{run_key}-tasks.json",{"run_id":run_id,"tasks":tasks})
    run_checks.append({"run_id":run_id,"state":record["state"],"successful_tasks":len(tasks)})
next_run=docker(["exec","-T","airflow-scheduler","airflow","dags","next-execution",DAG]).strip()
dag_list=json.loads(docker(["exec","-T","airflow-scheduler","airflow","dags","list","--output","json"]))
save("airflow/dag-list.json",dag_list)
save("airflow/live-check.json",{"checked_at_utc":checked,"dag_id":DAG,"runs":run_checks,
    "next_execution_utc":next_run,"method":"Live Airflow CLI; GUI helper unavailable, not a visual inspection"})

container=f"/opt/project/artifacts/pipeline/{KEY}"
for folder in ["eda","validation"]:
    destination=OUT/folder
    destination.mkdir(parents=True,exist_ok=True)
    docker(["cp",f"airflow-scheduler:{container}/{folder}/.",str(destination)])
docker(["cp",f"airflow-scheduler:{container}/load-receipt.json",str(OUT/"validation/load-receipt.json")])
hash_code=("import hashlib,json; from pathlib import Path; root=Path("+repr(container)+"); "
           "files=list((root/'eda').glob('*'))+list((root/'validation').glob('*.json'))+[root/'load-receipt.json']; "
           "print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}))")
source_hashes=json.loads(docker(["exec","-T","airflow-scheduler","python","-c",hash_code]))
for relative,digest in source_hashes.items():
    local=OUT/("validation/load-receipt.json" if relative=="load-receipt.json" else relative)
    assert hashlib.sha256(local.read_bytes()).hexdigest()==digest,f"Export mismatch: {relative}"

sql="""BEGIN TRANSACTION READ ONLY;
SELECT json_build_object(
    'checked_at_utc', transaction_timestamp(),
    'transaction_read_only', current_setting('transaction_read_only'),
    'database', current_database(),
    'table', 'bike_analytics.bike_daily',
    'final_counts', (SELECT json_build_object(
        'rows',count(*),'unique_dates',count(DISTINCT date),
        'first_date',min(date),'last_date',max(date),
        'total_rentals',sum(cnt),'dataset_versions',count(DISTINCT dataset_hash),
        'dataset_hash',min(dataset_hash))
        FROM bike_analytics.bike_daily),
    'runs', (SELECT json_agg(r ORDER BY loaded_at) FROM (
        SELECT run_id,row_count,dataset_hash,loaded_at,
            validation->'matched' AS matched_dates,
            validation->'bike_only' AS bike_only,
            validation->'weather_only' AS weather_only,
            eda_summary IS NOT NULL AS eda_complete,
            eda_summary->>'query' AS analysis_query
        FROM bike_analytics.pipeline_runs) r)
);
COMMIT;
"""
(OUT/"postgres_verify.sql").write_text(sql,encoding="utf-8")
raw=docker(["exec","-T","app-db","psql","-X","-q","-A","-t","-v","ON_ERROR_STOP=1",
            "-U","bike_app","-d","bike_demand","--file","-"],input_text=sql)
live=json.loads(raw)
assert live["transaction_read_only"]=="on"
assert live["final_counts"]["rows"]==live["final_counts"]["unique_dates"]==731
assert live["final_counts"]["total_rentals"]==3292679
assert len({r["dataset_hash"] for r in live["runs"]})==1
save("postgres_live_snapshot.json",live)
before=json.loads((ROOT/"docs/verification/phase-b/sql-before-rerun.json").read_text(encoding="utf-8"))
after=json.loads((ROOT/"docs/verification/phase-b/sql-after-rerun.json").read_text(encoding="utf-8"))
save("idempotence_before.json",before)
save("idempotence_after.json",after)
assert before==after
counts=live["final_counts"]
assert counts["dataset_hash"]==json.loads((OUT/"eda/summary.json").read_text(encoding="utf-8"))["dataset_hash"]
assert counts["rows"]==after["rows"] and counts["total_rentals"]==after["total_rentals"]
lines=["# Read-only PostgreSQL verification","",
    f"Checked at UTC: {live['checked_at_utc']}. Database: {live['database']}; table: {live['table']}.",
    "Server transaction_read_only = on. Only SELECT was executed between BEGIN READ ONLY and COMMIT.","",
    "| Measure | Live result |","| --- | --- |",
    f"| Final rows | {counts['rows']} |",f"| Unique dates | {counts['unique_dates']} |",
    f"| Date coverage | {counts['first_date']} to {counts['last_date']} |",
    f"| Total rentals | {counts['total_rentals']:,} |",f"| Content versions | {counts['dataset_versions']} |","",
    f"Dataset SHA-256: {counts['dataset_hash']}.","","## Persisted load history","",
    "| Run ID | Loaded rows | Matched | Bike-only | Weather-only | EDA recorded |",
    "| --- | --- | --- | --- | --- | --- |"]
for run in live["runs"]:
    lines.append(f"| {run['run_id']} | {run['row_count']} | {run['matched_dates']} | {run['bike_only']} | {run['weather_only']} | {run['eda_complete']} |")
lines += ["","## Idempotence evidence","",
    "The prior controlled runtime test measured the table before and after phase_b_manual_02.",
    "Both saved snapshots show 731 rows, 731 unique dates, 3,292,679 rentals and one dataset version.",
    "All three persisted successful load records share the same content hash.",
    "Today's read-only snapshot matches those totals/hash. No new DAG run or SQL write was performed.","",
    "This combines saved before/after evidence with a fresh read; it does not claim a new idempotence experiment.",
    "See idempotence_before.json, idempotence_after.json, postgres_live_snapshot.json and postgres_verify.sql.","",
    "The EDA provenance stores an ordered SELECT of persisted cleaned columns from bike_analytics.bike_daily.",
    "This report and the EDA exports are evidence artifacts, not UI screenshots."]
(OUT/"postgres_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
(OUT/"postgres_report.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
save("manifest.json",{"exported_at_utc":checked,"dag_id":DAG,"source_run_id":RUN,
    "source_container_directory":container,"container_artifact_sha256":source_hashes,
    "all_export_hashes_match":True,"read_only_postgres_transaction":True,
    "database_writes":False,"new_dag_runs_triggered":False,"screenshots_created":False,
    "ui_visual_verification":False,"live_run_checks":run_checks})
print(json.dumps({"dag_id":DAG,"runs":run_checks,"live_counts":counts,
    "export_directory":str(OUT),"all_export_hashes_match":True,"read_only":live["transaction_read_only"]},indent=2))
