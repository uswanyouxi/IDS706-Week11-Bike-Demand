"""Atomic run artifacts. No host cache fallback."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid

def now():
    return datetime.now(timezone.utc).isoformat()

def run_key(run_id):
    return hashlib.sha256(run_id.encode()).hexdigest()[:24]

def data_dir(run_id):
    return Path(os.environ.get("PROJECT_DATA_DIR", "/opt/project/data")) / "runs" / run_key(run_id)

def artifact_dir(run_id):
    return Path(os.environ.get("PROJECT_ARTIFACT_DIR", "/opt/project/artifacts")) / "pipeline" / run_key(run_id)

def atomic_bytes(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(payload)
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()

def write_json(path, body):
    atomic_bytes(path, (json.dumps(body, indent=2, sort_keys=True, allow_nan=False)+"\n").encode())
    return str(path)

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
