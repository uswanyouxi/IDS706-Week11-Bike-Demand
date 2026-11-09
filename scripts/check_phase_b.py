"""Host-only Phase B checks. Does not build/start Docker or contact a DB."""
import ast
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
OUT=ROOT/"docs/verification/phase-b"
OUT.mkdir(parents=True,exist_ok=True)
env={**os.environ,"PYTHONIOENCODING":"utf-8"}
proc=subprocess.run([sys.executable,"-m","pytest","-q","-ra",
    "--junitxml="+str(OUT/"host-tests.xml")],cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8")
(OUT/"host-tests.log").write_text(proc.stdout+proc.stderr,encoding="utf-8")
print(proc.stdout)
files=list((ROOT/"src").rglob("*.py"))+list((ROOT/"dags").glob("*.py"))+list((ROOT/"tests").rglob("*.py"))
for path in files:
    ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
from bike_demand.contracts import clean_bike,clean_weather,merge_dates,dataset_hash
raw=ROOT/"data/raw"
bike,bike_report=clean_bike((raw/"day.csv").read_bytes())
weather,weather_report=clean_weather(json.loads((raw/"open-meteo-era5-2011-2012.json").read_text(encoding="utf-8")))
merged,merge_report=merge_dates(bike,weather)
summary=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),phase="B",
    pytest_exit_code=proc.returncode,python_ast_files=len(files),
    host_versions={k:importlib.metadata.version(k) for k in ["pandas","numpy","psycopg","requests","matplotlib","pytest"]},
    cached_source_probe={"note":"Prior real downloads, not a DAG/DB run",
        "bike":bike_report,"weather":weather_report,"merge":merge_report,"dataset_hash":dataset_hash(merged)},
    actual_dag_parse="pending real Linux Airflow",actual_database_rows=None,actual_dag_runs=[],
    part2="not implemented")
(OUT/"host-checks.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
raise SystemExit(proc.returncode)
