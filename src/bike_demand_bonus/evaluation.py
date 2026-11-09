"""Explicit case specifications, isolated faults, independent checks and real results."""
import copy,csv,json,re,math
from pathlib import Path
import psycopg
from bike_demand.io_utils import write_json
from bike_demand_ml.db import load_postgres_snapshot
from bike_demand_ml.models import FORBIDDEN
from bike_demand_bonus.runner import execute,fault_trainer
from bike_demand_bonus.audit import audit_saved_run

POLICIES=["adaptive","fixed_port","simple_port"]
CASES=[
 {"id":"normal","input":"Unmodified validated PostgreSQL snapshot","expected":"All complete with sealed test evaluation","criteria":"success, valid data/features, finite metrics, bounded routes, complete report","threshold":"all assertions true"},
 {"id":"duplicate_date","input":"Isolated copy with date[1]=date[0]","expected":"All reject before training","criteria":"failed, attempt=0, no test metrics","threshold":"all assertions true"},
 {"id":"missing_weather","input":"Isolated copy without precipitation_sum","expected":"All reject before training","criteria":"failed, attempt=0, no test metrics","threshold":"all assertions true"},
 {"id":"transient_database","input":"One injected OperationalError before snapshot delivery","expected":"Adaptive/fixed recover; simple port fails without DB recovery","criteria":"expected status; successful recovery exactly once where supported","threshold":"all assertions true"},
 {"id":"permanent_database","input":"Injected PermissionError, no database mutation","expected":"All fail without retry","criteria":"failed, recoveries=0, no test metrics","threshold":"all assertions true"},
 {"id":"transient_training","input":"One TrainingInterrupted on first candidate","expected":"Adaptive/fixed recover; simple port fails","criteria":"expected status; one recovery where supported","threshold":"all assertions true"},
 {"id":"exhaust_training","input":"Every candidate raises TrainingInterrupted","expected":"All fail within budgets","criteria":"failed; <=3 attempts, <=2 recoveries; no test metrics","threshold":"all assertions true"},
 {"id":"weak_model","input":"All candidate operations intentionally use Dummy; real predictions scored","expected":"Bounded termination with unmet quality; best Dummy retained","criteria":"success; adaptive/simple 3 attempts, fixed 1; no improvement claimed","threshold":"all assertions true"},
 {"id":"invalid_model","input":"Unsupported model family in isolated candidate fixture","expected":"All abort unsupported fit, without recovery","criteria":"failed; attempt=1, recoveries=0, no test metrics","threshold":"all assertions true"},
]

def loader_for(frame,provenance,case):
    calls=0
    def loader():
        nonlocal calls
        calls+=1
        if case=="transient_database" and calls==1:raise psycopg.OperationalError("isolated fixture")
        if case=="permanent_database":raise PermissionError("isolated fixture")
        result=frame.copy(deep=True)
        if case=="duplicate_date":result.loc[1,"date"]=result.loc[0,"date"]
        if case=="missing_weather":result=result.drop(columns=["precipitation_sum"])
        meta=copy.deepcopy(provenance)
        meta.update(origin="isolated_evaluation_fixture",parent_origin=provenance["origin"],scenario=case)
        return result,meta
    return loader

def expected_status(case,policy):
    if case in {"duplicate_date","missing_weather","permanent_database","exhaust_training","invalid_model"}:return "failed"
    if case in {"transient_database","transient_training"} and policy=="simple_port":return "failed"
    return "success"

def assess(report,case,policy):
    expected=expected_status(case,policy)
    assertions={}
    assertions["expected_status"]=report["status"]==expected
    assertions["termination"]=report.get("attempt",0)<=3 and report.get("load_attempts",0)<=2 and report.get("recoveries",0)<=2
    assertions["route_explanations"]=all(r.get("reason") and not r.get("uses_heldout_metrics") for r in report.get("routes",[]))
    routes=report.get("routes",[])
    forward={"loaded":"data_quality","quality_checked":"feature_analysis","features_ready":"model_selection",
        "features_refined":"model_selection","candidate_selected":"training","trained":"evaluation",
        "recovered":None,"tested":"reporting","evaluated":None}
    bad_routes=[]
    pending_recovery_stage=None
    for record in routes:
        phase=record["from_phase"];destination=record["destination"]
        if record.get("issue_type"):
            room=(record["recoveries"]<record["max_recoveries"] and
                ((record["issue_stage"]=="data_loader" and record["load_attempts"]<record["max_loads"]) or
                 (record["issue_stage"]=="training" and record["attempt"]<record["max_attempts"])))
            expected_route="recovery" if record["recoverable"] and room and policy!="simple_port" else "failure_report"
            if expected_route=="recovery":pending_recovery_stage=record["issue_stage"]
        elif phase=="evaluated":
            if policy=="fixed_port" or record["attempt"]>=record["max_attempts"]:
                expected_route="final_test"
            elif record["validation_target_met"] and (policy=="simple_port" or record["last_gap"]<=1.5):
                expected_route="final_test"
            elif policy=="adaptive" and record["last_gap"]>1.5 and record["has_collinear_weather"] and not record["refined"]:
                expected_route="feature_refinement"
            else:expected_route="model_selection"
        elif phase=="recovered":
            expected_route=("data_loader" if pending_recovery_stage=="data_loader" else
                            "model_selection" if pending_recovery_stage=="training" else "invalid")
            pending_recovery_stage=None
        else:expected_route=forward.get(phase)
        if destination!=expected_route:bad_routes.append(record)
    assertions["legal_routes"]=not bad_routes
    assertions["report_complete"]=all(k in report for k in ["run_id","policy","scenario","status","routes","trials","issue"])
    if expected=="success":
        assertions["data_quality"]=report.get("quality",{}).get("contract_valid") is True
        assertions["feature_quality"]=not FORBIDDEN.intersection(report["features"])
        assertions["split_quality"]=[report["diagnostics"][k] for k in ["train_rows","validation_rows","test_rows"]]==[365,182,184]
        assertions["single_final_test"]=report["test_stage_count"]==1
        assertions["validation_selection"]=math.isclose(report["best"]["validation"]["rmse"],min([report["baseline"]["rmse"]]+[t["validation"]["rmse"] for t in report["trials"] if t["status"]=="success"]),rel_tol=1e-12)
        assertions["final_metrics"]=all(math.isfinite(report["final_metrics"][m][k])
            for m in ["selected","dummy"] for k in ["mae","rmse","r2"])
    else:
        assertions["no_test_metrics"]=not report.get("final_metrics") and report.get("test_stage_count",0)==0
    if case in {"duplicate_date","missing_weather"}:assertions["reject_before_training"]=report.get("attempt",0)==0
    if case in {"permanent_database","invalid_model"}:assertions["no_invalid_recovery"]=report.get("recoveries",0)==0
    if case in {"transient_database","transient_training"} and policy!="simple_port":
        assertions["recovery_success"]=report["status"]=="success" and report.get("recoveries")==1
    if case=="weak_model":
        assertions["bounded_weak_search"]=report["attempt"]==(1 if policy=="fixed_port" else 3)
        assertions["honest_weak_model"]=report["best"]["spec"]["name"]=="dummy"
    return {"assertions":assertions,"score":sum(assertions.values())/len(assertions),
        "threshold":1.0,"passed":all(assertions.values()),"route_decisions":len(routes),
        "incorrect_routes":len(bad_routes)}

