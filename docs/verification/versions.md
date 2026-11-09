# Version and compatibility evidence — Phase A

Verified on November 8, 2026 (America/New_York). `scripts/check_pins.py` fetched
public PyPI JSON for every direct package pin and inspected all three base-image
manifests without pulling them or starting containers. Results and metadata are
in `pins.json`: every requested release exists, all three images advertise
linux/amd64, and their Python requirements include Python 3.11.

Airflow 3.4.0 itself and the selected providers require Python >=3.11. Use the
Python 3.11 Airflow image, not a guessed Python 3.10 variant. The local host's
3.11.9 launcher is sufficient for verifier scripts; it does not pin the Python
patch release bundled inside Airflow's 3.11 image. The separate ML base is pinned
to Python 3.11.14. PostgreSQL 16 follows the major version of the official
versioned Compose reference; this project pins 16.11-bookworm for both instances.

The official Airflow Python 3.11 constraints were downloaded directly from:
https://raw.githubusercontent.com/apache/airflow/constraints-3.4.0/constraints-3.11.txt

Vendored file: `requirements/airflow-constraints-3.11.txt`; SHA-256:
`22ac327cdf6fe75b8d873ab363455bbe0645c03cee3e3896c6513d583c25e5f8`.
Provider pins match this file. Our Airflow Dockerfile installs with this constraint
and explicitly repeats `apache-airflow==3.4.0` to prevent accidental core upgrades.
The ML/dashboard dependencies are isolated in a different image.

## Resolver checks actually performed

These are **pip dry-runs**, with no package installation. Both final checks
produced successful resolution reports. Compact resolved versions/counts and the
resolver's actual environment metadata are in `resolution-summary.json`; the large
raw pip reports are ignored local evidence. Native Windows marker evaluation can
still differ from a Linux install even when target wheel platforms are supplied.
Thus this is compatibility evidence, not proof of a built Linux runtime.

Initial ML command failed because its target wheel list omitted older manylinux
tags used by Streamlit's watchdog dependency. Adding those compatible tags let
pip resolve the pinned package set; no package was silently replaced and the
Streamlit pin did not change. The final exact PowerShell commands were:

```powershell
py -3.11 -m pip install --dry-run --ignore-installed --only-binary=:all: --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64 --platform manylinux_2_34_x86_64 --python-version 3.11 --implementation cp --abi cp311 --report docs/verification/airflow-resolution.json --constraint requirements/airflow-constraints-3.11.txt --requirement requirements/airflow.txt --quiet
py -3.11 -m pip install --dry-run --ignore-installed --only-binary=:all: --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64 --platform manylinux_2_34_x86_64 --platform manylinux_2_5_x86_64 --platform manylinux1_x86_64 --platform manylinux_2_12_x86_64 --platform manylinux2010_x86_64 --python-version 3.11 --implementation cp --abi cp311 --report docs/verification/ml-resolution.json --requirement requirements/ml.txt --quiet
```

Direct dependencies are pinned. The ML transitive set is recorded from this probe
but is not a Linux hash lock; image builds must run `pip check` and record actual
Linux package versions. Image tags are release pins, not immutable digest pins.
`manifest_sha256` in pins.json hashes the CLI manifest output, **not** a canonical
registry digest suitable for `FROM image@sha256:...`.

## Local scaffold checks

- `docker compose config --quiet`: succeeded after `.env` generation.
- `docker compose --profile ml config --quiet`: succeeded.
- Services resolved: storage-init, airflow-db, app-db, airflow-init,
  airflow-apiserver, airflow-scheduler, airflow-dag-processor, dashboard, ml-runner.
- Python AST parsing: six project Python files parsed successfully.
- Git ignore checks: `.env`, raw day.csv and large resolver reports are ignored.
- No tracked files or commits exist yet; repository initialized locally only.

PowerShell execution policy rejected the first `.ps1` secret-generator invocation.
No execution policy was weakened. Setup now uses `py -3.11 scripts/new_local_env.py`;
it generated `.env` without displaying credentials. An initial report-summary
read hit Windows' default GBK encoding; reading JSON explicitly as UTF-8 fixed it.
These failed attempts are not counted as successful checks.

Git's elevated-user commands encountered dubious ownership because sandbox
`git init` created .git as CodexSandboxOffline. Verification uses a one-command
safe.directory override for this exact project, without a global trust change:

```powershell
git -c safe.directory='D:/未来/IDS706/IDS706-Week11-Bike-Demand' status --short
git -c safe.directory='D:/未来/IDS706/IDS706-Week11-Bike-Demand' check-ignore .env
```

Use the same prefix for later Git commands if the IDE user sees the ownership
check. Do not globally trust every directory. No files were staged, no commit
was created, and no remote was configured or contacted by Git.

## Official design references read

- https://airflow.apache.org/docs/apache-airflow/3.4.0/howto/docker-compose/index.html
- https://airflow.apache.org/docs/apache-airflow/3.4.0/docker-compose.yaml
- https://airflow.apache.org/docs/apache-airflow/3.4.0/core-concepts/executor/index.html
- https://docs.langchain.com/oss/python/langgraph/graph-api
- PyPI release JSON URLs are recorded for each pin in pins.json.

No Docker build, service startup, `pip check` inside a container, DAG import/run,
database load or ML execution occurred. Those runtime checks remain pending.