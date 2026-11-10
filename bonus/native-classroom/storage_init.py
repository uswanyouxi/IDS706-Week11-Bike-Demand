"""Initialize only new native-project volume directories; no recursive chmod."""
import json,os
from pathlib import Path
PATHS=["/repo","/repo/datasets","/repo/datasets/airflow","/repo/artifacts",
       "/repo/artifacts/airflow","/repo/artifacts/airflow/runs","/opt/airflow/logs","/evidence"]
for name in PATHS:
    p=Path(name);p.mkdir(parents=True,exist_ok=True)
    os.chown(p,50000,0);os.chmod(p,0o2775)
space=os.statvfs("/repo")
print(json.dumps({"initialized":PATHS,"filesystem_available_bytes":space.f_bavail*space.f_frsize}))
