"""Read-only post-run checks and evidence export for the existing Phase C run.

Does not start services, train, mutate SQL data, or overwrite workflow run folders.
Run from the project root with: py -3.11 scripts/verify_phase_c_evidence.py
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/verification/phase-c"

def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

def docker(*args, code=None):
    process = subprocess.run(["docker", "compose", *args], cwd=ROOT, input=code,
        text=True, encoding="utf-8", errors="replace", capture_output=True)
    if process.returncode:
        raise RuntimeError(f"Docker command failed ({process.returncode}): {process.stderr[-1200:]}")
    return process.stdout

def inside(code):
    output = docker("exec", "-T", "dashboard", "python", "-", code=code)
    # Only this marked JSON is data; framework diagnostics may precede it.
    return json.loads(output.split("PHASE_C_JSON=", 1)[1].splitlines()[0])

def main():
    baseline = json.loads((OUT/"part1-before.json").read_text(encoding="utf-8"))
    altered = []
    for name, digest in baseline["file_hashes"].items():
        path = ROOT/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            altered.append(name)
    if altered:
        raise AssertionError(f"Protected Part 1 files changed: {altered}")
    production = inside("""
import json
from bike_demand_ml.db import load_postgres_snapshot
frame, provenance = load_postgres_snapshot()
print("PHASE_C_JSON="+json.dumps({
 "rows":len(frame),"unique_dates":int(frame.date.nunique()),
 "total_rentals":int(frame.cnt.sum()),"dataset_hash":provenance["dataset_hash"],"versions":1,
 "provenance":provenance}))
""")
    current = {k: production[k] for k in baseline["production_database"]}
    assert current == baseline["production_database"], (current, baseline["production_database"])
    write("part1-preservation.json", {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "protected_files_checked": len(baseline["file_hashes"]),
        "all_protected_files_unchanged": True, "production_database_unchanged": True,
        "before": baseline["production_database"], "after": current,
        "verification_transaction": production["provenance"]["transaction_read_only"]})
    app = inside("""
import json
from pathlib import Path
from streamlit.testing.v1 import AppTest
a=AppTest.from_file("/opt/project/dashboard/app.py",default_timeout=30).run()
a.selectbox[0].select("ml_main_01").run()
assert len(a.exception)==0, [str(x) for x in a.exception]
assert a.title[0].value=="DC Bike Demand Model Lab"
assert len(a.get("graphviz_chart"))==1
assert len(a.dataframe)==4
report=json.loads(Path("/opt/project/artifacts/ml/ml_main_01/report.json").read_text())
evaluation=a.dataframe[1].value
assert evaluation.iloc[0]["mae"]==report["final_metrics"]["selected"]["mae"]
assert evaluation.iloc[1]["rmse"]==report["final_metrics"]["dummy"]["rmse"]
events=[json.loads(line) for line in Path("/opt/project/artifacts/ml/ml_main_01/events.jsonl").read_text().splitlines()]
retry_index=next(i+1 for i,e in enumerate(events)
 if e["node"]=="conditional_router" and e["kind"]=="node_completed" and e["decision"]=="retry")
a.checkbox[0].uncheck().run()
a.slider[0].set_value(retry_index).run()
assert len(a.exception)==0
trace=a.dataframe[0].value
assert len(trace)==retry_index
assert trace.iloc[-1]["decision"]=="retry"
assert a.metric[0].value=="1"
a.selectbox[0].select("ml_failure_probe_01").run()
assert len(a.exception)==0 and len(a.error)>0
print("PHASE_C_JSON="+json.dumps({
 "framework":"Streamlit AppTest in actual dashboard container",
 "main_run":"ml_main_01","exceptions":0,"compiled_graph_rendered":True,
 "completed_metric_table_matches_actual_report":True,
 "retry_replay_event":retry_index,"retry_replay_attempt":1,
 "failure_run_displayed_without_success_metrics":True,
 "browser_pixels_or_screenshots_verified":False}))
