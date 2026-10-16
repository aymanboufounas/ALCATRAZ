"""Exercise check-runner failure containment and durable reports without Unity."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_source_checks import Check, build_checks, run_checks


class SourceCheckRunnerTests(unittest.TestCase):
    def run_isolated(self, checks, timeout=5):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        reports = root / "reports"
        with contextlib.redirect_stdout(io.StringIO()):
            report = run_checks(checks, root, reports, timeout)
        saved = json.loads((reports / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(report, saved)
        self.assertFalse(saved["unity_runtime_verified"])
        return report, reports

    def test_failure_does_not_prevent_independent_checks(self):
        # The second command must not execute after its own compile-like step fails.
        checks = [
            Check("fails", ((sys.executable, "-c", "print('compiler failed'); raise SystemExit(7)"),
                            (sys.executable, "-c", "print('must not execute')"))),
            Check("continues", ((sys.executable, "-c", "print('independent check ran')"),)),
        ]
        report, reports = self.run_isolated(checks)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["completed_checks"], 2)
        self.assertEqual(report["failed_checks"], 1)
        self.assertEqual(report["checks"][0]["commands"][0]["exit_code"], 7)
        self.assertEqual(len(report["checks"][0]["commands"]), 1)
        self.assertIn("compiler failed", (reports / "fails.log").read_text())
        self.assertNotIn("must not execute", (reports / "fails.log").read_text())
        self.assertIn("independent check ran", (reports / "continues.log").read_text())
        summary = (reports / "summary.md").read_text()
        self.assertIn("fails | FAILED", summary)
        self.assertIn("continues | PASSED", summary)

    def test_missing_executable_is_a_reported_failure(self):
        report, reports = self.run_isolated([
            Check("missing", (("/alcatraz-test-nonexistent/compiler",),)),
            Check("still_runs", ((sys.executable, "-c", "print('ok')"),)),
        ])
        self.assertEqual(report["status"], "failed")
        self.assertIn("error", report["checks"][0]["commands"][0])
        self.assertEqual(report["checks"][1]["status"], "passed")
        self.assertIn("Could not execute command", (reports / "missing.log").read_text())

    def test_timeout_is_a_failure_and_does_not_block_following_check(self):
        report, _ = self.run_isolated([
            Check("times_out", ((sys.executable, "-c", "import time; time.sleep(5)"),)),
            Check("after_timeout", ((sys.executable, "-c", "print('finished')"),)),
        ], timeout=0.2)
        self.assertEqual(report["checks"][0]["commands"][0]["error"], "timeout")
        self.assertEqual(report["checks"][1]["status"], "passed")

    def test_success_produces_complete_report(self):
        report, reports = self.run_isolated([
            Check("successful", ((sys.executable, "-c", "print('verified')"),)),
        ])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["completed_checks"], report["total_checks"])
        self.assertEqual(report["failed_checks"], 0)
        self.assertFalse(list(reports.glob("*.tmp")))

    def test_cli_returns_failure_for_unavailable_tools_and_writes_reports(self):
        with tempfile.TemporaryDirectory(prefix="alcatraz check root ") as temporary:
            root = Path(temporary)
            reports = root / "external reports"
            missing_tool = str(root / "not installed")
            runner = Path(__file__).resolve().parents[1] / "run_source_checks.py"
            process = subprocess.run([
                sys.executable, str(runner), "--root", str(root),
                "--report-dir", str(reports), "--python", missing_tool,
                "--mcs", missing_tool, "--mono", missing_tool,
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
            self.assertEqual(process.returncode, 1, process.stdout)
            report = json.loads((reports / "results.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["completed_checks"], report["total_checks"])
            self.assertEqual(report["failed_checks"], report["total_checks"])
            self.assertTrue((reports / "summary.md").exists())

    def test_nonwriting_compiler_cannot_reuse_a_previous_executable(self):
        with tempfile.TemporaryDirectory(prefix="alcatraz repeated check ") as temporary:
            root = Path(temporary)
            reports = root / "reports"
            (reports / "bin").mkdir(parents=True)
            stale_binary = reports / "bin/HoldemTests.exe"
            stale_binary.write_bytes(b"previous passing build")
            compiler = root / "compiler"
            compiler.write_text("#!/bin/sh\nexit 0\n")
            compiler.chmod(0o700)
            runtime = root / "runtime"
            runtime.write_text('#!/bin/sh\n[ -f "$1" ]\n')
            runtime.chmod(0o700)
            checks = build_checks(root, reports, sys.executable, str(compiler), str(runtime))
            holdem = next(check for check in checks if check.name == "HoldemTests")
            with contextlib.redirect_stdout(io.StringIO()):
                report = run_checks([holdem], root, reports)
            self.assertFalse(stale_binary.exists())
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["checks"][0]["commands"][0]["exit_code"], 0)
            self.assertNotEqual(report["checks"][0]["commands"][1]["exit_code"], 0)

    def test_cli_rejects_nonfinite_and_nonpositive_timeouts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = Path(__file__).resolve().parents[1] / "run_source_checks.py"
            for timeout in ("nan", "inf", "-inf", "0", "-1"):
                with self.subTest(timeout=timeout):
                    reports = root / timeout
                    process = subprocess.run([
                        sys.executable, str(runner), "--root", str(root),
                        "--report-dir", str(reports), "--check-timeout=" + timeout,
                    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
                    self.assertEqual(process.returncode, 2, process.stdout)
                    self.assertIn("finite and positive", process.stdout)
                    self.assertFalse(reports.exists())


if __name__ == "__main__":
    unittest.main()
