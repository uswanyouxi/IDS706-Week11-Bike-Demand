"""Mocked init readiness/failure/idempotence checks; no real Airflow execution."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
from contextlib import redirect_stdout
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('init_airflow', Path(__file__).resolve().parents[2] / 'scripts/init_airflow.py')
init = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init)
ADMIN = json.dumps([{'username': 'student', 'roles': ['Admin']}])


def result(stdout='', code=0):
    return SimpleNamespace(returncode=code, stdout=stdout)


class InitTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'AIRFLOW_ADMIN_USERNAME': 'student', 'AIRFLOW_ADMIN_PASSWORD': 'test-password-sentinel'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_db_readiness_is_bounded_and_blocks_migration(self):
        with patch.object(init.subprocess, 'run', return_value=result(code=1)) as run:
            with self.assertRaisesRegex(init.InitError, 'Database readiness failed'):
                init.main()
            run.assert_called_once_with(['airflow', 'db', 'check', '--retry', '20', '--retry-delay', '3'], text=True, capture_output=True, timeout=90)

    def test_failed_migration_blocks_user_creation(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(code=1)]) as run:
            with self.assertRaisesRegex(init.InitError, 'Metadata migration failed'):
                init.main()
            self.assertEqual(run.call_count, 2)

    def test_failed_migration_verification_blocks_user_lookup(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(code=1)]) as run:
            with self.assertRaisesRegex(init.InitError, 'Migration verification failed'):
                init.main()
            self.assertEqual(run.call_count, 3)

    def test_existing_admin_is_preserved(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(), result(ADMIN)]) as run:
            init.main()
            self.assertEqual(run.call_count, 4)
            self.assertFalse(any('create' in call.args[0] for call in run.call_args_list))

    def test_new_admin_is_created_then_role_verified(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(), result('[]'), result(), result(ADMIN)]) as run:
            init.main()
            self.assertEqual(run.call_args_list[4].args[0][1:3], ['users', 'create'])
            self.assertEqual(run.call_args_list[5].args[0], ['airflow', 'users', 'list', '--output', 'json'])

    def test_second_run_does_not_recreate_admin(self):
        first = [result(), result(), result(), result('[]'), result(), result(ADMIN)]
        second = [result(), result(), result(), result(ADMIN)]
        with patch.object(init.subprocess, 'run', side_effect=first+second) as run:
            init.main()
            init.main()
            self.assertEqual(sum('create' in call.args[0] for call in run.call_args_list), 1)

    def test_existing_nonadmin_fails_without_grant_or_reset(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(), result('[{"username":"student","roles":["Viewer"]}]')]) as run:
            with self.assertRaisesRegex(init.InitError, 'lacks the Admin role'):
                init.main()
            self.assertEqual(run.call_count, 4)

    def test_failed_user_creation_excludes_password_from_exception(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(), result('[]'), result('test-password-sentinel', code=1)]):
            with self.assertRaisesRegex(init.InitError, 'FAB admin creation failed') as ctx:
                init.main()
            self.assertNotIn('test-password-sentinel', str(ctx.exception))

    def test_missing_user_after_successful_create_fails(self):
        with patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(), result('[]'), result(), result('[]')]):
            with self.assertRaisesRegex(init.InitError, 'not present after creation'):
                init.main()

    def test_malformed_users_json_fails(self):
        for payload in ['not-json', '{}', '[null]']:
            with self.subTest(payload=payload), patch.object(init.subprocess, 'run', side_effect=[result(), result(), result(), result(payload)]):
                with self.assertRaises(init.InitError):
                    init.main()

    def test_timeout_does_not_expose_secret_argv(self):
        secret = 'test-password-sentinel'
        with patch.object(init.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['airflow','--password',secret], 120)):
            with self.assertRaises(init.InitError) as ctx:
                init.run_cli(['users','create','--password',secret], 'FAB admin creation')
            self.assertNotIn(secret, str(ctx.exception))

    def test_placeholder_credentials_fail_before_cli(self):
        with patch.dict(os.environ, {'AIRFLOW_ADMIN_PASSWORD': 'REPLACE_ME'}), patch.object(init.subprocess, 'run') as run:
            with self.assertRaises(init.InitError):
                init.main()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()