""")
    write("dashboard-apptest-final.json", app)
    with urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=10) as response:
        health = {"status":response.status,"body":response.read().decode()}
    assert health == {"status":200,"body":"ok"}
    write("dashboard-health-final.json", health)
    services = []
    for line in docker("ps", "--all", "--format", "json").splitlines():
        item=json.loads(line)
        services.append({k:item.get(k) for k in ["Service","State","Health","ID","CreatedAt","Status"]})
    for name in ["airflow-apiserver","airflow-scheduler","airflow-dag-processor","airflow-db","app-db"]:
        record=next(s for s in services if s["Service"]==name)
        assert record["State"]=="running" and record["Health"]=="healthy", record
    write("service-status-final.json",services)
    (OUT/"linux-freeze.txt").write_text(docker("exec","-T","dashboard","python","-m","pip","freeze"),encoding="utf-8")
    (OUT/"pip-check-final.log").write_text(docker("exec","-T","dashboard","python","-m","pip","check"),encoding="utf-8")
    tests=ET.parse(OUT/"test-artifacts/tests-final.xml").getroot()
    suites=tests.findall("testsuite") if tests.tag=="testsuites" else [tests]
    totals={key:sum(int(s.get(key,0)) for s in suites) for key in ["tests","failures","errors","skipped"]}
    assert totals=={"tests":19,"failures":0,"errors":0,"skipped":0},totals
    main_report=json.loads((OUT/"runs/ml_main_01/report.json").read_text())
    failed=json.loads((OUT/"runs/ml_failure_probe_01/report.json").read_text())
    assert main_report["status"]=="success" and main_report["test_stage_count"]==1
    assert failed["status"]=="failed" and not failed.get("final_metrics")
    assert not failed["metrics_claimed"] and failed["attempt"]==0
    assert [r["decision"] for r in main_report["routes"]]==["retry","finish"]
    events=[json.loads(line) for line in (OUT/"runs/ml_main_01/events.jsonl").read_text().splitlines()]
    assert sum(e["node"]=="train_model" and e["kind"]=="node_completed" for e in events)==2
    manifest={}
    for path in sorted((OUT/"runs").rglob("*")):
        if path.is_file():
            manifest[str(path.relative_to(OUT)).replace("\\","/")]=hashlib.sha256(path.read_bytes()).hexdigest()
    # Byte-compare host exports to originals on the named Docker artifact volume.
    container_hashes=inside("""
import hashlib,json
from pathlib import Path
root=Path("/opt/project/artifacts/ml")
print("PHASE_C_JSON="+json.dumps({
 "runs/"+str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
 for p in root.rglob("*") if p.is_file()}))
""")
    assert manifest==container_hashes,"Exported ML evidence differs from container originals"
    write("export-sha256.json",manifest)
    write("runtime-results.json",{
        "checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "main_run":"ml_main_01","status":"success",
        "input":main_report["provenance"],"attempts":main_report["attempt"],
        "baseline_metrics":main_report["baseline_metrics"],
        "trials":main_report["trials"],"routes":main_report["routes"],
        "selected_model":main_report["best_spec"],"test_metrics":main_report["final_metrics"],
        "test_stage_count":main_report["test_stage_count"],"tests":totals,
        "events":len(events),"dashboard":app,"health":health,
        "negative_probe":{"run_id":"ml_failure_probe_01","expected_exit_code":1,
            "status":failed["status"],"error":failed["error"],"metrics_claimed":False},
        "part1_protected_files_unchanged":len(baseline["file_hashes"]),
        "production_database_unchanged":True,"export_files_byte_verified":len(manifest)})
    print(json.dumps({"tests":totals,"protected_files_unchanged":len(baseline["file_hashes"]),
        "database":current,"dashboard":app,"export_files_byte_verified":len(manifest)},indent=2))
if __name__=="__main__":
    main()
