"""Check the final submission without staging or running production workflows.

Standard library only. Run from anywhere:
  py -3.11 scripts/check_submission.py --write-manifest  # deliberate refresh
  py -3.11 scripts/check_submission.py                   # check exact list
"""
import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"docs/verification/final-submission"
MANIFEST = ROOT/"submission/commit-files.txt"
SCREENSHOTS = [
    "01_airflow_dag_success.png", "02_airflow_graph.png",
    "06_langgraph_live_execution.png", "07_langgraph_conditional_retry.png",
    "08_regression_evaluation.png", "09_model_comparison_charts.png",
]

def git(*args, input_bytes=None, check=True):
    result = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT, input=input_bytes, capture_output=True)
    if check and result.returncode:
        raise RuntimeError("Read-only Git inspection failed")
    return result

def eligible():
    raw=git("ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
    return sorted(set(p.decode("utf-8") for p in raw.split(b"\0") if p))

def decode(raw):
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8-sig", errors="replace")

def local_links(paths):
    broken=[]
    ignored=[]
    count=0
    candidates=set(paths)
    for name in paths:
        if not name.endswith(".md"):
            continue
        path=ROOT/name
        content=path.read_text(encoding="utf-8-sig")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
            target=target.strip()
            if target.startswith("<"):
                target=target[1:target.index(">")]
            else:
                target=target.split(' "',1)[0]
            if "://" in target or target.startswith(("#","mailto:")):
                continue
            target=unquote(target.split("#",1)[0])
            if not target:
                continue
            resolved=(path.parent/target).resolve()
            count+=1
            if not resolved.exists():
                broken.append({"document":name,"target":target})
                continue
            try:
                relative=resolved.relative_to(ROOT).as_posix()
            except ValueError:
                broken.append({"document":name,"target":"outside project"})
                continue
            if resolved.is_file() and relative not in candidates:
                ignored.append({"document":name,"target":relative})
            if resolved.is_dir() and not any(p.startswith(relative+"/") for p in candidates):
                ignored.append({"document":name,"target":relative+"/"})
    return count,broken,ignored

def secrets_check(paths):
    # Exact local values never leave this process or appear in the report.
    values=[]
    env=ROOT/".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key,value=line.split("=",1)
                value=value.strip().strip("'\"")
                if any(part in key.upper() for part in ["PASSWORD","SECRET","FERNET","TOKEN","PRIVATE_KEY"]) and len(value)>=12:
                    values.append(value)
    signatures={
        "private_key":re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "github_token":re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
        "aws_access_key":re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        "google_api_key":re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b"),
        "slack_token":re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    }
    findings=[]
    text_files=0
    for name in paths:
        raw=(ROOT/name).read_bytes()
        # Include non-text candidates in the exact-value scan.
        if any(value.encode("utf-8") in raw or value.encode("utf-16-le") in raw for value in values):
            findings.append({"file":name,"kind":"actual_local_credential"})
        if raw.startswith(b"\x89PNG\r\n\x1a\n") or name.endswith((".joblib",".pkl",".pickle")):
            continue
        text_files+=1
        text=decode(raw)
        for kind,pattern in signatures.items():
            if pattern.search(text):
                findings.append({"file":name,"kind":kind})
    return text_files,findings

def junit(name):
    tree=ET.parse(OUT/name).getroot()
    suites=tree.findall("testsuite") if tree.tag=="testsuites" else [tree]
    return {key:sum(int(s.get(key,0)) for s in suites)
            for key in ["tests","failures","errors","skipped"]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifest",action="store_true")
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    report_path=OUT/"checks.json"
    if args.write_manifest:
        if not report_path.exists():
            report_path.write_text("{}\n",encoding="utf-8")
        if not MANIFEST.exists():
            MANIFEST.write_text("",encoding="utf-8")
    paths=eligible()
    if args.write_manifest:
        MANIFEST.write_text("\n".join(paths)+"\n",encoding="utf-8")
    assert MANIFEST.exists(),"Generate and review submission/commit-files.txt first"
    manifest=MANIFEST.read_text(encoding="utf-8").splitlines()
    assert manifest==paths,"Git-eligible files differ from the reviewed manifest; refresh deliberately"
    protected=json.loads((OUT/"before-sha256.json").read_text(encoding="utf-8"))
    integrity={}
    for category,items in protected.items():
        changed=[name for name,digest in items.items()
                 if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
        assert not changed,f"Verified source/evidence changed: {changed}"
        integrity[category]={"files":len(items),"unchanged":True}
    python_files=[name for name in paths if name.endswith(".py")]
    for name in python_files:
        ast.parse((ROOT/name).read_text(encoding="utf-8-sig"),filename=name)
    count,broken,ignored=local_links(paths)
    scanned,findings=secrets_check(paths)
    ignored_probes=[
        ".env",".env.production",".env.compose-check",".venv/Lib/example.py",
        "venv/example.py","src/__pycache__/example.pyc",".pytest_cache/example",
        ".aws/credentials",".ssh/id_rsa","credentials.json","client_secret_test.json",
        "token_local.json","private.key","private.pem","volumes/postgres/PG_VERSION",
        "postgres-data/PG_VERSION","pgdata/PG_VERSION","docker-data/ext4.vhdx",
        "local.dump","data/raw/day.csv","artifacts/ml/new/model.joblib",
        "build/example.py","dist/package.whl","node_modules/package/test.js",
        "screenshots/unreviewed.png","screenshots/private.txt","README_FIRST.md",
        "prompts/04_audit_bonus.txt"]
    ignore_failures=[name for name in ignored_probes
                     if git("check-ignore","--no-index","-q","--",name,check=False).returncode!=0]
    required=[".env.example","README.md","Dockerfile.airflow","Dockerfile.ml","compose.yaml",
        "dags/dc_bike_weather.py","src/bike_demand_ml/graph.py","tests/ml/test_policy.py"]
    required += ["screenshots/"+name for name in SCREENSHOTS]
    assert all(name in paths for name in required),"Required submission file missing/ignored"
    forbidden=[name for name in paths if
        (Path(name).name.startswith(".env") and name!=".env.example")
        or any(part in {".venv","venv","__pycache__",".aws",".ssh","volumes","pgdata","node_modules","build","dist"} for part in Path(name).parts)
        or name.endswith((".pyc",".pem",".key",".pfx",".p12",".vhdx",".sqlite",".dump"))]
    screenshots={}
    actual=sorted(name for name in paths if name.startswith("screenshots/") and name.endswith(".png"))
    assert actual==sorted("screenshots/"+name for name in SCREENSHOTS),"Screenshot allowlist mismatch"
    for name in actual:
        raw=(ROOT/name).read_bytes()
        assert raw[:8]==b"\x89PNG\r\n\x1a\n","Invalid PNG"
        width,height=struct.unpack(">II",raw[16:24])
        screenshots[name]={"width":width,"height":height,"sha256":hashlib.sha256(raw).hexdigest()}
    main_run=ROOT/"docs/verification/phase-c/runs/ml_main_01"
    result=json.loads((main_run/"report.json").read_text(encoding="utf-8"))
    with (main_run/"test_predictions.csv").open(encoding="utf-8",newline="") as handle:
        predictions=list(csv.DictReader(handle))
    for label,column in [("selected","selected_prediction"),("dummy","dummy_prediction")]:
        errors=[float(row[column])-float(row["observed_cnt"]) for row in predictions]
        actual_metrics={"mae":sum(abs(e) for e in errors)/len(errors),
                        "rmse":math.sqrt(sum(e*e for e in errors)/len(errors))}
        assert all(math.isclose(value,result["final_metrics"][label][metric],rel_tol=1e-12)
                   for metric,value in actual_metrics.items()),"Saved metrics do not match predictions"
    negative=sum(float(row["selected_prediction"])<0 for row in predictions)
    assert len(predictions)==184 and negative==1
    tests={label:junit(name) for label,name in [
        ("pipeline_unit","host-unit-tests.xml"),("ml_unit","ml-tests.xml"),("real_dag_import","dag-import.xml")]}
    assert [tests[name]["tests"] for name in tests]==[39,19,1]
    assert all(not t["failures"] and not t["errors"] and not t["skipped"] for t in tests.values())
    for profile in [[],["--profile","ml"]]:
        proc=subprocess.run(["docker","compose",*profile,"config","--quiet"],
            cwd=ROOT,capture_output=True)
        assert proc.returncode==0,"Compose config validation failed"
    staged=git("diff","--cached","--name-only","-z").stdout.split(b"\0")
    staged=[name.decode("utf-8") for name in staged if name]
    categories={}
    for name in paths:
        group=name.split("/",1)[0] if "/" in name else "(root)"
        categories[group]=categories.get(group,0)+1
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "manifest":"submission/commit-files.txt","recommended_files":len(paths),
        "category_file_counts":categories,"total_candidate_bytes":sum((ROOT/name).stat().st_size for name in paths),
        "preservation":integrity,"python_files_ast_parsed":len(python_files),
        "local_markdown_targets_checked":count,"broken_local_links":broken,
        "linked_files_excluded_from_git":ignored,"secret_scan_text_files":scanned,
        "secret_findings":findings,"forbidden_submission_paths":forbidden,
        "ignore_probes":len(ignored_probes),"ignore_probe_failures":ignore_failures,
        "screenshots":screenshots,"tests":tests,"total_tests_passed":59,
        "compose_default_and_ml_profiles_valid":True,
        "saved_predictions_match_metrics":True,"negative_test_predictions":negative,
        "staged_files_observed":staged,"production_training_or_dag_runs_performed":False,
        "scope":"Local checks only; no Git index mutation or push. ML tests fit synthetic fixtures."}
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["recommended_files","category_file_counts",
        "preservation","python_files_ast_parsed","local_markdown_targets_checked",
        "broken_local_links","linked_files_excluded_from_git","secret_scan_text_files",
        "secret_findings","forbidden_submission_paths","ignore_probe_failures",
        "total_tests_passed","negative_test_predictions","staged_files_observed"]},indent=2))
    assert not (broken or ignored or findings or forbidden or ignore_failures),"Submission checks found issues; see checks.json"
if __name__=="__main__":
    main()
