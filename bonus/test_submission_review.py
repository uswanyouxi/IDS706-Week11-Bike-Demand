"""Counterexamples for documentation exceptions and unchanged-source safeguards."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("review", Path(__file__).with_name("review_submission.py"))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def frozen(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"original evidence\n")
        return {name: {"sha256": review.digest(path), "mtime_ns": path.stat().st_mtime_ns}}

    def test_authorized_readme_rewrite(self):
        snapshot = self.frozen("README.md")
        (self.root / "README.md").write_bytes(b"Concise final results\n")
        self.assertEqual(review.check_preservation(self.root, snapshot, review.AUTHORIZED), 0)

    def test_authorization_is_exact_not_directory_wide(self):
        self.assertNotIn("docs/verification/phase-c/report.json", review.AUTHORIZED)
        self.assertNotIn("bonus/native-classroom/run_native_loop.py", review.AUTHORIZED)

    def test_source_changes_rejected(self):
        for name in ["dags/dc_bike_weather.py", "src/bike_demand_ml/graph.py",
                     "src/bike_demand_bonus/evaluation.py", "tests/bonus/test_adaptive.py",
                     "compose.yaml", "requirements/ml.txt"]:
            with self.subTest(path=name):
                snapshot = self.frozen(name)
                (self.root / name).write_bytes(b"changed\n")
                with self.assertRaises(AssertionError):
                    review.check_preservation(self.root, snapshot, review.AUTHORIZED)

    def test_frozen_log_change_rejected(self):
        snapshot = self.frozen("old.log")
        (self.root / "old.log").write_bytes(b"trimmed evidence\n")
        with self.assertRaises(AssertionError):
            review.check_preservation(self.root, snapshot)

    def test_timestamp_change_rejected(self):
        snapshot = self.frozen("old.csv")
        path = self.root / "old.csv"
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10000000))
        with self.assertRaises(AssertionError):
            review.check_preservation(self.root, snapshot)

    def test_missing_evidence_rejected(self):
        snapshot = self.frozen("capture.png")
        (self.root / "capture.png").unlink()
        with self.assertRaises(AssertionError):
            review.check_preservation(self.root, snapshot)

    def test_exact_rename_preserves_bytes_and_timestamp(self):
        old = "screenshots/14_bonus_agent_metrics.png"
        snapshot = self.frozen(old)
        (self.root / old).rename(self.root / review.RENAMED[old])
        self.assertEqual(review.check_preservation(self.root, snapshot, renames=review.RENAMED), 1)

    def test_rename_does_not_allow_substitution(self):
        old = "screenshots/14_bonus_agent_metrics.png"
        snapshot = self.frozen(old)
        target = self.root / review.RENAMED[old]
        (self.root / old).rename(target)
        target.write_bytes(b"substituted image")
        with self.assertRaises(AssertionError):
            review.check_preservation(self.root, snapshot, renames=review.RENAMED)

    def test_only_reviewed_image_names_allowed(self):
        text = "\n".join("!/screenshots/" + name for name in review.SCREENSHOTS)
        review.screenshot_allowlist(text, review.SCREENSHOTS)
        for invalid in [text + "\n!/screenshots/unreviewed.png", text.replace("20_native_and_regression_scopes.png", "optional.png")]:
            with self.assertRaises(AssertionError):
                review.screenshot_allowlist(invalid, review.SCREENSHOTS)

    def test_secret_cache_and_volume_paths_rejected(self):
        paths = [".env", "artifacts/native-classroom-local/.env", ".venv/x.py",
                 "volumes/postgres/file", "src/__pycache__/x.pyc", "build/temp.py"]
        self.assertEqual(review.forbidden(paths), paths)
        self.assertEqual(review.forbidden([".env.example", "README.md", "bonus/review_submission.py"]), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
