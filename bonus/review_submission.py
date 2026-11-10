"""Read-only submission review; never fit models, start services, or alter Git."""
import argparse
import ast
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "docs/verification/bonus/review"
NATIVE = ROOT / "docs/verification/bonus/native-classroom/runtime/native_classroom_01"
COMPOSE = ["docker", "compose", "-f", "compose.yaml", "-f", "compose.bonus.yaml"]
# Explicit authorized documentation edits; no source/test/config wildcard exemptions.
DOCUMENTS = {
    "README.md", "agents/README.md", "bonus/README.md", "bonus/COMPARISON.md",
    "docs/checklist.md", "docs/running.md", "docs/submission.md",
    "docs/verification/bonus/review/README.md",
    "docs/verification/bonus/review/bonus-staging.txt",
    "docs/verification/bonus/review/submission-preparation.md",
    "docs/verification/bonus/screenshot-guide.md", "screenshots/README.md",
    "submission/part1/README.md",
    "docs/verification/bonus/native-classroom/results.md",
    "docs/verification/bonus/native-classroom/capture-guide.md",
    "docs/verification/bonus/native-classroom/final-staging.txt",
}
AUTHORIZED = DOCUMENTS | {".gitignore", "bonus/review_submission.py"}
RENAMED = {"screenshots/14_bonus_agent_metrics.png": "screenshots/14_bonus_policy_comparison.png"}
SCREENSHOTS = [
    "01_airflow_dag_success.png", "02_airflow_graph.png",
    "06_langgraph_live_execution.png", "07_langgraph_conditional_retry.png",
    "08_regression_evaluation.png", "09_model_comparison_charts.png",
    "10_bonus_adaptive_graph.png", "11_bonus_routing_recovery.png",
    "11b_bonus_recovery_events.png", "12_bonus_evaluation_suite.png",
    "12b_bonus_evaluation_criteria.png", "13_bonus_baseline_comparison.png",
    "14_bonus_policy_comparison.png", "15_native_airflow_success.png",
    "16_native_airflow_graph.png", "17_native_airflow_metrics.png",
    "18_native_langgraph_execution.png", "19_native_classification_results.png",
    "20_native_and_regression_scopes.png",
]
SCRATCH = {"docs/verification/bonus/review/audit-initial.json",
           "docs/verification/bonus/review/audit-rerun.json"}
sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(args, code=None):
    result = subprocess.run(args, cwd=ROOT, input=code, text=True,
                            encoding="utf-8", errors="replace", capture_output=True)
    if result.returncode:
        # Do not echo arbitrary command stderr, which could contain credentials.
        raise RuntimeError("Read-only command failed: " + str(args[0]) +
                           " (exit " + str(result.returncode) + ")")
    return result.stdout


def git(*args):
    return run(["git", "-c", "safe.directory=" + ROOT.as_posix(), *args])


def save(path, obj):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def check_preservation(root, snapshot, allowed=frozenset(), renames=None):
    """Compare bytes AND mtimes; exemptions are exact paths, never directories."""
    renames = renames or {}
    verified = 0
    for name, record in snapshot.items():
        if name in allowed:
            continue
        path = root / renames.get(name, name)
        expected = record["sha256"] if isinstance(record, dict) else record
        assert path.is_file(), "Protected file missing: " + name
        assert digest(path) == expected, "Protected bytes changed: " + name
        if isinstance(record, dict) and "mtime_ns" in record:
            assert path.stat().st_mtime_ns == record["mtime_ns"], "Protected timestamp changed: " + name
        verified += 1
    return verified


def forbidden(paths):
    bad = []
    for name in paths:
        path = Path(name)
        if ((path.name.startswith(".env") and path.name != ".env.example")
            or any(p in {".venv", "venv", "__pycache__", ".aws", ".ssh", "volumes",
                         "pgdata", "node_modules", "build", "dist", ".pytest_cache"} for p in path.parts)
            or name.startswith(("artifacts/", "data/raw/")) and not name.endswith(("README.md", ".gitkeep"))
            or name.endswith((".pyc", ".pem", ".key", ".pfx", ".p12", ".vhdx", ".sqlite", ".dump"))):
            if name not in {"artifacts/README.md", "artifacts/eda/.gitkeep", "artifacts/ml/.gitkeep", "data/raw/.gitkeep"}:
                bad.append(name)
    return bad


