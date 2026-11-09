"""Run-scoped intermediate frames; small receipts only through XCom."""
from pathlib import Path
import time
import pandas as pd
from bike_demand import contracts, storage
from bike_demand.sources import SourceUnavailable
from bike_demand.io_utils import artifact_dir, data_dir, now, read_json, write_json

def save_frame(run_id, name, frame, report):
    path = data_dir(run_id)/"clean"/f"{name}.json"
    write_json(path, frame.to_dict(orient="records"))
    report_path = artifact_dir(run_id)/"validation"/f"{name}.json"
    write_json(report_path, report)
    return dict(path=str(path),report_path=str(report_path),rows=len(frame))

def read_frame_file(path, columns):
    rows = read_json(path)
    contracts.require(isinstance(rows,list) and bool(rows), "Empty/invalid intermediate rows")
    contracts.require(all(isinstance(r,dict) and set(r)==set(columns) for r in rows),
                      "Intermediate schema mismatch")
    return pd.DataFrame(rows, columns=columns)

def clean_bike(source, run_id):
    frame, report = contracts.clean_bike(Path(source["path"]).read_bytes())
    return {**save_frame(run_id,"bike",frame,report),"source":source}

def clean_weather(source, run_id):
    frame, report = contracts.clean_weather(read_json(source["path"]))
    return {**save_frame(run_id,"weather",frame,report),"source":source}

def merge(bike, weather, run_id):
    frame, report = contracts.merge_dates(read_frame_file(bike["path"],contracts.BIKE_COLUMNS),
        read_frame_file(weather["path"],["date"]+contracts.WEATHER_COLUMNS))
    report.update(coverage=contracts.dates_contract(frame),dataset_hash=contracts.dataset_hash(frame))
    return {**save_frame(run_id,"merged",frame,report),
            "sources":{"uci":bike["source"],"open_meteo":weather["source"]}}

def load(merged, run_id):
    receipt = storage.load_frame(read_frame_file(merged["path"],contracts.FINAL_COLUMNS),run_id,
                                 merged["sources"],read_json(merged["report_path"]))
    write_json(artifact_dir(run_id)/"load-receipt.json",receipt)
    return receipt

def execute_stage(audit_run_id, task_id, attempt, function, **kwargs):
    audit_path = artifact_dir(audit_run_id)/"tasks"/f"{task_id}_attempt_{attempt}.json"
    audit = dict(run_id=audit_run_id,task_id=task_id,attempt=attempt,started_at_utc=now(),status="running")
    write_json(audit_path,audit)
    started = time.monotonic()
    try:
        result = function(**kwargs)
    except Exception as exc:
        audit.update(status="failed",finished_at_utc=now(),elapsed_seconds=time.monotonic()-started,
            error_type=type(exc).__name__,
            error=str(exc) if isinstance(exc,(contracts.ContractError,SourceUnavailable)) else "Stage failed; secret-bearing details omitted.",
            sqlstate=getattr(exc,"sqlstate",None))
        write_json(audit_path,audit)
        raise
    audit.update(status="success",finished_at_utc=now(),elapsed_seconds=time.monotonic()-started,result=result)
    write_json(audit_path,audit)
    return result
