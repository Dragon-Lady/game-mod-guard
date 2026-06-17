import tempfile
import unittest
import zipfile
from pathlib import Path

from game_mod_guard import scan_target


def write_zip(path, names):
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, "sample")


class GameModGuardTests(unittest.TestCase):
    def test_safe_looking_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "tractor.zip"
            write_zip(mod, ["modDesc.xml", "vehicle.i3d", "textures/body.dds"])

            report = scan_target(mod, defender=False)

        self.assertEqual(report.verdict, "SAFE-LOOKING")

    def test_executable_in_zip_is_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "tractor.zip"
            write_zip(mod, ["modDesc.xml", "setup.exe"])

            report = scan_target(mod, defender=False)

        self.assertEqual(report.verdict, "STOP")
        self.assertTrue(any(f.issue.startswith("executable-style") for f in report.findings))

    def test_script_in_zip_is_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "tractor.zip"
            write_zip(mod, ["modDesc.xml", "install.ps1"])

            report = scan_target(mod, defender=False)

        self.assertEqual(report.verdict, "REVIEW")

    def test_nested_archive_is_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "tractor.zip"
            write_zip(mod, ["modDesc.xml", "extra/download.zip"])

            report = scan_target(mod, defender=False)

        self.assertEqual(report.verdict, "REVIEW")


if __name__ == "__main__":
    unittest.main()