def screenshot_allowlist(text, names):
    actual = [line.removeprefix("!/screenshots/") for line in text.splitlines()
              if line.startswith("!/screenshots/") and line.endswith(".png")]
    assert len(actual) == len(set(actual)), "Duplicate screenshot exemption"
    assert set(actual) == set(names), "Reviewed screenshot allowlist mismatch"


def ignored(name):
    proc = subprocess.run(["git", "-c", "safe.directory=" + ROOT.as_posix(),
                           "check-ignore", "--no-index", "-q", "--", name],
                          cwd=ROOT, capture_output=True)
    assert proc.returncode in (0, 1), "Git ignore check failed"
    return proc.returncode == 0


def native_module(name):
    directory = ROOT / "bonus/native-classroom"
    sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location(name, directory / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="New repository-relative directory; must not exist")
    args = parser.parse_args()
    relative = args.output or ("docs/verification/final-bonus/audit-" +
                               datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out = ROOT / relative
    assert out.resolve().is_relative_to(ROOT / "docs/verification/final-bonus")
    out.mkdir(parents=True, exist_ok=False)  # Never overwrite a historical report.
    assert git("branch", "--show-current").strip() == "bonus/adaptive-multi-agent"
    original = load(OLD.parent / "preservation-before.json")
    assert git("rev-parse", "main").strip() == original["main_commit"]
    preserved = {}
    preserved["original_main_files"] = check_preservation(ROOT, {
        p: {"sha256": h, "mtime_ns": original["modification_time_ns"][p]}
        for p, h in original["files"].items()
    }, AUTHORIZED)
    preserved["pre_native_workspace"] = check_preservation(
        ROOT, load(NATIVE / "workspace-before.json"), AUTHORIZED, RENAMED)
    protected = load(OLD.parent / "runtime-export-sha256.json")
    preserved["frozen_bonus_runtime"] = check_preservation(OLD.parent / "runtime", protected)
    preserved["historical_logs"] = check_preservation(ROOT, load(OLD / "logs-preservation.json")["files"])
    preserved["native_runtime"] = check_preservation(NATIVE, load(NATIVE / "native-evidence-sha256.json")["files"])
    # Local audit-start snapshot additionally protects the new harness and ignored credentials.
    local_before = ROOT / "artifacts/final-submission-audit/before.json"
    if local_before.exists():
        preserved["audit_start_files"] = check_preservation(ROOT, load(local_before), AUTHORIZED)

    engine = json.loads(run(["docker", "info", "--format", "{{json .ServerVersion}}"]))
    control = native_module("control")
    assert control.inspect_existing() == load(NATIVE / "existing-services-before.json"), "Existing services changed"
    production = control.production()
    assert production == load(NATIVE / "production-before.json")
    assert production["readonly"] == "on"
    save(out / "production-readonly.json", production)
    actual = json.loads(run(COMPOSE + ["exec", "-T", "bonus-dashboard", "python", "-"], """
import json
from pathlib import Path
from bike_demand_bonus.audit import audit_saved_run
root = Path('/opt/project/artifacts/bonus')
rows = json.loads((root/'evaluations/bonus_suite_01/results.json').read_text())
print(json.dumps([audit_saved_run(root/'runs'/r['run_id'],r['case'],r['policy']) for r in rows]))
"""))
    assert len(actual) == 27 and all(r["passed"] for r in actual)
    save(out / "evaluation-audit.json", actual)
    native = native_module("verify_native").verify_native(NATIVE / "artifacts")
    save(out / "native-verification.json", native)
    live_run = control.api("dags/solution_baseline_prep/dagRuns/native_prep_01")
    live_tasks = control.api("dags/solution_baseline_prep/dagRuns/native_prep_01/taskInstances")["task_instances"]
    assert live_run["state"] == "success" and len(live_tasks) == 7
    assert all(t["state"] == "success" for t in live_tasks)
    save(out / "native-ui-api.json", {"run_id": live_run["dag_run_id"], "state": live_run["state"],
                                    "tasks": {t["task_id"]: t["state"] for t in live_tasks}})
    for port in (8502, 8503):
        with urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=10) as response:
            assert response.status == 200 and response.read() == b"ok"

    screenshot_allowlist((ROOT / ".gitignore").read_text(encoding="utf-8"), SCREENSHOTS)
    images = {}
    import struct
    for name in SCREENSHOTS:
        path = ROOT / "screenshots" / name
        assert path.is_file() and not ignored("screenshots/" + name)
        raw = path.read_bytes()
        assert raw.startswith(b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", raw[16:24])
        assert width > 100 and height > 100
        images[name] = {"sha256": digest(path), "bytes": len(raw), "width": width, "height": height}
    prior_images = load(OLD / "screenshots.json")["reviewed_present"]
    for name, record in prior_images.items():
        actual_name = Path(RENAMED.get("screenshots/" + name, "screenshots/" + name)).name
        assert images[actual_name]["sha256"] == record["sha256"]
    save(out / "screenshots.json", {"reviewed_present": images,
        "content_qualification": "19 shows node execution records and per-cycle validation F1; final classification cards are in 18 and 20. 16 shows topology; 15/17 show actual success/run evidence."})
    probes = [".env", ".env.production", "artifacts/native-classroom-local/.env",
              ".venv/example.py", "src/__pycache__/x.pyc", ".aws/credentials",
              "credentials.json", "private.key", "volumes/postgres/PG_VERSION",
              "artifacts/native-classroom-reference/loop_runtime.py", "build/temp.bin",
              "screenshots/not-reviewed.png", "screenshots/14_bonus_agent_metrics.png"]
    assert all(ignored(p) for p in probes)

    helper_spec = importlib.util.spec_from_file_location("submission_helpers", ROOT / "scripts/check_submission.py")
    helpers = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helpers)
    eligible = [p for p in helpers.eligible() if (ROOT / p).is_file() and p not in SCRATCH]
    assert not forbidden(eligible), forbidden(eligible)
    links, broken, excluded = helpers.local_links(eligible)
    assert not broken and not excluded, (broken, excluded)
    scanned, findings = helpers.secrets_check(eligible)
    # Include native credentials in private exact-value scans, including binary files.
    private_values = [v.strip().strip("'\"") for k, v in control.values().items()
                      if any(s in k for s in ("PASSWORD", "SECRET", "KEY"))]
    for p in eligible:
        raw = (ROOT / p).read_bytes()
        if any(len(v) >= 12 and (v.encode() in raw or v.encode("utf-16-le") in raw) for v in private_values):
            findings.append({"file": p, "kind": "native_local_credential"})
    assert not findings, findings  # Never include matched values.
    python_files = [p for p in eligible if p.endswith(".py")]
    for p in python_files:
        ast.parse((ROOT / p).read_text(encoding="utf-8-sig"), filename=p)
    run(COMPOSE + ["--profile", "bonus", "config", "--quiet"])
    run(["docker", "compose", "--profile", "ml", "config", "--quiet"])
    config = json.loads(run(control.compose("config", "--format", "json")))
    native_module("isolation").validate_config(config, ROOT)
    git("diff", "--check")
    git("diff", "--cached", "--check")
    final_tests = load(ROOT / "docs/verification/final-bonus/test-summary.json")
    assert final_tests["total_final_tests_passed"] == 128
    assert final_tests["final_failures"] == final_tests["final_skips"] == 0
    for name, expected in [("regression-tests", 100), ("dag-import", 1), ("postgres-integration-corrected", 1)]:
        import xml.etree.ElementTree as ET
        tree = ET.parse(ROOT / ("docs/verification/final-bonus/" + name + ".xml")).getroot()
        suites = tree.findall("testsuite") if tree.tag == "testsuites" else [tree]
        assert sum(int(t.get("tests", 0)) for t in suites) == expected
        assert all(all(int(t.get(k, 0)) == 0 for k in ("failures", "errors", "skipped")) for t in suites)
    assert not load(ROOT / "docs/verification/final-bonus/untracked-whitespace-corrected.json")["git_no_index_whitespace_findings"]
    pins = load(ROOT / "bonus/native-classroom/source-pins.json")
    for name, record in pins["source_files"].items():
        assert digest(ROOT / "artifacts/native-classroom-reference" / name) == record["sha256"]
    # Exact candidate inventory relative to verified main; separate pending deletions.
    changed = set(filter(None, git("diff", "main", "--name-only", "--diff-filter=ACMR", "-z").split("\0")))
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    paths = sorted(p for p in changed | untracked if p not in SCRATCH and (ROOT / p).is_file())
    deletions = sorted(filter(None, git("ls-files", "--deleted", "-z").split("\0")))
    assert set(deletions) <= set(RENAMED), "Unexpected deleted tracked files"
    for name in deletions:
        assert (ROOT / RENAMED[name]).is_file()
    for name, values in [("staging-files.txt", paths), ("staging-deletions.txt", deletions)]:
        (out / name).write_bytes(("\n".join(values) + "\n").encode())
    # Include the new reports/manifests in their own final inventory.
    placeholders = {"checks.json": {}, "file-status.json": {}}
    for name, value in placeholders.items():
        save(out / name, value)
    (out / "pending-staging-files.txt").write_bytes(b"")
    (out / "changed-files.txt").write_bytes(git("-c", "core.quotepath=false", "status", "--short", "--untracked-files=all").encode())
    paths = sorted(set(paths) | {p.relative_to(ROOT).as_posix() for p in out.iterdir()})
    pending_changed = set(filter(None, git("diff", "HEAD", "--name-only", "--diff-filter=ACMR", "-z").split("\0")))
    pending = sorted((pending_changed | untracked | {p.relative_to(ROOT).as_posix() for p in out.iterdir()}) & set(paths))
    (out / "pending-staging-files.txt").write_bytes(("\n".join(pending) + "\n").encode())
    (out / "staging-files.txt").write_bytes(("\n".join(paths) + "\n").encode())
    preview = git("--literal-pathspecs", "add", "--dry-run", "--pathspec-from-file=" + relative + "/staging-files.txt")
    if deletions:
        git("--literal-pathspecs", "add", "--dry-run", "-u", "--pathspec-from-file=" + relative + "/staging-deletions.txt")
    staged = list(filter(None, git("diff", "--cached", "--name-only", "-z").split("\0")))
    assert set(staged) <= set(paths) | set(deletions)
    status = [{"path": p, "action": "add" if p in untracked or p.startswith(relative + "/") else ("modify" if p in pending_changed else "already_committed_bonus")}
              for p in paths] + [{"path": p, "action": "delete_old_renamed_path"} for p in deletions]
    (out / "file-status.json").write_bytes((json.dumps(status, indent=2) + "\n").encode())
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "branch": "bonus/adaptive-multi-agent", "preservation": preserved,
              "docker_engine": engine, "fresh_readonly_review_completed": True,
              "production": production, "independent_saved_case_passes": 27,
              "native_classroom": native, "screenshots_reviewed": len(images),
              "screenshot_19_qualification": "Execution table; final metrics supported by 18 and 20",
              "final_tests_passed": final_tests["total_final_tests_passed"],
              "final_test_failures": 0, "final_test_skips": 0,
              "python_files_parsed": len(python_files), "markdown_targets_checked": links,
              "secret_scan_text_files": scanned, "secret_findings": findings,
              "ignore_probes_passed": len(probes), "compose_valid": True,
              "whitespace_checks_passed": True, "existing_file_candidates": len(paths),
              "pending_existing_files": len(pending),
              "pending_deletions": len(deletions),
              "total_pending_staging_paths": len(pending) + len(deletions), "total_staging_paths": len(paths) + len(deletions),
              "staged_file_count": len(staged), "dry_run_passed": True,
              "scope": "Read-only review; no fits, DAG runs, service starts/stops, SQL writes, index changes or publication",
              "limits": ["Classification scores checked against original records, not independently refit",
                         "Native F1 target not met; LLM path untested; overlapping native evaluation cohorts",
                         "Regression ports remain adaptations; final scores equal across all policies",
                         "Candidate validation predictions were not saved"]}
    (out / "checks.json").write_bytes((json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"report": relative + "/checks.json", **result}, indent=2))


if __name__ == "__main__":
    main()
