"""Guarded host driver for the explicitly approved native-only Compose project."""
import argparse,base64,ctypes,hashlib,json,os,re,secrets,shutil,subprocess,sys,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from isolation import validate_config
sys.dont_write_bytecode=True
if hasattr(sys.stdout,"reconfigure"):sys.stdout.reconfigure(encoding="utf-8")
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PROJECT="ids706-classroom-native-v1"
LOCAL=ROOT/"artifacts/native-classroom-local"
ENV=LOCAL/".env"
OUT=ROOT/"docs/verification/bonus/native-classroom/runtime/native_classroom_01"
DAG="solution_baseline_prep"
RUN="native_prep_01"
def stamp():return datetime.now(timezone.utc).isoformat()
def save(path,obj):
    with Path(path).open("x",encoding="utf-8") as f:json.dump(obj,f,indent=2,ensure_ascii=True);f.write("\n")
def values():
    return dict(line.split("=",1) for line in ENV.read_text().splitlines() if "=" in line and not line.startswith("#"))
def redact(text):
    if ENV.exists():
        for value in values().values():text=text.replace(value,"[REDACTED]")
    return text
def command(args,*,input_text=None,check=True):
    r=subprocess.run([str(a) for a in args],cwd=ROOT,input=input_text,text=True,encoding="utf-8",errors="replace",capture_output=True)
    if check and r.returncode:raise RuntimeError(redact(r.stderr[-1500:]))
    return r
def git(*args):return command(["git","-c","safe.directory="+ROOT.as_posix(),*args]).stdout
def compose(*args):return ["docker","compose","--project-name",PROJECT,"--env-file",str(ENV),"-f",str(HERE/"compose.yaml"),*args]
def runlog(name,args):
    original=name;attempt=1
    while (OUT/(name+".log")).exists() or (OUT/(name+"-command.json")).exists():
        attempt+=1;name=original+"-attempt"+str(attempt)
    path=OUT/(name+".log")
    save(OUT/(name+"-command.json"),{"at_utc":stamp(),"command":list(map(str,args)),"scope":"Native project only"})
    with path.open("x",encoding="utf-8") as f:
        p=subprocess.Popen(list(map(str,args)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
        for line in p.stdout:
            line=redact(line);f.write(line);f.flush();print(line,end="",flush=True)
        p.stdout.close()
        result=p.wait()
    if result:raise RuntimeError("Native command failed: "+name+" (exit "+str(result)+")")
def inspect_existing():
    names=command(["docker","ps","--filter","label=com.docker.compose.project=ids706-bike-demand","--format","{{.Names}}"]).stdout.splitlines()
    return {name:json.loads(command(["docker","inspect","--format",'{"id":"{{.Id}}","started_at":"{{.State.StartedAt}}","restart_count":{{.RestartCount}}}',name]).stdout) for name in names}
def production():
    code="""import json
from bike_demand_ml.db import load_postgres_snapshot
f,p=load_postgres_snapshot()
print('@@JSON@@'+json.dumps({'rows':len(f),'unique_dates':int(f.date.nunique()),'total_rentals':int(f.cnt.sum()),'dataset_hash':p['dataset_hash'],'readonly':p['transaction_read_only']}))
"""
    raw=command(["docker","compose","exec","-T","dashboard","python","-"],input_text=code).stdout
    return json.loads(raw.split("@@JSON@@",1)[1])
def resources(stage):
    class MemoryStatus(ctypes.Structure):
        _fields_=[("length",ctypes.c_uint32),("load",ctypes.c_uint32)]+[(name,ctypes.c_uint64) for name in
            ["total_physical","available_physical","total_pagefile","available_pagefile","total_virtual","available_virtual","available_extended"]]
    memory=MemoryStatus();memory.length=ctypes.sizeof(memory)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)),"Windows memory query failed"
    host_available=memory.available_physical/1024**3
    disk_free=shutil.disk_usage("D:/").free
    guest=command(["docker","exec","ids706-bike-demand-airflow-scheduler-1","cat","/proc/meminfo"]).stdout
    available=int(next(s for s in guest.splitlines() if s.startswith("MemAvailable:")).split()[1])*1024
    result={"at_utc":stamp(),"stage":stage,"host_available_gib":host_available,
        "guest_available_gib":available/1024**3,"drive_available_gib":disk_free/1024**3}
    suffix=len(list(OUT.glob("resources-*.json")))
    save(OUT/("resources-"+str(suffix).zfill(2)+"-"+stage+".json"),result)
    print("Resource gate: "+json.dumps(result),flush=True)
    assert result["host_available_gib"]>=2.5,"Host memory below approved startup gate; do not force"
    minimum=1.5 if stage in {"airflow","loop","viewer","tests"} else 4
    assert result["guest_available_gib"]>=minimum,"Guest memory below native stage gate"
    assert result["drive_available_gib"]>=25,"Docker host drive headroom below gate"
    before=json.loads((OUT/"existing-services-before.json").read_text())
    assert inspect_existing()==before,"An existing service changed; investigate before continuing"
    return result
