"""Checked container initialization for Airflow 3.4.0 + FAB.

The official entrypoint sets umask 0002, but a direct Python command does not
receive its component-specific DB wait. Perform our own bounded DB check first.
"""
import json
import os
import subprocess


class InitError(RuntimeError):
    """Safe stage-level error with no credentials or command arguments."""


def run_cli(arguments, stage, *, timeout=120):
    print(f'Initializing: {stage}', flush=True)
    try:
        result = subprocess.run(['airflow', *arguments], text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise InitError(f'{stage} could not complete within its execution limits') from None
    if result.returncode:
        # Neither argv nor raw CLI output is echoed: either may contain secrets.
        raise InitError(f'{stage} failed with exit code {result.returncode}')
    return result.stdout


def read_users(stage):
    try:
        users = json.loads(run_cli(['users', 'list', '--output', 'json'], stage))
    except (TypeError, json.JSONDecodeError):
        raise InitError(f'{stage} returned invalid JSON') from None
    if not isinstance(users, list) or any(not isinstance(user, dict) for user in users):
        raise InitError(f'{stage} returned an unexpected user-list shape')
    return users


def find_admin(users, username):
    matches = [user for user in users if user.get('username') == username]
    if len(matches) > 1:
        raise InitError('FAB returned duplicate usernames')
    if not matches:
        return None
    # FAB users-list exposes roles; Airflow's JSON formatter emits a list of names.
    roles = matches[0].get('roles')
    if not isinstance(roles, list) or 'Admin' not in roles:
        raise InitError('Existing FAB user lacks the Admin role; inspect it manually')
    return matches[0]


def main():
    username = os.environ.get('AIRFLOW_ADMIN_USERNAME', '')
    password = os.environ.get('AIRFLOW_ADMIN_PASSWORD', '')
    if not username.strip() or not password.strip() or password == 'REPLACE_ME':
        raise InitError('A real local admin username/password is required')
    run_cli(['db', 'check', '--retry', '20', '--retry-delay', '3'], 'Database readiness', timeout=90)
    run_cli(['db', 'migrate'], 'Metadata migration', timeout=600)
    run_cli(['db', 'check-migrations', '--migration-wait-timeout', '60'], 'Migration verification', timeout=90)
    if find_admin(read_users('FAB user lookup'), username) is not None:
        print('Metadata ready; existing FAB administrator preserved (password not reset).')
        return
    run_cli(['users', 'create', '--username', username, '--firstname', 'Course',
             '--lastname', 'Student', '--email', 'student@example.invalid',
             '--role', 'Admin', '--password', password], 'FAB admin creation')
    if find_admin(read_users('FAB admin verification'), username) is None:
        raise InitError('FAB administrator was not present after creation')
    print('Metadata ready; local FAB administrator created and role verified.')


if __name__ == '__main__':
    try:
        main()
    except InitError as exc:
        raise SystemExit(f'Airflow initialization failed: {exc}') from None
    except Exception:
        raise SystemExit('Airflow initialization failed unexpectedly; no command arguments were logged.') from None