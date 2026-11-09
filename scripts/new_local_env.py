"""Generate local secrets without changing PowerShell execution policy."""
import base64
from pathlib import Path
import secrets

target = Path(__file__).resolve().parents[1] / '.env'
values = dict(AIRFLOW_UID='50000', AIRFLOW_META_PASSWORD=secrets.token_hex(32),
              APP_DB_PASSWORD=secrets.token_hex(32), AIRFLOW_JWT_SECRET=secrets.token_hex(32),
              AIRFLOW_API_SECRET_KEY=secrets.token_hex(32),
              AIRFLOW_FERNET_KEY=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
              AIRFLOW_ADMIN_USERNAME='student', AIRFLOW_ADMIN_PASSWORD=secrets.token_hex(32))
try:
    with target.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(''.join(f'{k}={v}\n' for k, v in values.items()))
except FileExistsError:
    raise SystemExit('.env already exists; refusing to overwrite local secrets.')
print('Created ignored .env; credentials were not printed. Keep the file private.')