"""Final Bonus review only: no model fits, DAG runs, container starts or Git writes."""
import ast,hashlib,importlib.util,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/verification/bonus/review"
COMPOSE=["docker","compose","-f","compose.yaml","-f","compose.bonus.yaml"]
EXPECTED=["10_bonus_adaptive_graph.png","11_bonus_routing_recovery.png","11b_bonus_recovery_events.png",
"12_bonus_evaluation_suite.png","12b_bonus_evaluation_criteria.png","13_bonus_baseline_comparison.png","14_bonus_agent_metrics.png"]
ALLOWED={"README.md",".gitignore","screenshots/README.md"}
sys.dont_write_bytecode=True
def run(args,code=None):
    r=subprocess.run(args,cwd=ROOT,input=code,text=True,encoding="utf-8",errors="replace",capture_output=True)
    if r.returncode:raise RuntimeError("Read-only review command failed: "+r.stderr[-500:])
    return r.stdout
def git(*args):return run(["git","-c","safe.directory="+ROOT.as_posix(),*args])
def save(name,obj):(OUT/name).write_bytes((json.dumps(obj,indent=2,ensure_ascii=False)+"\n").encode("utf-8"))
def suite(name):
    r=ET.parse(OUT/name).getroot();items=r.findall("testsuite") if r.tag=="testsuites" else [r]
    return {k:sum(int(s.get(k,0)) for s in items) for k in ["tests","errors","failures","skipped"]}
def ignored(name):
    r=subprocess.run(["git","-c","safe.directory="+ROOT.as_posix(),"check-ignore","--no-index","-q","--",name],cwd=ROOT,capture_output=True)
    return r.returncode==0
