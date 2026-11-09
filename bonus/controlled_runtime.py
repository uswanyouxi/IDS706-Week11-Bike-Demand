"""Previously approved serial runtime; no original service is started/recreated."""
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/verification/bonus"
COMPOSE=["docker","compose","-f","compose.yaml","-f","compose.bonus.yaml","--profile","bonus"]
def command(args,log=None,code=None):
    result=subprocess.run(args,cwd=ROOT,input=code,text=True,encoding="utf-8",errors="replace",capture_output=True)
    if log:(OUT/log).write_text(result.stdout+result.stderr,encoding="utf-8")
    if result.returncode:raise RuntimeError(f"Command failed with exit {result.returncode}; see {log}")
    return result.stdout
def jsonfile(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
def database():
    code="""import json
from bike_demand_ml.db import load_postgres_snapshot
frame,meta=load_postgres_snapshot()
print(json.dumps({"rows":len(frame),"unique_dates":int(frame.date.nunique()),"total_rentals":int(frame.cnt.sum()),"dataset_hash":meta["dataset_hash"],"readonly":meta["transaction_read_only"],"provenance":meta}))"""
    return json.loads(command(["docker","compose","exec","-T","dashboard","python","-"],code=code))
def resources():
    host=int(command(["powershell","-NoProfile","-Command","(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"]).strip())
    code="from pathlib import Path; print(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))"
    guest=int(command(["docker","compose","exec","-T","dashboard","python","-c",code]).strip())
    state={"host_free_kib":host,"wsl_available_kib":guest,"checked_utc":datetime.now(timezone.utc).isoformat(),
        "order":"One serial worker; dashboard starts after all workers exit"}
    if host<1024*1024 or guest<3*1024*1024:
        jsonfile("resource-stop.json",state)
        raise RuntimeError("Memory below controlled-run floor; no new container started")
    return state
def main():
    branch=command(["git","-c","safe.directory="+ROOT.as_posix(),"branch","--show-current"]).strip()
    assert branch=="bonus/adaptive-multi-agent"
    before=database();jsonfile("database-before.json",before)
    steps=[("runtime-main.log",["run","--id","bonus_main_01"]),
           ("runtime-suite.log",["evaluate","--id","bonus_suite_01"]),
           ("runtime-classroom.log",["classroom","--id","classroom_probe_01"])]
    for log,args in steps:
        state=resources();jsonfile("preflight-"+log.replace(".log",".json"),state)
        print("Starting "+log,flush=True)
        line="umask 0002; exec python -m bike_demand_bonus.cli "+" ".join(args)
        command(COMPOSE+["run","--rm","--no-deps","bonus-runner","/bin/sh","-c",line],log)
        print("Completed "+log,flush=True)
    state=resources();jsonfile("preflight-integration.json",state)
    command(COMPOSE+["run","--rm","--no-deps","-e","BONUS_DB_INTEGRATION=1","bonus-runner",
        "python","-m","pytest","/opt/project/tests/bonus","-c","/opt/project/pytest.ini",
        "-p","no:cacheprovider","-q","-ra",
        "--junitxml=/opt/project/artifacts/bonus/bonus-integration-tests.xml"],"runtime-tests.log")
    after=database();jsonfile("database-after.json",after)
    assert before==after,"Application snapshot changed"
    # New UI only, after the serial workers have exited.
    resources()
    command(COMPOSE+["up","-d","--no-deps","bonus-dashboard"],"dashboard-startup.log")
    destination=OUT/"runtime";destination.mkdir(exist_ok=True)
    command(COMPOSE+["cp","bonus-dashboard:/opt/project/artifacts/bonus/.",str(destination)],"export.log")
    print("Controlled runtime complete; original services and SQL snapshot unchanged.",flush=True)
if __name__=="__main__":main()
