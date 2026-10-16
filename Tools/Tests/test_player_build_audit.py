"""Exercise export qualification with tiny synthetic files, never a claimed game build."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_player_build import audit_build, EXPECTED_SCENES, RECEIPT_NAME, REQUIRED_FILES


def native_header():
    """Minimal PE headers test structural checks; these bytes cannot run a game."""
    data = bytearray(256)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<H", data, 132, 0x8664)
    struct.pack_into("<H", data, 148, 112)
    struct.pack_into("<H", data, 152, 0x20B)
    return bytes(data)


class PlayerBuildAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="Alcatraz export fixture ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "Windows player with spaces"
        self.root.mkdir()
        for name in REQUIRED_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(native_header() if name in ("AlcatrazEscape.exe", "UnityPlayer.dll") else b"synthetic fixture: " + name.encode())
        self.receipt = {
            "schemaVersion": 2, "receiptKind": "AlcatrazWindowsPlayer",
            "builtUtc": "2026-10-16T15:00:00.0000000Z", "buildGuid": "1" * 32,
            "target": "StandaloneWindows64", "executable": "AlcatrazEscape.exe", "result": "Succeeded",
            "unityVersion": "6000.0.62f1", "contextCaptured": True,
            "scenes": list(EXPECTED_SCENES), "buildOptions": "None", "buildOptionsValue": 0,
            "developmentBuild": False, "source": {"available": True, "commit": "a" * 40, "dirty": False},
            "targetInstalledBytes": 5_000_000_000, "runtimeVerified": False, "finishedGameVerified": False,
            "unreportedFiles": [], "installedFiles": [], "largestPackedContributors": [],
        }
        self.refresh_inventory()

    def refresh_inventory(self):
        rows = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.name in (RECEIPT_NAME, RECEIPT_NAME + ".sha256"):
                continue
            data = path.read_bytes()
            rows.append({"path": path.relative_to(self.root).as_posix(), "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest(), "reportedByUnity": True,
                         "unityReportedBytes": len(data), "unityRole": "synthetic fixture"})
        self.receipt["installedFiles"] = rows
        total = sum(row["bytes"] for row in rows)
        self.receipt.update(installedPlayerBytes=total, reportedPlayerBytes=total,
                            installedDecimalGB=total / 1_000_000_000, installedGiB=total / 1_073_741_824,
                            targetMet=total >= 5_000_000_000)
        self.write_receipt()

    def write_receipt(self):
        data = (json.dumps(self.receipt, indent=2) + "\n").encode()
        self.write_raw_receipt(data)

    def write_raw_receipt(self, data):
        (self.root / RECEIPT_NAME).write_bytes(data)
        (self.root / (RECEIPT_NAME + ".sha256")).write_text(
            hashlib.sha256(data).hexdigest() + "  " + RECEIPT_NAME + "\n", encoding="utf-8")

    def assert_fails(self, phrase, **options):
        result = audit_build(self.root, **options)
        self.assertFalse(result["passed"], result)
        self.assertIn(phrase, "\n".join(result["issues"]), result)
        self.assertFalse(result["runtime_verified"])
        self.assertFalse(result["finished_game_verified"])
        return result

    def test_small_export_integrity_passes_without_size_or_gameplay_claim(self):
        result = audit_build(self.root)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["installed_player_bytes"], self.receipt["installedPlayerBytes"])
        self.assertEqual(result["measured_file_count"], len(REQUIRED_FILES))
        self.assertFalse(result["target_met"])
        self.assertFalse(result["runtime_verified"])
        self.assertFalse(result["finished_game_verified"])
        self.assertIn("forged", result["integrity_limit"])

    def test_minimum_uses_actual_files_and_includes_exact_threshold(self):
        total = self.receipt["installedPlayerBytes"]
        self.assertTrue(audit_build(self.root, require_minimum=total)["passed"])
        self.assert_fails("required minimum", require_minimum=total + 1)
        self.assert_fails("required minimum is 5000000000", require_minimum=5_000_000_000)

    def test_receipt_and_digest_are_required(self):
        for name in (RECEIPT_NAME, RECEIPT_NAME + ".sha256"):
            with self.subTest(name=name):
                self.write_receipt()
                (self.root / name).unlink()
                result = audit_build(self.root)
                self.assertFalse(result["passed"])

    def test_one_sided_manual_receipt_edit_fails_integrity(self):
        self.receipt["installedPlayerBytes"] = 5_000_000_000
        (self.root / RECEIPT_NAME).write_text(json.dumps(self.receipt), encoding="utf-8")
        self.assert_fails("SHA-256 mismatch")

    def test_rehashed_claimed_size_cannot_override_measured_files(self):
        self.receipt.update(installedPlayerBytes=5_000_000_000, installedDecimalGB=5,
                            installedGiB=5_000_000_000 / 1_073_741_824, targetMet=True)
        self.write_receipt()
        result = self.assert_fails("installed total differs", require_minimum=5_000_000_000)
        self.assertLess(result["installed_player_bytes"], 5_000_000_000)
        self.assertFalse(result["target_met"])

    def test_same_size_player_change_is_detected(self):
        path = self.root / "AlcatrazEscape.exe"
        data = bytearray(path.read_bytes())
        data[-1] ^= 1
        path.write_bytes(data)
        self.assert_fails("Modified installed file: AlcatrazEscape.exe")

    def test_missing_dll_is_detected(self):
        (self.root / "UnityPlayer.dll").unlink()
        self.assert_fails("Missing installed file: UnityPlayer.dll")

    def test_required_runtime_missing_even_after_manifest_is_rewritten(self):
        (self.root / "MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll").unlink()
        self.refresh_inventory()
        self.assert_fails("Required player file missing or empty: MonoBleedingEdge")

    def test_missing_scene_data_is_not_a_complete_export(self):
        (self.root / "AlcatrazEscape_Data/level2").unlink()
        self.refresh_inventory()
        self.assert_fails("Required player file missing or empty: AlcatrazEscape_Data/level2")

    def test_unlisted_old_file_in_build_folder_is_rejected(self):
        (self.root / "old-scene.assets").write_bytes(b"left from a previous build")
        self.assert_fails("Unexpected/stale installed file: old-scene.assets")

    def test_stale_file_captured_by_manifest_still_requires_unity_report(self):
        (self.root / "padding.bin").write_bytes(b"not part of Unity output")
        self.refresh_inventory()
        row = next(row for row in self.receipt["installedFiles"] if row["path"] == "padding.bin")
        row["reportedByUnity"] = False
        row["unityReportedBytes"] = 0
        self.receipt["unreportedFiles"] = ["padding.bin"]
        self.write_receipt()
        self.assert_fails("Unreported/stale file")

    def test_generic_postbuild_receipt_cannot_qualify(self):
        self.receipt["contextCaptured"] = False
        self.write_receipt()
        self.assert_fails("generic postbuild reports cannot qualify")

    def test_missing_scene_or_wrong_default_cannot_qualify(self):
        for scenes in (list(EXPECTED_SCENES[:2]), list(reversed(EXPECTED_SCENES))):
            with self.subTest(scenes=scenes):
                self.receipt["scenes"] = scenes
                self.write_receipt()
                self.assert_fails("all three Alcatraz scenes")

    def test_source_revision_and_dirty_policies_are_explicit(self):
        self.assert_fails("requested revision", expected_commit="b" * 40)
        self.receipt["source"]["dirty"] = True
        self.write_receipt()
        self.assertTrue(audit_build(self.root)["passed"])
        self.assert_fails("dirty source checkout", require_clean_source=True)

    def test_unavailable_source_provenance_is_not_silently_clean(self):
        self.receipt["source"] = {"available": False, "error": "git unavailable", "dirty": False}
        self.write_receipt()
        self.assert_fails("provenance are unavailable")

    def test_small_development_build_is_measurable_without_release_size(self):
        self.receipt.update(buildOptionsValue=1, buildOptions="Development", developmentBuild=True)
        self.write_receipt()
        self.assertTrue(audit_build(self.root)["passed"])
        self.assert_fails("required minimum", require_minimum=5_000_000_000)

    def test_invalid_binary_cannot_pass_by_updating_its_hash(self):
        (self.root / "AlcatrazEscape.exe").write_bytes(b"not a Windows player")
        self.refresh_inventory()
        self.assert_fails("Native x64 Windows binary header is invalid")

    def test_manifest_cannot_escape_or_use_ambiguous_windows_paths(self):
        original = deepcopy(self.receipt)
        for path in ("../outside-secret", "/absolute", "C:/outside", "folder\\file", "a//b", "a/./b", "a. /file", "CON.txt", "a*/b"):
            with self.subTest(path=path):
                self.receipt = deepcopy(original)
                self.receipt["installedFiles"][0]["path"] = path
                self.write_receipt()
                result = audit_build(self.root)
                self.assertFalse(result["passed"])

    def test_duplicate_manifest_names_fail_windows_collision_check(self):
        row = deepcopy(self.receipt["installedFiles"][0])
        row["path"] = row["path"].upper()
        self.receipt["installedFiles"].append(row)
        self.write_receipt()
        self.assert_fails("repeats a Windows filename")

    def test_external_symlink_is_rejected_without_reading_target(self):
        outside = Path(self.temporary.name) / "outside"
        outside.write_bytes(b"must not be part of export")
        try:
            (self.root / "linked-file").symlink_to(outside)
        except OSError as error:
            self.skipTest(str(error))
        self.assert_fails("must not be symbolic links")

    def test_invalid_json_values_are_controlled_failures(self):
        for data in (b'{"schemaVersion":2,"schemaVersion":2}', b'{"bad":NaN}', b'[]', b'not json'):
            with self.subTest(data=data):
                self.write_raw_receipt(data)
                self.assertFalse(audit_build(self.root)["passed"])

    def test_wrong_receipt_sidecar_name_is_rejected(self):
        sidecar = self.root / (RECEIPT_NAME + ".sha256")
        sidecar.write_text(sidecar.read_text().replace(RECEIPT_NAME, "another-build.json"))
        self.assert_fails("invalid sidecar")

    def test_nonregular_receipt_is_rejected_before_read(self):
        path = self.root / RECEIPT_NAME
        path.unlink()
        path.mkdir()
        self.assert_fails("must be regular files")

    def test_cli_reports_actual_bytes_and_minimum_failure_with_spaced_path(self):
        tool = Path(__file__).resolve().parents[1] / "verify_player_build.py"
        result = subprocess.run([sys.executable, str(tool), str(self.root), "--require-minimum", "5000000000"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["installed_player_bytes"], self.receipt["installedPlayerBytes"])
        self.assertFalse(report["target_met"])
        successful = subprocess.run([sys.executable, str(tool), str(self.root), "--require-minimum",
                                     str(self.receipt["installedPlayerBytes"])], capture_output=True, text=True, check=False)
        self.assertEqual(successful.returncode, 0, successful.stdout + successful.stderr)


if __name__ == "__main__":
    unittest.main()