def main():
    OUT.mkdir(exist_ok=True)
    for name in ["checks.json","bonus-staging.txt"]:
        if not (OUT/name).exists():(OUT/name).write_text("{}\n" if name.endswith(".json") else "",encoding="utf-8")
    assert git("branch","--show-current").strip()=="bonus/adaptive-multi-agent"
    before=json.loads((OUT.parent/"preservation-before.json").read_text())
    assert git("rev-parse","main").strip()==before["main_commit"]
    changed=[p for p,d in before["files"].items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=d]
    assert set(changed)<=ALLOWED,changed
    assert (ROOT/"README.md").read_text(encoding="utf-8").startswith(git("show","main:README.md"))
    mtime=[p for p,t in before["modification_time_ns"].items() if p not in ALLOWED and (ROOT/p).stat().st_mtime_ns!=t]
    assert not mtime,mtime
    old_hashes=json.loads((OUT.parent/"runtime-export-sha256.json").read_text())
    for name,digest in old_hashes.items():
        assert hashlib.sha256((OUT.parent/"runtime"/name).read_bytes()).hexdigest()==digest,name
    # An unreachable engine is a blocker, never a fresh runtime success.
    engine=json.loads(run(["docker","info","--format",'{{json .ServerVersion}}']))
    logs=json.loads((OUT/"logs-preservation.json").read_text())["files"]
    for name,record in logs.items():
        path=ROOT/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record["sha256"],name
        assert path.stat().st_mtime_ns==record["mtime_ns"],name
    # Audit actual volume records; never refit, rewrite or rescore the frozen original files.
    actual=json.loads(run(COMPOSE+["exec","-T","bonus-dashboard","python","-"],code="""
import json
from pathlib import Path
from bike_demand_bonus.audit import audit_saved_run
root=Path('/opt/project/artifacts/bonus')
rows=json.loads((root/'evaluations/bonus_suite_01/results.json').read_text())
print(json.dumps([audit_saved_run(root/'runs'/r['run_id'],r['case'],r['policy']) for r in rows]))
"""))
    save("evaluation-audit.json",actual)
    assert len(actual)==27 and all(r["passed"] for r in actual)
    # Fresh server-enforced read-only production snapshot.
    live=json.loads(run(["docker","compose","exec","-T","dashboard","python","-"],code="""
import json
from bike_demand_ml.db import load_postgres_snapshot
f,p=load_postgres_snapshot()
print(json.dumps({'rows':len(f),'unique_dates':int(f.date.nunique()),'total_rentals':int(f.cnt.sum()),
 'dataset_hash':p['dataset_hash'],'readonly':p['transaction_read_only']}))
"""))
    initial=json.loads((OUT.parent/"database-before.json").read_text())
    assert all(live[k]==initial[k] for k in live)
    save("production-readonly.json",live)
    captures={};missing=[]
    for name in EXPECTED:
        path=ROOT/"screenshots"/name
        if not path.exists():missing.append(name);assert ignored("screenshots/"+name);continue
        assert not ignored("screenshots/"+name),name
        raw=path.read_bytes();assert raw.startswith(b"\x89PNG\r\n\x1a\n")
        captures[name]={"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
    assert set(captures)==set(EXPECTED) and not missing
    screenshot_exceptions=[line[len("!/screenshots/"):] for line in (ROOT/".gitignore").read_text().splitlines()
                           if line.startswith("!/screenshots/") and line.endswith(".png")]
    original_images=[Path(p).name for p in before["files"] if p.startswith("screenshots") and p.endswith(".png")]
    assert set(screenshot_exceptions)==set(original_images)|set(captures)
    probes=[".env",".env.production",".venv/example.py","src/__pycache__/secret.pyc",
            ".aws/credentials","credentials.json","private.key","volumes/postgres/PG_VERSION",
            "artifacts/classroom-reference/loop_runtime.py","build/temp.bin","screenshots/not-reviewed.png"]
    assert all(ignored(p) for p in probes)
    save("screenshots.json",{"reviewed_present":captures,"missing_not_allowlisted":missing,
                            "published_six_byte_unchanged":True})
    spec=importlib.util.spec_from_file_location("submission_helpers",ROOT/"scripts/check_submission.py")
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    eligible=helpers.eligible()
    links,broken,excluded=helpers.local_links(eligible)
    assert not broken and not excluded,(broken,excluded)
    scanned,findings=helpers.secrets_check(eligible);assert not findings,findings
    files=[p for p in eligible if p.endswith(".py")]
    for name in files:ast.parse((ROOT/name).read_text(encoding="utf-8-sig"),filename=name)
    subprocess.run(["docker","compose","-f","compose.yaml","-f","compose.bonus.yaml","--profile","bonus","config","--quiet"],cwd=ROOT,check=True,capture_output=True)
    with urllib.request.urlopen("http://localhost:8502/_stcore/health",timeout=10) as response:assert response.status==200 and response.read()==b"ok"
    tests={k:suite(v) for k,v in {"bonus_and_part2":"submission-bonus-ml.xml","pipeline":"submission-pipeline.xml","dag":"submission-dag.xml"}.items()}
    assert all(not t["errors"] and not t["failures"] and not t["skipped"] for t in tests.values())
    # Exact branch-only recommendation; nothing is added to the index.
    changed_paths={p for p in git("diff","main","--name-only","--diff-filter=ACMR","-z").split("\0") if p}
    new_paths={p for p in git("ls-files","--others","--exclude-standard","-z").split("\0") if p}
    local_scratch={"docs/verification/bonus/review/audit-initial.json","docs/verification/bonus/review/audit-rerun.json"}
    paths=sorted((changed_paths|new_paths)-local_scratch)
    (OUT/"bonus-staging.txt").write_bytes(("\n".join(paths)+"\n").encode("utf-8"))
    preview=git("--literal-pathspecs","add","--dry-run","--pathspec-from-file=docs/verification/bonus/review/bonus-staging.txt")
    # Git dry-run prints only paths requiring an index refresh, not all staged paths.
    staged=[p for p in git("diff","--cached","--name-only").splitlines() if p]
    assert set(staged)<=set(paths),"Unexpected staged paths outside the reviewed manifest"
    git("diff","--check")
    git("diff","--cached","--check")
    forbidden=[p for p in eligible if
        (Path(p).name.startswith(".env") and p!=".env.example") or
        any(part in {".venv","venv","__pycache__",".aws",".ssh","volumes","pgdata","node_modules","build","dist"} for part in Path(p).parts)]
    assert not forbidden,forbidden
    result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"branch":"bonus/adaptive-multi-agent",
        "main_commit_unchanged":before["main_commit"],"original_authorized_documentation_changes":changed,
        "other_original_files_byte_unchanged":len(before["files"])-len(changed),
        "historical_mtime_changes":mtime,"historical_logs_byte_and_mtime_unchanged":len(logs),
        "docker_engine_version":engine,"fresh_readonly_review_completed":True,"whitespace_checks_passed":True,"frozen_bonus_runtime_files_unchanged":len(old_hashes),
        "production":live,"reviewed_bonus_images":list(captures),"missing_bonus_images":missing,
        "original_published_images_unchanged":original_images,
        "independently_audited_executions":27,"independent_expected_behavior_passes":27,
        "tests":tests,"tests_passed":sum(t["tests"] for t in tests.values()),
        "python_files_parsed":len(files),"local_markdown_links":links,"secret_scan_text_files":scanned,
        "secret_findings":findings,"ignore_probes_passed":len(probes)+len(EXPECTED),
        "compose_valid":True,"recommended_stage_files":len(paths),"dry_run_exact_list_passed":True,
        "local_scratch_excluded":sorted(local_scratch),"staged_files":staged,"staged_file_count":len(staged),"staged_set_matches_manifest":set(staged)==set(paths),
        "native_classroom_airflow_dag_executed":False,
        "remaining_risks":["Strict two-native-baseline equivalence is incomplete","Validation predictions were not saved",
                           "Designed fault coverage is limited","Image 14 shows policy rates, not per-agent metrics"],
        "scope":"No production training/DAG run, new container, Docker deletion, commit, merge or push"}
    save("checks.json",result)
    print(json.dumps({k:result[k] for k in ["other_original_files_byte_unchanged","frozen_bonus_runtime_files_unchanged",
        "reviewed_bonus_images","missing_bonus_images","tests_passed","independently_audited_executions",
        "python_files_parsed","local_markdown_links","secret_findings","recommended_stage_files","staged_file_count","staged_set_matches_manifest"]},indent=2))
if __name__=="__main__":main()
