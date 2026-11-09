"""Independent post-run evidence checks; no training, database writes or policy calls."""
import csv,json,math
from pathlib import Path
from bike_demand.contracts import dataset_hash,validate_final
from bike_demand_ml.models import prepare,FEATURES,FORBIDDEN

KNOWN_CASES={"normal","duplicate_date","missing_weather","transient_database","permanent_database",
             "transient_training","exhaust_training","weak_model","invalid_model"}
KNOWN_POLICIES={"adaptive","fixed_port","simple_port"}
RECOVERABLE={"OperationalError","TimeoutError","TrainingInterrupted"}

def audit_saved_run(folder,case,policy,*,require_database=True):
    """Fail closed on missing/inconsistent artifacts. Tolerance is numerical, not a quality target."""
    folder=Path(folder);checks={};observed={};errors=[]
    def check(name,value):checks[name]=bool(value)
    try:
        report=json.loads((folder/"report.json").read_text())
        events=[json.loads(s) for s in (folder/"events.jsonl").read_text().splitlines()]
        topology=json.loads((folder/"graph.json").read_text())
        check("recognized_scenario_policy",case in KNOWN_CASES and policy in KNOWN_POLICIES)
        check("identity",report.get("scenario")==case and report.get("policy")==policy and report.get("run_id")==folder.name)
        expected_success=(case in {"normal","weak_model"} or
            case in {"transient_database","transient_training"} and policy!="simple_port")
        check("scenario_status",report.get("status")==("success" if expected_success else "failed"))
        starts=[e for e in events if e.get("kind")=="node_started"]
        ends=[e for e in events if e.get("kind")=="node_completed"]
        routes=report.get("routes",[]);trials=report.get("trials",[])
        count=lambda name:sum(e.get("node")==name for e in starts)
        check("nonempty_trace",bool(events) and bool(routes))
        check("paired_ordered_events",len(events)%2==0 and bool(events) and
              [e.get("sequence") for e in events]==list(range(1,len(events)+1)) and
              all(events[i].get("kind")=="node_started" and events[i+1].get("kind")=="node_completed"
                  and events[i].get("node")==events[i+1].get("node") for i in range(0,len(events)-1,2)))
        edges={(e["source"],e["target"]) for e in topology["edges"]}
        check("executed_edges_exist",bool(starts) and starts[0]["node"]=="data_loader"
            and all((a["node"],b["node"]) in edges for a,b in zip(starts,starts[1:])))
        terminal="reporting" if expected_success else "failure_report"
        check("terminal_once",count(terminal)==1 and
              count("failure_report" if expected_success else "reporting")==0 and
              bool(ends) and ends[-1]["node"]==terminal)
        counters={"attempt":count("training"),"load_attempts":count("data_loader"),"recoveries":count("recovery")}
        check("counters_match_execution",all(type(report.get(k)) is int and report[k]==v for k,v in counters.items())
              and report.get("node_operations")==len(ends))
        check("finite_declared_budgets",all(type(report.get(k)) is int and 0<=report[k]<=v
              for k,v in {"attempt":3,"load_attempts":2,"recoveries":2}.items()) and
              report.get("max_attempts")==3 and report.get("max_loads")==2 and report.get("max_recoveries")==2)
        check("trial_sequence",len(trials)==counters["attempt"] and
              [t.get("attempt") for t in trials]==list(range(1,counters["attempt"]+1)))
        check("trials_match_observed_events",bool(ends) and trials==ends[-1].get("trials"))
        coordinator_ends=[e for e in ends if e["node"]=="coordinator"]
        recorded=[e.get("routes",[])[-1] if e.get("routes") else None for e in coordinator_ends]
        check("routes_match_observed_events",bool(routes) and routes==recorded)
        actual_errors=[e["issue"] for e in ends if e.get("issue") and e["issue"].get("stage")==e["node"]]
        expected_fault={
            "duplicate_date":("data_quality","ContractError",False),
            "missing_weather":("data_quality","ContractError",False),
            "permanent_database":("data_loader","PermissionError",False),
            "transient_database":("data_loader","OperationalError",True),
            "transient_training":("training","TrainingInterrupted",True),
            "exhaust_training":("training","TrainingInterrupted",True),
            "invalid_model":("training","ValueError",False)}.get(case)
        expected_error_count=(3 if policy!="simple_port" else 1) if case=="exhaust_training" else (1 if expected_fault else 0)
        check("scenario_specific_fault",len(actual_errors)==expected_error_count and
              all((e.get("stage"),e.get("type"),e.get("recoverable"))==expected_fault for e in actual_errors))
        expected_recoveries=(2 if policy!="simple_port" else 0) if case=="exhaust_training" else (
            1 if case in {"transient_database","transient_training"} and policy!="simple_port" else 0)
        expected_loads=2 if case=="transient_database" and policy!="simple_port" else 1
        check("exact_load_recovery_counts",counters["load_attempts"]==expected_loads and counters["recoveries"]==expected_recoveries)
        if case in {"duplicate_date","missing_weather","permanent_database"}:
            check("reject_before_fit",counters["attempt"]==0)
        if case in {"invalid_model","exhaust_training","weak_model"}:
            expected_attempts=1 if case=="invalid_model" or policy=="simple_port" and case=="exhaust_training" or policy=="fixed_port" and case=="weak_model" else 3
            check("exact_scenario_attempt_count",counters["attempt"]==expected_attempts and report.get("attempt")==expected_attempts)
        if case=="transient_training":
            check("fit_retry_not_early_abort",counters["attempt"]>=2 if policy!="simple_port" else counters["attempt"]==1)
        if policy=="fixed_port" and case not in {"weak_model","invalid_model"}:
            check("fixed_policy_identity",all(t.get("spec")=={"name":"ridge","alpha":10.0} for t in trials))
        # Derive coordinator destinations from measured pre-node events, never call the policy.
        wrong=[];reasons_wrong=[];pending=None
        forward={"loaded":"data_quality","quality_checked":"feature_analysis","features_ready":"model_selection",
                 "features_refined":"model_selection","candidate_selected":"training","trained":"evaluation","tested":"reporting"}
        for start,end in zip(events[::2],events[1::2]):
            if start["node"]!="coordinator":continue
            issue=start.get("issue");phase=start.get("phase");attempt=start["attempt"]
            if issue:
                recoverable=issue.get("type") in RECOVERABLE
                room=start["recoveries"]<2 and (
                    issue["stage"]=="data_loader" and start["load_attempts"]<2 or
                    issue["stage"]=="training" and attempt<3)
                destination="recovery" if recoverable and room and policy!="simple_port" else "failure_report"
                reason="supported_transient_failure" if destination=="recovery" else "unrecoverable_or_retry_exhausted"
                if destination=="recovery":pending=issue["stage"]
            elif phase=="recovered":
                destination="data_loader" if pending=="data_loader" else "model_selection" if pending=="training" else "invalid"
                reason="resume_after_bounded_recovery";pending=None
            elif phase=="evaluated":
                available=[t for t in start["trials"] if t.get("status")=="success"]
                best=min([report["baseline"]["rmse"]]+[t["validation"]["rmse"] for t in available])
                met=best<=0.95*report["baseline"]["rmse"]
                last=available[-1];gap=last["validation"]["rmse"]/max(last["train"]["rmse"],1e-9)
                if policy=="fixed_port":destination,reason="final_test","fixed_workflow_single_candidate"
                elif attempt>=3:destination,reason="final_test","attempt_budget_exhausted"
                elif met and (policy=="simple_port" or gap<=1.5):destination,reason="final_test","validation_target_met"
                elif policy=="adaptive" and gap>1.5 and start["diagnostics"]["collinear_weather"]:
                    # Refinement state is also checked from actual feature_refinement visits below.
                    refined_before=any(e["node"]=="feature_refinement" and e["sequence"]<start["sequence"] for e in ends)
                    destination,reason=("model_selection","validation_gap_requires_another_candidate") if refined_before else (
                        "feature_refinement","train_validation_gap_and_collinear_weather")
                else:destination,reason="model_selection","validation_gap_requires_another_candidate"
            else:destination=forward.get(phase,"invalid");reason="validated_"+str(phase)
            if end.get("next_node")!=destination:wrong.append(end["sequence"])
            if end.get("reason")!=reason:reasons_wrong.append(end["sequence"])
        check("independent_actual_routing",not wrong and bool(coordinator_ends))
        check("specific_routing_reasons",not reasons_wrong and bool(coordinator_ends))
        observed.update(counters,events=len(events),error_count=len(actual_errors),incorrect_route_events=wrong)
        if expected_success:
            import pandas as pd
            frame=pd.read_csv(folder/"database_snapshot.csv",float_precision="round_trip")
            validate_final(frame)
            digest=dataset_hash(frame);provenance=report["provenance"]
            check("snapshot_contract_and_hash",report.get("dataset_hash")==digest==provenance.get("dataset_hash"))
            q=report["quality"]
            check("measured_quality",q.get("contract_valid") is True and q.get("rows")==len(frame)==731
                  and q.get("unique_dates")==frame.date.nunique()==731 and
                  q.get("start")==min(frame.date)=="2011-01-01" and q.get("end")==max(frame.date)=="2012-12-31" and q.get("dataset_hash")==digest)
            if require_database:
                check("readonly_database_provenance",provenance.get("transaction_read_only")=="on" and
                    provenance.get("database")=="bike_demand" and
                    (provenance.get("origin")=="application_postgresql" or provenance.get("parent_origin")=="application_postgresql"))
            X,y,parts=prepare(frame)
            train_dates=frame.iloc[parts["train"]].date.tolist()
            val_dates=frame.iloc[parts["validation"]].date.tolist()
            test_dates=frame.iloc[parts["test"]].date.tolist()
            check("chronological_boundaries",len(train_dates)==365 and len(val_dates)==182 and len(test_dates)==184
                  and max(train_dates)<min(val_dates) and max(val_dates)<min(test_dates)
                  and train_dates[0]=="2011-01-01" and val_dates[0]=="2012-01-01" and test_dates[0]=="2012-07-01")
            lists=[report["features"],report["best"]["features"]]+[t["features"] for t in trials]
            check("nonempty_allowed_features",all(bool(f) and len(f)==len(set(f)) and set(f)<=set(FEATURES) and not FORBIDDEN.intersection(f) for f in lists))
            correlations=X.iloc[parts["train"]].astype(float).corr().abs()
            collinear=[c for c in ["temperature_2m_max","temperature_2m_min"] if correlations.loc["temperature_2m_mean",c]>0.95]
            check("measured_training_diagnostics",report["diagnostics"]["collinear_weather"]==collinear and
                [report["diagnostics"][k] for k in ["train_rows","validation_rows","test_rows"]]==[365,182,184])
            training_mean=float(y.iloc[parts["train"]].mean())
            validation_values=y.iloc[parts["validation"]].tolist()
            baseline_errors=[training_mean-v for v in validation_values]
            baseline_mean=sum(validation_values)/len(validation_values)
            expected_baseline={"mae":sum(abs(e) for e in baseline_errors)/len(baseline_errors),
                "rmse":math.sqrt(sum(e*e for e in baseline_errors)/len(baseline_errors)),
                "r2":1-sum(e*e for e in baseline_errors)/sum((v-baseline_mean)**2 for v in validation_values)}
            check("measured_dummy_validation_baseline",all(math.isclose(v,report["baseline"][k],rel_tol=1e-10,abs_tol=1e-10) for k,v in expected_baseline.items()))
            best={"spec":{"name":"dummy"},"features":list(FEATURES),"validation":report["baseline"]}
            for trial in trials:
                if trial["status"]=="success" and trial["validation"]["rmse"]<best["validation"]["rmse"]:
                    best={k:trial[k] for k in ["spec","features","validation"]}
            check("selected_identity_and_features",best["spec"]==report["best"]["spec"] and best["features"]==report["best"]["features"] and
                  math.isclose(best["validation"]["rmse"],report["best"]["validation"]["rmse"],rel_tol=1e-12))
            predictions=list(csv.DictReader((folder/"test_predictions.csv").open()))
            check("predictions_cover_heldout",len(predictions)==184 and [r["date"] for r in predictions]==test_dates and
                  [float(r["observed_cnt"]) for r in predictions]==y.iloc[parts["test"]].tolist())
            labels=[float(r["observed_cnt"]) for r in predictions];mean=sum(labels)/len(labels)
            measured={}
            for label,column in [("selected","prediction"),("dummy","dummy_prediction")]:
                errors_=[float(r[column])-float(r["observed_cnt"]) for r in predictions]
                values={"mae":sum(abs(e) for e in errors_)/len(labels),
                        "rmse":math.sqrt(sum(e*e for e in errors_)/len(labels)),
                        "r2":1-sum(e*e for e in errors_)/sum((v-mean)**2 for v in labels)}
                measured[label]=values
                check("recomputed_"+label+"_metrics",all(math.isfinite(v) and math.isclose(v,report["final_metrics"][label][k],rel_tol=1e-10,abs_tol=1e-10)
                      for k,v in values.items()))
            check("single_final_stage_no_backedge",count("final_test")==report["test_stage_count"]==1 and
                  report.get("final_refit_rows")==547 and report.get("heldout_rows")==184 and
                  all(e["node"] in {"coordinator","reporting"} for e in starts if e["sequence"]>next(e["sequence"] for e in ends if e["node"]=="final_test")))
            if case=="weak_model":
                check("weak_model_still_weak",report["best"]["spec"]["name"]=="dummy" and
                      all(math.isclose(t["validation"]["rmse"],report["baseline"]["rmse"],rel_tol=1e-12) for t in trials) and
                      all(math.isclose(measured["selected"][k],measured["dummy"][k],rel_tol=1e-10,abs_tol=1e-10) for k in measured["selected"]))
            observed["measured_metrics"]=measured
        else:
            check("failure_no_evaluation_artifacts",not report.get("final_metrics") and report.get("test_stage_count",0)==0
                  and count("final_test")==0 and not (folder/"test_predictions.csv").exists())
        check("role_metrics_match_events",all(v["calls"]==count(name) and v["seconds"]>=0 and
              math.isclose(v["seconds"],sum(ev.get("duration_seconds") or 0 for ev in ends if ev["node"]==name),rel_tol=1e-10,abs_tol=1e-12) and
              v["errors"]==sum((ev.get("issue") or {}).get("stage")==name for ev in ends if ev["node"]==name)
              for name,v in report["agent_metrics"].items()) and set(report["agent_metrics"])=={e["node"] for e in ends})
    except Exception as error:
        errors.append(type(error).__name__);check("complete_parseable_evidence",False)
    return {"case":case,"policy":policy,"run_id":folder.name,"assertions":checks,
        "observed":observed,"errors":errors,"score":sum(checks.values())/len(checks) if checks else 0.0,
        "threshold":1.0,"passed":bool(checks) and all(checks.values())}