def evaluate_suite(suite_id,root,loader=load_postgres_snapshot):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,39}",suite_id):raise ValueError("Unsafe suite ID")
    target=Path(root)/"evaluations"/suite_id;target.mkdir(parents=True,exist_ok=False)
    frame,provenance=loader()
    write_json(target/"input_provenance.json",provenance)
    write_json(target/"case_definitions.json",CASES)
    rows=[]
    for case in CASES:
        for policy in POLICIES:
            run_id=suite_id+"_"+case["id"]+"_"+policy
            result=execute(run_id,Path(root)/"runs",policy=policy,scenario=case["id"],
                loader=loader_for(frame,provenance,case["id"]),trainer=fault_trainer(case["id"]))
            grade=assess(result,case["id"],policy)
            artifact_audit=audit_saved_run(Path(root)/"runs"/run_id,case["id"],policy,
                require_database=provenance.get("origin")=="application_postgresql")
            grade["assertions"].update({"artifact_"+key:value for key,value in artifact_audit["assertions"].items()})
            grade["score"]=sum(grade["assertions"].values())/len(grade["assertions"])
            grade["passed"]=all(grade["assertions"].values()) and artifact_audit["passed"]
            grade["artifact_audit"]=artifact_audit
            rows.append({"case":case["id"],"policy":policy,"run_id":run_id,
                "input":case["input"],"expected":expected_status(case["id"],policy),
                "criteria":case["criteria"],"observed_status":result["status"],**grade,
                "attempts":result.get("attempt",0),"recoveries":result.get("recoveries",0),
                "wall_seconds":result["wall_seconds"],"cpu_seconds":result["cpu_seconds"],"node_operations":result["node_operations"],
                "worker_rss_high_water_kib":result["worker_rss_high_water_kib"],
                "final_metrics":result.get("final_metrics")})
            write_json(target/"results.json",rows)  # live incremental progress
    summary=[]
    for policy in POLICIES:
        group=[r for r in rows if r["policy"]==policy]
        count=sum(r["route_decisions"] for r in group)
        summary.append({"policy":policy,"cases":len(group),
            "completion_rate":sum(r["observed_status"]=="success" for r in group)/len(group),
            "expected_behavior_pass_rate":sum(r["passed"] for r in group)/len(group),
            "incorrect_routing_rate":sum(r["incorrect_routes"] for r in group)/max(count,1),
            "total_wall_seconds":sum(r["wall_seconds"] for r in group),
            "total_cpu_seconds":sum(r["cpu_seconds"] for r in group),
            "total_attempts":sum(r["attempts"] for r in group),
            "total_recoveries":sum(r["recoveries"] for r in group),
            "normal_test":next(r["final_metrics"] for r in group if r["case"]=="normal"),
            "baseline_scope":"Original adaptive system" if policy=="adaptive" else
                "Explicit regression workflow port; not an unmodified classroom execution"})
    write_json(target/"summary.json",summary)
    with (target/"results.csv").open("w",newline="",encoding="utf-8") as handle:
        columns=["case","policy","run_id","expected","observed_status","passed","score","threshold",
                 "attempts","recoveries","wall_seconds","node_operations","incorrect_routes"]
        writer=csv.DictWriter(handle,fieldnames=columns,extrasaction="ignore");writer.writeheader();writer.writerows(rows)
    return {"suite_id":suite_id,"cases":len(CASES),"executions":len(rows),
            "passed":sum(r["passed"] for r in rows),"failed":sum(not r["passed"] for r in rows),
            "summary":summary}
