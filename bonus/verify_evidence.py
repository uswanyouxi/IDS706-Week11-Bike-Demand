"""Read-only evidence audit; writes only new bonus verification summaries."""
import ast,csv,hashlib,importlib.util,json,math,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/verification/bonus"
RUNTIME=OUT/"runtime"
COMPOSE=["docker","compose","-f","compose.yaml","-f","compose.bonus.yaml"]
sys.dont_write_bytecode=True

def run(args,code=None):
    value=subprocess.run(args,cwd=ROOT,input=code,text=True,encoding="utf-8",errors="replace",capture_output=True)
    if value.returncode:raise RuntimeError("Audit command failed: "+value.stderr[-600:])
    return value.stdout
def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def git(*args):return run(["git","-c","safe.directory="+ROOT.as_posix(),*args]).strip()
def junit(name):
    root=ET.parse(OUT/name).getroot()
    suites=root.findall("testsuite") if root.tag=="testsuites" else [root]
    return {k:sum(int(s.get(k,0)) for s in suites) for k in ["tests","errors","failures","skipped"]}
def main():
    if not (OUT/"final-checks.json").exists():save("final-checks.json",{"status":"audit_pending"})
    assert git("branch","--show-current")=="bonus/adaptive-multi-agent"
    before=json.loads((OUT/"preservation-before.json").read_text())
    assert git("rev-parse","main")==before["main_commit"]
    altered=[name for name,digest in before["files"].items()
        if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    assert set(altered)<= {"README.md"},altered
    if "README.md" in altered:
        original=run(["git","-c","safe.directory="+ROOT.as_posix(),"show","main:README.md"])
        assert (ROOT/"README.md").read_text(encoding="utf-8").startswith(original)
    timestamp_changed=[name for name,value in before["modification_time_ns"].items()
        if name!="README.md" and (ROOT/name).stat().st_mtime_ns!=value]
    assert not timestamp_changed,timestamp_changed
    db_before=json.loads((OUT/"database-before.json").read_text())
    db_after=json.loads((OUT/"database-after.json").read_text())
    assert db_before==db_after
    assert db_after["rows"]==db_after["unique_dates"]==731 and db_after["total_rentals"]==3292679
    assert db_after["readonly"]=="on"
    # Reassess all recorded routes with the strengthened oracle; do not refit.
    reassess=run(COMPOSE+["exec","-T","bonus-dashboard","python","-"],code="""
import json
from pathlib import Path
from bike_demand_bonus.evaluation import assess
root=Path('/opt/project/artifacts/bonus')
rows=json.loads((root/'evaluations/bonus_suite_01/results.json').read_text())
checks=[]
for row in rows:
 report=json.loads((root/'runs'/row['run_id']/'report.json').read_text())
 grade=assess(report,row['case'],row['policy'])
 checks.append({'run_id':row['run_id'],**grade})
print(json.dumps(checks))
""")
    reassess=json.loads(reassess);assert len(reassess)==27 and all(row["passed"] for row in reassess)
    save("evaluation-reassessment.json",reassess)
    runs=[]
    for folder in sorted((RUNTIME/"runs").iterdir()):
        report=json.loads((folder/"report.json").read_text())
        if report["status"]=="success":
            rows=list(csv.DictReader((folder/"test_predictions.csv").open()))
            assert len(rows)==184 and report["test_stage_count"]==1
            for label,column in [("selected","prediction"),("dummy","dummy_prediction")]:
                errors=[float(r[column])-float(r["observed_cnt"]) for r in rows]
                observed=[float(r["observed_cnt"]) for r in rows]
                mean=sum(observed)/184
                values={"mae":sum(abs(e) for e in errors)/184,"rmse":math.sqrt(sum(e*e for e in errors)/184),
                        "r2":1-sum(e*e for e in errors)/sum((v-mean)**2 for v in observed)}
                for name,value in values.items():
                    assert math.isclose(value,report["final_metrics"][label][name],rel_tol=1e-12)
        else:assert not report.get("final_metrics")
        runs.append({"run_id":folder.name,"status":report["status"]})
    assert len(runs)==28
    # Actual container UI, including original Part 2 navigation and event replay.
    ui=json.loads(run(COMPOSE+["exec","-T","bonus-dashboard","python","-"],code="""
import json
from pathlib import Path
from streamlit.testing.v1 import AppTest
a=AppTest.from_file('/opt/project/bonus/dashboard.py',default_timeout=30).run()
a.selectbox[0].select('bonus_main_01').run()
assert not a.exception
assert len(a.get('graphviz_chart'))==1
m=a.dataframe[1].value
assert abs(float(m.loc[m.model=='selected','rmse'].iloc[0])-1202.3613050409385)<1e-8
a.checkbox[0].uncheck().run();a.slider[0].set_value(24).run()
assert not a.exception and a.dataframe[0].value.iloc[-1]['next_node']=='feature_refinement'
a.selectbox[0].select('bonus_suite_01_transient_database_adaptive').run()
a.slider[0].set_value(8).run()
assert not a.exception and a.dataframe[0].value.iloc[-1]["next_node"]=="data_loader"
assert any(x.label=='Recoveries' and int(x.value)==1 for x in a.metric)
assert len(a.dataframe[-1].value)==27
summary=a.dataframe[-2].value
assert set(summary['policy'])=={'adaptive','fixed_port','simple_port'}
a.switch_page('/opt/project/dashboard/app.py').run()
assert not a.exception and a.title[0].value=='DC Bike Demand Model Lab'
print(json.dumps({'application_exceptions':0,'compiled_graph_rendered':True,
 'real_metrics_match':True,'dynamic_event_24_verified':True,'real_recovery_verified':True,
 'evaluation_rows':27,'comparison_policies':3,'original_part2_navigation_verified':True,
 'browser_pixels_verified':False,'screenshots_created':False}))
"""))
    save("dashboard-checks.json",ui)
    with urllib.request.urlopen("http://localhost:8502/_stcore/health",timeout=10) as response:
        assert response.status==200 and response.read()==b"ok"
    # Safe checks: import the existing pure helper functions, never run its report writer.
    spec=importlib.util.spec_from_file_location("submission_audit",ROOT/"scripts/check_submission.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    candidates=module.eligible()
    links,broken,ignored=module.local_links(candidates)
    assert not broken and not ignored,(broken,ignored)
    scanned,findings=module.secrets_check(candidates);assert not findings,findings
    pyfiles=[p for p in candidates if p.endswith(".py")]
    for name in pyfiles:ast.parse((ROOT/name).read_text(encoding="utf-8"),filename=name)
    freeze=run(COMPOSE+["exec","-T","bonus-dashboard","python","-m","pip","freeze"])
    (OUT/"linux-freeze.txt").write_text(freeze,encoding="utf-8")
    tests={name:junit(file) for name,file in [
        ("bonus","final-bonus-tests.xml"),("part1_unit","original-pipeline-regression.xml"),
        ("part2_unit","original-ml-regression.xml"),("original_dag_import","original-dag-import.xml")]}
    assert all(not t["failures"] and not t["errors"] and not t["skipped"] for t in tests.values())
    services=[json.loads(s) for s in run(COMPOSE+["ps","--all","--format","json"]).splitlines()]
    state=[{k:s.get(k) for k in ["Service","ID","State","Health","CreatedAt"]} for s in services]
    assert all(next(s for s in state if s["Service"]==name)["Health"]=="healthy"
        for name in ["airflow-apiserver","airflow-scheduler","airflow-dag-processor","airflow-db","app-db"])
    save("service-status-final.json",state)
    manifest={p.relative_to(RUNTIME).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in RUNTIME.rglob("*") if p.is_file()}
    remote=json.loads(run(COMPOSE+["exec","-T","bonus-dashboard","python","-"],code="""
import hashlib,json
from pathlib import Path
root=Path('/opt/project/artifacts/bonus')
print(json.dumps({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
 for p in root.rglob('*') if p.is_file()}))
"""))
    assert manifest==remote,"Exported bonus evidence differs from the actual named volume"
    save("runtime-export-sha256.json",manifest)
    summary={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"branch":git("branch","--show-current"),
        "main_commit_unchanged":before["main_commit"],"original_files_checked":len(before["files"]),
        "original_files_changed":altered,"historical_timestamps_changed":timestamp_changed,
        "database_unchanged":True,"database_rows":731,"suite_executions":27,"suite_expected_passes":27,
        "suite_incorrect_routes":sum(r["incorrect_routes"] for r in reassess),
        "runtime_runs":runs,"tests":tests,"tests_passed":sum(t["tests"] for t in tests.values()),
        "python_files_parsed":len(pyfiles),"local_documentation_links":links,
        "secret_scan_text_files":scanned,"secret_findings":findings,
        "dashboard":ui,"runtime_export_files":len(manifest),
        "strict_classroom_airflow_comparison_complete":False,
        "limitation":"Native Airflow DAG not executed; native classification results and regression ports are distinct.",
        "staged_files":git("diff","--cached","--name-only").splitlines()}
    save("final-checks.json",summary)
    print(json.dumps({k:summary[k] for k in ["branch","original_files_checked","original_files_changed",
        "historical_timestamps_changed","database_unchanged","suite_executions","suite_expected_passes",
        "tests_passed","python_files_parsed","local_documentation_links","secret_findings","staged_files"]},indent=2))
if __name__=="__main__":main()
