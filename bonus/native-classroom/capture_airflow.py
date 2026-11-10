"""Read native Airflow state/XCom and preserve actual outputs; no training calls."""
import hashlib,json,os,sys
from datetime import datetime,timezone
from importlib.metadata import version
from pathlib import Path
import pandas as pd
from airflow.models import DagBag,DagRun,XCom
from airflow.utils.session import create_session
from airflow.configuration import conf

os.umask(0o002)
ROOT=Path("/evidence/native_classroom_01")
DAG="solution_baseline_prep"
RUN="native_prep_01"
TASKS={"validate_customers","validate_transactions","merge_csvs","make_subset","profile_light","train_baseline","publish_merged"}
def save(path,data):
    path=Path(path)
    if path.exists():
        assert json.loads(path.read_text())==json.loads(json.dumps(data,default=str)),"Existing evidence differs: "+str(path)
        return
    with path.open("x",encoding="utf-8") as f:json.dump(data,f,indent=2,default=str);f.write("\n")
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def inspect():
    ROOT.mkdir(exist_ok=True)
    ROOT.chmod(0o2775)
    bag=DagBag(dag_folder="/opt/airflow/dags",include_examples=False,safe_mode=False)
    assert not bag.import_errors,str(bag.import_errors)
    dag=bag.get_dag(DAG);assert dag and set(dag.task_ids)==TASKS
    assert dag.schedule_interval is None and not dag.catchup
    original=Path("/reference/solution/airflow/dags/solution_baseline_prep.py")
    mounted=Path("/opt/airflow/dags/solution_baseline_prep.py")
    pins=json.loads(Path("/harness/source-pins.json").read_text())
    assert digest(mounted)==pins["source_files"]["solution/airflow/dags/solution_baseline_prep.py"]["sha256"]
    data={"executor":conf.get("core","executor"),"parallelism":conf.getint("core","parallelism"),"dag_id":DAG,"schedule":None,"catchup":dag.catchup,"tasks":sorted(TASKS),
        "edges":[[t.task_id,d] for t in dag.tasks for d in sorted(t.downstream_task_ids)],
        "source_sha256":digest(original),"mounted_sha256":digest(mounted),"source_byte_unchanged":original.read_bytes()==mounted.read_bytes(),
        "versions":{p:version(p) for p in ["apache-airflow","pandas","numpy","scikit-learn","scipy"]}}
    save(ROOT/"dag-import.json",data);return data
def status():
    with create_session() as session:
        dr=session.query(DagRun).filter_by(dag_id=DAG,run_id=RUN).one_or_none()
        if dr is None:return {"run":None,"tasks":[]}
        return {"run":{"dag_id":DAG,"dag_run_id":RUN,"state":dr.state,"logical_date":str(dr.execution_date)},
            "tasks":[{"task_id":t.task_id,"state":t.state} for t in dr.get_task_instances(session=session)]}
def capture():
    ROOT.chmod(0o2775)
    folder=ROOT/RUN;folder.mkdir(exist_ok=True)
    if (folder/"report.json").exists():return json.loads((folder/"report.json").read_text())
    with create_session() as session:
        dr=session.query(DagRun).filter_by(dag_id=DAG,run_id=RUN).one()
        tasks=dr.get_task_instances(session=session)
        states=[{"task_id":t.task_id,"state":t.state,"try_number":t.try_number,"start_date":t.start_date,
                 "end_date":t.end_date,"duration":t.duration,"hostname":t.hostname} for t in tasks]
        assert len(states)==7 and {t["task_id"] for t in states}==TASKS and all(t["state"]=="success" for t in states)
        assert dr.state=="success"
        values={task:XCom.get_one(dag_id=DAG,task_id=task,run_id=RUN,key="return_value",session=session) for task in TASKS}
        identity={"dag_id":DAG,"run_id":RUN,"state":dr.state,"logical_date":dr.execution_date,
            "start_date":dr.start_date,"end_date":dr.end_date,"run_type":str(dr.run_type),"external_trigger":dr.external_trigger}
    save(folder/"task-states.json",states);save(folder/"xcom.json",values)
    merged=Path(values["merge_csvs"]["merged_path"]);subset=Path(values["make_subset"]["merged_path"])
    published=Path(values["publish_merged"]["published_latest"])
    assert published.read_bytes()==subset.read_bytes()
    frames={key:pd.read_csv(p) for key,p in [("merged",merged),("subset",subset),("published",published)]}
    assert len(frames["merged"])==10000 and len(frames["subset"])==len(frames["published"])==2000
    expected=frames["merged"].sample(n=2000,random_state=42).reset_index(drop=True)
    pd.testing.assert_frame_equal(expected,frames["subset"].reset_index(drop=True),check_exact=False,rtol=1e-10,atol=1e-10)
    metric=values["train_baseline"];assert 0<=metric["f1"]<=1 and (metric["n_train"],metric["n_val"])==(1600,400)
    output={}
    for key,path in [("merged",merged),("subset",subset),("published",published)]:
        dest=folder/(key+".csv");dest.write_bytes(path.read_bytes())
        output[key]={"path":str(path),"rows":len(frames[key]),"sha256":digest(path),
          "class_counts":{str(k):int(v) for k,v in frames[key].is_fraud.value_counts().items()}}
    source={}
    for filename in ["customers.csv","transactions.csv"]:
        p=Path("/repo/datasets/airflow")/filename
        expected_sha=json.loads(Path("/harness/source-pins.json").read_text())["source_files"]["datasets/airflow/"+filename]["sha256"]
        assert digest(p)==expected_sha
        source[filename]={"sha256":digest(p),"rows":len(pd.read_csv(p))}
    report={**identity,"captured_at_utc":datetime.now(timezone.utc).isoformat(),"actual_airflow_dag_executed":True,
        "all_seven_tasks_success":True,"baseline_validation":metric,"heldout_metrics":None,
        "scope":"Native numeric-only fraud classification; 80/20 random stratified split; no sealed holdout in this DAG",
        "source_data":source,"outputs":output,"source_commit":json.loads(Path("/harness/source-pins.json").read_text())["commit"],
        "sampling":"2000 rows; DataFrame.sample(random_state=42), not stratified","native_source_modified":False}
    save(folder/"report.json",report);return report
if __name__=="__main__":
    result={"inspect":inspect,"status":status,"capture":capture}[sys.argv[1]]()
    print("@@JSON@@"+json.dumps(result,default=str))
