"""Read-only package/image metadata verification; writes evidence, installs nothing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'verification'


def main():
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'packages': {}, 'images': {}}
    for file in ('airflow.txt', 'ml.txt', 'dev.txt'):
        for line in (ROOT / 'requirements' / file).read_text().splitlines():
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^ ]+)', line)
            if not match:
                continue
            name, version = match.groups()
            key = f'{name}=={version}'
            if key in result['packages']:
                continue
            url = f'https://pypi.org/pypi/{name}/{version}/json'
            try:
                with urllib.request.urlopen(url, timeout=45) as response:
                    body = json.load(response)
                result['packages'][key] = dict(status='verified-release', url=url,
                    requires_python=body['info']['requires_python'],
                    requires_dist=body['info']['requires_dist'],
                    has_wheels=any(f['packagetype'] == 'bdist_wheel' for f in body['urls']))
            except Exception as exc:
                result['packages'][key] = dict(status='unverified', url=url, error=str(exc))
    for image in ('apache/airflow:3.4.0-python3.11', 'python:3.11.14-slim-bookworm', 'postgres:16.11-bookworm'):
        proc = subprocess.run(['docker', 'manifest', 'inspect', image], capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=120)
        try:
            body = json.loads(proc.stdout)
            result['images'][image] = dict(status='verified-manifest' if proc.returncode == 0 else 'unverified',
                platforms=[m.get('platform') for m in body.get('manifests', [])],
                manifest_sha256=hashlib.sha256(proc.stdout.encode()).hexdigest())
        except ValueError:
            result['images'][image] = dict(status='unverified', exit_code=proc.returncode, error=proc.stderr[-1000:])
    constraint = ROOT / 'requirements' / 'airflow-constraints-3.11.txt'
    result['airflow_constraints'] = dict(
        url='https://raw.githubusercontent.com/apache/airflow/constraints-3.4.0/constraints-3.11.txt',
        sha256=hashlib.sha256(constraint.read_bytes()).hexdigest())
    (OUT / 'pins.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({**result, 'packages': {k: {x: v[x] for x in ('status', 'requires_python') if x in v}
                                         for k, v in result['packages'].items()}}, indent=2))
    return int(any(v['status'] == 'unverified' for group in ('packages', 'images') for v in result[group].values()))


if __name__ == '__main__':
    raise SystemExit(main())
