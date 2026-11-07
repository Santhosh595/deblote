"""Tests for deblote — run: python -m unittest discover -s tests -v"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from deblote import Report, CleanTarget, clean_target, human, windows_targets


class TestDeblote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_tree(self, name, files=3, size=1000):
        d = self.base / name
        sub = d / "sub"
        sub.mkdir(parents=True)
        for i in range(files):
            (d / f"f{i}.txt").write_text("x" * size)
            (sub / f"g{i}.txt").write_text("y" * size)
        return d

    def test_dry_run_deletes_nothing(self):
        d = self._make_tree("Temp")
        r = Report(when="t", dry_run=True)
        clean_target(CleanTarget("Temp", d), True, r)
        self.assertTrue(any(d.rglob("*.txt")), "dry-run must not delete")
        self.assertGreater(r.freed_bytes, 0)

    def test_clean_removes_contents_keeps_dir(self):
        d = self._make_tree("Temp")
        r = Report(when="t", dry_run=False)
        clean_target(CleanTarget("Temp", d), False, r)
        self.assertTrue(d.exists(), "folder itself must remain")
        self.assertFalse(any(d.rglob("*.txt")), "contents must be gone")
        self.assertGreater(r.freed_bytes, 0)

    def test_missing_path_is_not_an_error(self):
        r = Report(when="t", dry_run=False)
        clean_target(CleanTarget("Nope", self.base / "does-not-exist"), False, r)
        self.assertEqual(r.targets[0]["status"], "not present")
        self.assertEqual(r.errors, [])

    def test_user_folders_are_never_targets(self):
        names = " ".join(t.name.lower() for t in windows_targets())
        for protected in ("documents", "desktop", "pictures", "downloads"):
            self.assertNotIn(protected, names,
                             f"windows_targets must never include {protected}")

    def test_human(self):
        self.assertEqual(human(500), "500 B")
        self.assertIn("KB", human(2048))
        self.assertIn("MB", human(5 * 1024 * 1024))
        self.assertIn("GB", human(2 * 1024 * 1024 * 1024))


if __name__ == "__main__":
    unittest.main()
