$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$targetPath = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $targetPath) { throw '.env already exists; refusing to overwrite local secrets.' }
function New-HexSecret {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
$keyBytes = New-Object byte[] 32
$keyRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $keyRng.GetBytes($keyBytes) } finally { $keyRng.Dispose() }
$fernet = [Convert]::ToBase64String($keyBytes).Replace('+', '-').Replace('/', '_')
$lines = @(
    'AIRFLOW_UID=50000'
    "AIRFLOW_META_PASSWORD=$(New-HexSecret)"
    "APP_DB_PASSWORD=$(New-HexSecret)"
    "AIRFLOW_JWT_SECRET=$(New-HexSecret)"
    "AIRFLOW_FERNET_KEY=$fernet"
    'AIRFLOW_ADMIN_USERNAME=student'
    "AIRFLOW_ADMIN_PASSWORD=$(New-HexSecret)"
)
[IO.File]::WriteAllLines($targetPath, $lines, (New-Object Text.UTF8Encoding($false)))
Write-Output 'Created ignored .env. View the admin password locally; do not paste it into logs or git.'
