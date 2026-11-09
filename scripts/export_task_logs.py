"""Export real task logs to Windows-safe hashed run folders; starts no containers."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/verification/phase-b/airflow-task-logs"
reader = """
import base64,json
from pathlib import Path
root=Path('/opt/airflow/logs/dag_id=dc_bike_weather_daily')
records=[dict(path=str(p.relative_to(root)),body=base64.b64encode(p.read_bytes()).decode()) for p in sorted(root.rglob('*.log'))]
print(json.dumps(records))
"""
result=subprocess.run(["docker","compose","exec","-T","airflow-scheduler","python","-c",reader],
    cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60)
if result.returncode:
    raise SystemExit("Task-log read failed; check the Part 1 container state.")
import base64
records=json.loads(result.stdout)
secret_values=[]
for line in (ROOT/".env").read_text(encoding="utf-8").splitlines():
    if "=" in line:
        name,value=line.split("=",1)
        if any(word in name for word in ["PASSWORD","SECRET","KEY"]) and len(value)>12:
            secret_values.append(value)
manifest=[]
for record in records:
    parts=record["path"].split("/")
    run_id=parts[0].removeprefix("run_id=")
    key=hashlib.sha256(run_id.encode()).hexdigest()[:24]
    safe_parts=[re.sub(r'[^A-Za-z0-9._=-]','_',p) for p in parts[1:]]
    path=OUT/key/Path(*safe_parts)
    path.parent.mkdir(parents=True,exist_ok=True)
    text=base64.b64decode(record["body"]).decode("utf-8",errors="replace")
    for value in secret_values:
        text=text.replace(value,"[REDACTED]")
    path.write_text(text,encoding="utf-8")
    manifest.append(dict(original_linux_relative_path=record["path"],exported_path=str(path.relative_to(ROOT)),bytes=path.stat().st_size))
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print(f"Exported {len(manifest)} actual task logs with Windows-safe names; raw secret values were not printed.")