def config(output="compose-isolation.json"):
    raw=command(compose("config","--format","json")).stdout
    cfg=json.loads(raw)
    validate_config(cfg,ROOT)
    assert cfg["name"]==PROJECT
    for name,s in cfg["services"].items():
        assert name.startswith("native-")
        assert s.get("restart","no")=="no"
        for p in s.get("ports",[]):assert p["host_ip"]=="127.0.0.1" and int(p["published"]) in {8088,8503}
        for v in s.get("volumes",[]):
            if v["type"]=="volume":assert v["source"].startswith("native-")
            if v["type"]=="bind":assert v["read_only"] is True
        assert "APP_DB_PASSWORD" not in s.get("environment",{})
    save(OUT/output,{"name":cfg["name"],"services":{k:{field:v.get(field) for field in ["image","mem_limit","cpus","ports","volumes"]} for k,v in cfg["services"].items()},"new_volumes":list(cfg["volumes"]),"no_existing_networks_or_volumes":True})
def prepare():
    assert git("branch","--show-current").strip()=="bonus/adaptive-multi-agent"
    assert not command(["docker","ps","--all","--filter","label=com.docker.compose.project="+PROJECT,"--format","{{.Names}}"]).stdout.strip(),"Native project already exists; do not reinitialize or delete its evidence"
    assert not command(["docker","volume","ls","--filter","label=com.docker.compose.project="+PROJECT,"--format","{{.Name}}"]).stdout.strip(),"Native volumes already exist; preserved rather than reused for fresh preparation"
    OUT.mkdir(parents=True,exist_ok=False)
    LOCAL.mkdir(exist_ok=True)
    if not ENV.exists():
        with ENV.open("x",encoding="utf-8") as f:
            f.write("NATIVE_DB_PASSWORD="+secrets.token_hex(24)+"\n")
            f.write("NATIVE_ADMIN_PASSWORD="+secrets.token_hex(24)+"\n")
            f.write("NATIVE_WEB_SECRET="+secrets.token_hex(32)+"\n")
            f.write("NATIVE_FERNET_KEY="+base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()+"\n")
    assert command(["git","-c","safe.directory="+ROOT.as_posix(),"check-ignore","--no-index","-q",str(ENV)],check=False).returncode==0
    pins=json.loads((HERE/"source-pins.json").read_text())
    cache=ROOT/"artifacts/native-classroom-reference"
    for name,record in pins["source_files"].items():
        path=cache/name
        if not path.exists():
            with urllib.request.urlopen("https://raw.githubusercontent.com/"+pins["repository"]+"/"+pins["commit"]+"/"+name,timeout=40) as response:data=response.read()
            assert hashlib.sha256(data).hexdigest()==record["sha256"]
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record["sha256"],name
    tracked=[p for p in git("ls-files","-z").split("\0") if p and (ROOT/p).is_file()]
    tracked+=[".env"]
    snapshot={p:{"sha256":hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),"mtime_ns":(ROOT/p).stat().st_mtime_ns} for p in tracked}
    save(OUT/"workspace-before.json",snapshot)
    save(OUT/"git-before.json",{"head":git("rev-parse","HEAD").strip(),"main":git("rev-parse","main").strip(),"status":git("status","--short"),"staged":git("diff","--cached","--name-only")})
    save(OUT/"existing-services-before.json",inspect_existing())
    save(OUT/"production-before.json",production())
    config()
    resources("prepare")
    print("Native-only setup and preservation snapshots ready; credentials remain in ignored "+str(ENV),flush=True)
def state(service):
    identifier=command(compose("ps","--all","--quiet",service)).stdout.strip()
    if not identifier:return {}
    return json.loads(command(["docker","inspect","--format","{{json .State}}",identifier]).stdout)
def wait(service,kind,seconds=240):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        s=state(service);status=s.get("Status");health=s.get("Health",{}).get("Status")
        print(service+": "+str(status)+" / "+str(health),flush=True)
        if s.get("OOMKilled"):raise RuntimeError(service+" was OOM killed")
        if kind=="completed" and status=="exited":
            assert s["ExitCode"]==0,service+" init failed";return
        if kind=="healthy" and health=="healthy":return
        if kind=="healthy" and status=="exited":raise RuntimeError(service+" exited")
        time.sleep(5)
    raise TimeoutError(service+" did not reach "+kind)
def start():
    resources("start")
    runlog("start-storage",compose("up","-d","--no-build","native-db","native-storage-init"))
    wait("native-storage-init","completed");wait("native-db","healthy")
    runlog("storage-init-output",compose("logs","--no-color","native-storage-init"))
    runlog("start-initializer",compose("up","-d","--no-deps","--no-build","native-airflow-init"))
    wait("native-airflow-init","completed")
    runlog("airflow-init-output",compose("logs","--no-color","native-airflow-init"))
    runlog("start-airflow",compose("up","-d","--no-deps","--no-build","native-scheduler"))
    wait("native-scheduler","healthy")
