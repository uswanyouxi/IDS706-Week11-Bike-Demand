# Local environment — checked November 8, 2026, America/New_York

The sandbox initially denied Docker config/pipe access, WSL service enumeration,
CIM memory/disk reads and execution of the Microsoft Store Python launcher.
Approved read-only commands outside the sandbox succeeded. These are permission
differences, not evidence that Docker/WSL/Python are absent.

| Check | Actual result |
| --- | --- |
| Windows | Windows 11 Home China, 10.0.26200 |
| Docker CLI / engine | 29.7.2 / 29.7.2 |
| Docker Compose | v5.4.0 (above guide minimum v2.14) |
| Active Docker context | desktop-linux |
| Engine OS / logical CPUs | linux / 20 |
| Engine MemTotal | 8,215,236,608 bytes, approximately 7.65 GiB |
| WSL default / default version | docker-desktop / 2 |
| WSL distro listing | docker-desktop, Stopped, version 2 at that instant |
| Python | `python` not on PATH; `py -3.11 --version` = Python 3.11.9 |
| Git | 2.55.0.windows.3 |
| Host total visible RAM | 16,564,728 KiB, approximately 15.80 GiB |
| Host free physical RAM | 1,635,864 KiB, approximately 1.56 GiB at check time |
| C: size / free | 214,749,409,280 / 10,992,222,208 bytes (10.24 GiB free) |
| D: size / free | 294,972,813,312 / 53,220,241,408 bytes (49.57 GiB free) |
| User .wslconfig | no contents returned by existence-guarded check; no settings changed |
| Git repository | absent initially; `git init` subsequently succeeded locally |

`wsl.exe` emitted UTF-16 output imperfectly decoded by the command capture; the
ASCII distro name, state and version were legible. Docker API simultaneously
reported a reachable Linux engine. Do not resolve that transient disagreement by
asserting a Linux shell was tested: no command inside a WSL distro was executed.

Exact diagnostic commands used:

```powershell
docker --version
docker compose version
docker info --format 'Server={{.ServerVersion}} OS={{.OSType}} CPUs={{.NCPU}} MemoryBytes={{.MemTotal}}'
docker context show
wsl --status
wsl --list --verbose
python --version
py --list-paths
py -3.11 --version
git --version
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,TotalVisibleMemorySize,FreePhysicalMemory
Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Format-List DeviceID,Size,FreeSpace
if (Test-Path -LiteralPath "$env:USERPROFILE\.wslconfig") { Get-Content -LiteralPath "$env:USERPROFILE\.wslconfig" }
```

The initial `docker info --format '{{json .}}'` failed in the sandbox; its empty
server fields were discarded and never treated as zero real RAM. Initial
`Get-PSDrive` free-space values were also unavailable, so the approved CIM read
supplies the actual disk values above.

## Runtime blockers / unverified items

Free host memory is low, and engine RAM is slightly below the preferred 8 GiB.
C: has little headroom for large image layers and a growing WSL virtual disk.
The user has now confirmed Docker Desktop's WSL2 disk image is on C:, with
about 9.9 GB free, and will move it to D: using Docker Desktop settings themselves.
No Docker files/settings were changed by this review. After that move, verify
the new location/free space; virtual-disk free space and peak stack consumption
remain unverified. Release host memory before startup. Moving the project alone
does not relocate Docker volumes or image layers.

No image build, container startup, metadata migration, task import, scheduled run,
application DB schema/load, EDA or training was performed. Consequently the
container design is **not runtime-verified**. No destructive operations, software
installation, WSL shutdown, resource reallocation, prune, push or deployment ran.

## Windows setup follow-up

PowerShell execution policy blocks .ps1 scripts on this machine. The documented
setup uses Python's standard-library `scripts/new_local_env.py` instead; no policy
change was made. It created ignored local credentials without printing them.
Git initialized under the sandbox account, so elevated commands require the
project-scoped safe.directory prefix shown in versions.md. No global Git config
was changed. The sandbox runner subsequently failed its setup refresh, so final
workspace edits/checks required outside-sandbox execution approval.
## Current Phase B runtime verification

The measurements/limitations above describe the original Phase A checks. The
approved Phase B test now confirms Docker disk files on D:, successful builds,
migrations, health, real scheduled/manual DAG runs, PostgreSQL loads and EDA.
See [phase-b/status.md](phase-b/status.md) for current evidence and remaining
submission screenshots. No system settings or Docker data were moved/deleted.
