"""Unmodified pinned reference probes, separate from honest regression ports."""
import importlib.util,json,os,shutil,sys,tempfile,time
from pathlib import Path
from bike_demand.io_utils import write_json
from bike_demand_ml.db import load_postgres_snapshot

def import_file(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def probe(run_id,root,cache,loader=load_postgres_snapshot):
    import re
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}",run_id):raise ValueError("Unsafe run ID")
    out=Path(root)/"classroom"/run_id;out.mkdir(parents=True,exist_ok=False)
    frame,provenance=loader()
    write_json(out/"input_provenance.json",provenance)
    os.environ.pop("OPENROUTER_API_KEY",None);os.environ.pop("CURSOR_API_KEY",None)
    observations=[]
    with tempfile.TemporaryDirectory(prefix="ids706-classroom-") as work:
        reference=Path(work)/"reference";shutil.copytree(cache,reference)
        sys.path.insert(0,str(reference))
        prep=import_file("classroom_prep",reference/"solution/langgraph/baseline.py")
        loop=import_file("classroom_loop",reference/"solution/langgraph/graph.py")
        started=time.perf_counter()
        try:
            result=prep.run_prep(run_id="reference",subset_rows=2000)
            write_json(out/"native_prep_fraud.json",result)
            observations.append({"system":"Classroom fixed prep CLI helper","status":"success",
                "seconds":time.perf_counter()-started,"metrics":result["baseline"],
                "scope":"Unmodified documented CLI helper; original Airflow DAG was inspected, not scheduled/executed",
                "same_bike_problem":False})
            started=time.perf_counter()
            result_b=loop.run_solution_loop(dataset_path=result["published"]["published_latest"],
                target_column="is_fraud",max_cycles=2,seed=42)
            write_json(out/"native_simple_fraud.json",result_b)
            observations.append({"system":"Classroom simple agent graph","status":"success" if result_b.get("holdout_metrics") else "no_holdout",
                "seconds":time.perf_counter()-started,"metrics":result_b.get("holdout_metrics"),
                "cycles":result_b.get("cycles"),"same_bike_problem":False,
                "scope":"Unmodified graph with documented no-key heuristic fallback"})
        except Exception as error:
            observations.append({"system":"Native classroom fraud probe","status":"failed","error_type":type(error).__name__})
        snapshot=out/"bike_snapshot.csv";frame.to_csv(snapshot,index=False)
        for name,operation in [
            ("classroom_fixed_on_cnt",lambda:prep.train_baseline(snapshot,target_column="cnt",drop_columns=["date"])),
            ("classroom_simple_on_cnt",lambda:loop.run_solution_loop(dataset_path=str(snapshot),
                target_column="cnt",max_cycles=1,seed=706))]:
            started=time.perf_counter()
            try:
                value=operation()
                write_json(out/(name+".json"),value)
                observations.append({"system":name,"status":"completed_classification_contract",
                    "seconds":time.perf_counter()-started,"comparable_regression_metrics":False,
                    "scope":"Classifier/F1 API; no bike-demand MAE/RMSE comparison"})
            except Exception as error:
                observations.append({"system":name,"status":"incompatible_or_failed",
                    "seconds":time.perf_counter()-started,"error_type":type(error).__name__,
                    "comparable_regression_metrics":False})
    write_json(out/"summary.json",{"source_commit":"a294145ea9aa4225908ce701c06160c33213335d",
        "observations":observations,"exact_airflow_dag_executed":False,
        "limitation":"Native classification/random-split baselines do not implement chronological cnt regression. Regression ports are reported separately."})
    return observations