def api(path,method="GET",data=None):
    creds=base64.b64encode(("native_admin:"+values()["NATIVE_ADMIN_PASSWORD"]).encode()).decode()
    body=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request("http://127.0.0.1:8088/api/v1/"+path,data=body,method=method,
        headers={"Authorization":"Basic "+creds,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
def airflow():
    resources("airflow")
    assert state("native-scheduler").get("Health",{}).get("Status")=="healthy"
    runlog("dag-import",compose("exec","-T","native-scheduler","python","/harness/capture_airflow.py","inspect"))
    def observed():
        raw=command(compose("exec","-T","native-scheduler","python","/harness/capture_airflow.py","status")).stdout
        return json.loads(raw.split("@@JSON@@",1)[1])
    existing=observed()
    if existing["run"] is None:
        runlog("dag-unpause",compose("exec","-T","native-scheduler","airflow","dags","unpause",DAG))
        runlog("dag-trigger",compose("exec","-T","native-scheduler","airflow","dags","trigger",DAG,"--run-id",RUN))
    else:print("Observing existing native run, without retrigger: "+RUN,flush=True)
    until=time.monotonic()+600
    poll=len(list(OUT.glob("dag-poll-*.json")))
    while time.monotonic()<until:
        data=observed();r=data["run"]
        save(OUT/("dag-poll-"+str(poll).zfill(3)+".json"),data);poll+=1
        print("Real native DAG: "+r["state"]+" "+json.dumps({t["task_id"]:t["state"] for t in data["tasks"]}),flush=True)
        if r["state"] in {"success","failed"}:
            assert r["state"]=="success","Native DAG failed; inspect genuine task logs";break
        time.sleep(5)
    else:raise TimeoutError("Native DAG exceeded bounded wait")
    runlog("dag-capture",compose("exec","-T","native-scheduler","python","/harness/capture_airflow.py","capture"))

def export():
    target=OUT/"artifacts";assert not target.exists()
    runlog("export-native-artifacts",compose("cp","native-scheduler:/evidence/native_classroom_01",str(target)))
    logs=OUT/"airflow-task-logs";assert not logs.exists()
    runlog("export-native-task-logs",compose("cp","native-scheduler:/opt/airflow/logs/dag_id="+DAG,str(logs)))
    runlog("native-service-logs",compose("logs","--no-color","native-scheduler","native-webserver"))
    native_ids=command(["docker","ps","--all","--filter","label=com.docker.compose.project="+PROJECT,"--format","{{.ID}}"]).stdout.splitlines()
    info={}
    for identifier in native_ids:
        obj=json.loads(command(["docker","inspect",identifier]).stdout)[0]
        info[obj["Name"]]={"id":obj["Id"],"image":obj["Image"],"state":obj["State"],"memory_cap":obj["HostConfig"]["Memory"],"nano_cpus":obj["HostConfig"]["NanoCpus"],"mounts":obj["Mounts"]}
    save(OUT/"native-containers.json",info)
    save(OUT/"production-after.json",production())
    assert json.loads((OUT/"production-after.json").read_text())==json.loads((OUT/"production-before.json").read_text())
    assert inspect_existing()==json.loads((OUT/"existing-services-before.json").read_text())
    print("Exported genuine native evidence; existing services and production snapshot unchanged.")
def main():
    parser=argparse.ArgumentParser();parser.add_argument("stage",choices=["prepare","build","start","airflow","loop","viewer","export","validate","scheduler","pause-scheduler","web"])
    parser.add_argument("--loop-id",default="native_simple_01")
    parser.add_argument("--evidence-group",default="native_classroom_01")
    args=parser.parse_args()
    assert re.fullmatch(r"native_classroom_[A-Za-z0-9_.-]{1,60}",args.evidence_group),"Invalid evidence group"
    global OUT
    OUT=ROOT/"docs/verification/bonus/native-classroom/runtime"/args.evidence_group
    if args.stage=="prepare":prepare()
    elif args.stage=="build":
        resources("build");runlog("image-build",compose("--progress","plain","build","native-scheduler"))
    elif args.stage=="start":start()
    elif args.stage=="scheduler":
        resources("start")
        runlog("resume-native-scheduler",compose("up","-d","--no-deps","--no-build","native-scheduler"))
        wait("native-scheduler","healthy")
    elif args.stage=="pause-scheduler":runlog("pause-native-scheduler",compose("stop","native-scheduler"))
    elif args.stage=="web":
        resources("viewer")
        runlog("native-webserver",compose("up","-d","--no-deps","--no-build","native-webserver"))
        wait("native-webserver","healthy")
    elif args.stage=="airflow":airflow()
    elif args.stage=="loop":
        resources("loop");runlog("native-langgraph",compose("run","--rm","--no-deps","-e","NATIVE_LOOP_RUN_ID="+args.loop_id,"native-loop-worker"))
    elif args.stage=="viewer":
        resources("viewer");runlog("start-viewer",compose("up","-d","--no-deps","native-viewer"))
    elif args.stage=="export":export()
    elif args.stage=="validate":config("compose-isolation-final.json")
if __name__=="__main__":
    try:main()
    except Exception as error:
        print("NATIVE STAGE FAILED: "+redact(type(error).__name__+": "+str(error)),flush=True)
        raise SystemExit(1)
