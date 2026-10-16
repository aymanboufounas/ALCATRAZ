"""Verify a Unity-exported Alcatraz Windows folder without launching its player.

The Unity build wrapper writes a colocated receipt and SHA-256 sidecar. They
detect changed/missing/stale files and one-sided receipt edits, not deliberate
forgery of both receipt and digest. Nothing here certifies gameplay completion,
licensing, visual quality or successful execution on a Windows PC.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys

RECEIPT_NAME = "AlcatrazPlayerBuildReceipt.json"
TARGET_INSTALLED_BYTES = 5_000_000_000
EXPECTED_SCENES = (
    "Assets/Game/Scenes/SC_AlcatrazSuppliedIsland.unity",
    "Assets/Game/Scenes/SC_AlcatrazChapter01.unity",
    "Assets/Game/Scenes/SC_AlcatrazIsland.unity",
)
AUDIT_FILES = {RECEIPT_NAME, RECEIPT_NAME + ".sha256"}
HASH = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
REQUIRED_FILES = (
    "AlcatrazEscape.exe", "UnityPlayer.dll",
    "AlcatrazEscape_Data/globalgamemanagers", "AlcatrazEscape_Data/boot.config",
    "AlcatrazEscape_Data/Managed/Assembly-CSharp.dll",
    "AlcatrazEscape_Data/level0", "AlcatrazEscape_Data/level1", "AlcatrazEscape_Data/level2",
    "MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll",
)


class AuditError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AuditError("Receipt contains a duplicate JSON key.")
        result[key] = value
    return result


def integer(value):
    return type(value) is int and value >= 0


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise AuditError("Manifest paths must be normalized relative Windows-safe paths.")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in (".", "..") for part in path.parts) or path.as_posix() != value:
        raise AuditError("Manifest path escapes or is not normalized within the export.")
    reserved = {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))}
    if any(part.endswith((" ", ".")) or any(ord(c) < 32 or c in '<>"|?*' for c in part)
           or part.split(".")[0].upper() in reserved for part in path.parts):
        raise AuditError("Manifest contains an unsafe Windows filename.")
    return value


def hash_regular_file(path):
    before = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise AuditError("Export entries must be regular files; symbolic links are not accepted.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise AuditError("Export changed while being verified; audit a closed, stable build folder.")
    return before.st_size, digest.hexdigest()


def inventory(root):
    result = {}
    windows_paths = set()
    for directory, subdirectories, files in os.walk(root, followlinks=False):
        for name in subdirectories:
            path = Path(directory) / name
            if path.is_symlink() or path.is_junction():
                raise AuditError("Export directories must not be symbolic links or junctions.")
        for name in files:
            path = Path(directory) / name
            relative = safe_relative(path.relative_to(root).as_posix())
            folded = relative.casefold()
            if folded in windows_paths:
                raise AuditError("Export has colliding Windows filenames.")
            windows_paths.add(folded)
            if path.is_symlink():
                raise AuditError("Export files must not be symbolic links.")
            if relative not in AUDIT_FILES:
                result[relative] = hash_regular_file(path)
    return result


def check_windows_binary(path):
    # Basic native PE32+ x64 sanity, not an executable/engine authenticity check.
    with path.open("rb") as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            return False
        stream.seek(struct.unpack_from("<I", dos, 60)[0])
        header = stream.read(26)
    return (len(header) == 26 and header[:4] == b"PE\0\0"
            and struct.unpack_from("<H", header, 4)[0] == 0x8664
            and struct.unpack_from("<H", header, 20)[0] >= 2
            and struct.unpack_from("<H", header, 24)[0] == 0x20B)


def read_receipt(root):
    receipt = root / RECEIPT_NAME
    sidecar = root / (RECEIPT_NAME + ".sha256")
    if (receipt.is_symlink() or sidecar.is_symlink()
            or not stat.S_ISREG(receipt.stat().st_mode) or not stat.S_ISREG(sidecar.stat().st_mode)):
        raise AuditError("Receipt and digest must be regular files inside the export.")
    if receipt.stat().st_size > 32 * 1024 * 1024:
        raise AuditError("Receipt exceeds the supported manifest size.")
    raw = receipt.read_bytes()
    if sidecar.stat().st_size > 1024:
        raise AuditError("Receipt digest sidecar exceeds its expected size.")
    fields = sidecar.read_text(encoding="utf-8").strip().split()
    if (len(fields) != 2 or fields[1] != RECEIPT_NAME or not HASH.fullmatch(fields[0])
            or hashlib.sha256(raw).hexdigest() != fields[0]):
        raise AuditError("Receipt SHA-256 mismatch or invalid sidecar; receipt may be edited or stale.")
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(AuditError("Nonfinite JSON number.")))
    if not isinstance(data, dict):
        raise AuditError("Receipt must be a JSON object.")
    return data


def audit_build(build_root, require_minimum=None, expected_commit=None, require_clean_source=False):
    """Read and hash an export. A pass never asserts the game was launched."""
    result = {
        "passed": False, "build_root": str(build_root), "issues": [],
        "installed_player_bytes": None, "installed_decimal_gb": None, "installed_gib": None,
        "target_installed_bytes": TARGET_INSTALLED_BYTES, "target_met": False,
        "required_minimum_bytes": require_minimum,
        "runtime_verified": False, "finished_game_verified": False,
        "scope": "Receipt integrity, exact current file inventory, x64 export structure and optional installed-size threshold only.",
        "integrity_limit": "An unsigned receipt and digest can both be forged; they are not independent Unity authenticity evidence.",
    }
    issues = result["issues"]
    try:
        if require_minimum is not None and (type(require_minimum) is not int or require_minimum <= 0):
            raise AuditError("Required minimum must be a positive integer byte count.")
        root = Path(build_root)
        if root.is_symlink() or not root.is_dir():
            raise AuditError("Build root must be a real existing export directory.")
        root = root.resolve()
        receipt = read_receipt(root)
        if receipt.get("schemaVersion") != 2 or receipt.get("receiptKind") != "AlcatrazWindowsPlayer":
            raise AuditError("Unsupported or generic receipt; rebuild with the Alcatraz build wrapper.")
        if receipt.get("contextCaptured") is not True:
            issues.append("Actual Alcatraz build invocation was not captured; generic postbuild reports cannot qualify.")
        if receipt.get("result") != "Succeeded" or receipt.get("target") != "StandaloneWindows64":
            issues.append("Receipt does not describe a successful Windows x64 player build.")
        if receipt.get("executable") != "AlcatrazEscape.exe":
            issues.append("Receipt executable is not the Alcatraz player.")
        scenes = receipt.get("scenes")
        if (not isinstance(scenes, list) or len(scenes) != 3 or not all(isinstance(s, str) for s in scenes)
                or set(scenes) != set(EXPECTED_SCENES) or scenes[0] != EXPECTED_SCENES[0]):
            issues.append("Receipt must capture all three Alcatraz scenes with the supplied island first.")
        if not isinstance(receipt.get("buildGuid"), str) or not re.fullmatch(r"[0-9a-fA-F]{32}", receipt["buildGuid"]):
            issues.append("Unity build GUID is missing or invalid.")
        if not isinstance(receipt.get("unityVersion"), str) or not receipt["unityVersion"].startswith("6000.0.62f1"):
            issues.append("Receipt does not record the project's Unity 6000.0.62f1 editor.")
        try:
            stamp = datetime.fromisoformat(receipt["builtUtc"].replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError("Timestamp has no timezone")
        except (KeyError, ValueError, TypeError, AttributeError):
            issues.append("Receipt build timestamp must include its UTC offset.")
        source = receipt.get("source")
        if (not isinstance(source, dict) or source.get("available") is not True
                or not isinstance(source.get("commit"), str) or not COMMIT.fullmatch(source["commit"])
                or type(source.get("dirty")) is not bool):
            issues.append("Source commit and dirty-state provenance are unavailable or invalid.")
        else:
            result["source_commit"] = source["commit"]
            result["source_dirty"] = source["dirty"]
            if expected_commit is not None and source["commit"] != expected_commit.lower():
                issues.append("Receipt source commit differs from the requested revision.")
            if require_clean_source and source["dirty"]:
                issues.append("Build was created from a dirty source checkout.")
        if not integer(receipt.get("buildOptionsValue")) or not isinstance(receipt.get("buildOptions"), str):
            issues.append("Actual build options are unavailable or invalid.")
        elif type(receipt.get("developmentBuild")) is not bool or receipt["developmentBuild"] != bool(receipt["buildOptionsValue"] & 1):
            issues.append("Development flag contradicts recorded build options.")
        actual = inventory(root)
        total = sum(size for size, digest in actual.values())
        result.update(installed_player_bytes=total, installed_decimal_gb=total / 1_000_000_000,
                      installed_gib=total / 1_073_741_824, target_met=total >= TARGET_INSTALLED_BYTES,
                      measured_file_count=len(actual))
        rows = receipt.get("installedFiles")
        if not isinstance(rows, list) or not rows:
            raise AuditError("Receipt contains no installed file manifest.")
        expected = {}
        windows_paths = set()
        for row in rows:
            if not isinstance(row, dict):
                raise AuditError("Installed file entry is not an object.")
            name = safe_relative(row.get("path"))
            if name in AUDIT_FILES or name.casefold() in windows_paths:
                raise AuditError("Receipt inventories itself or repeats a Windows filename.")
            windows_paths.add(name.casefold())
            if not integer(row.get("bytes")) or not isinstance(row.get("sha256"), str) or not HASH.fullmatch(row["sha256"]):
                raise AuditError("Installed file byte count or SHA-256 is invalid.")
            expected[name] = row
            if row.get("reportedByUnity") is not True:
                issues.append("Unreported/stale file is not part of this Unity build: " + name)
            if not integer(row.get("unityReportedBytes")) or row["unityReportedBytes"] != row["bytes"]:
                issues.append("Unity output byte count differs from the measured file: " + name)
        for name in sorted(set(expected) - set(actual)):
            issues.append("Missing installed file: " + name)
        for name in sorted(set(actual) - set(expected)):
            issues.append("Unexpected/stale installed file: " + name)
        for name in sorted(set(actual) & set(expected)):
            if actual[name] != (expected[name]["bytes"], expected[name]["sha256"]):
                issues.append("Modified installed file: " + name)
        for name in REQUIRED_FILES:
            if name not in actual or actual[name][0] == 0:
                issues.append("Required player file missing or empty: " + name)
        for name in ("AlcatrazEscape.exe", "UnityPlayer.dll"):
            if name in actual and not check_windows_binary(root / name):
                issues.append("Native x64 Windows binary header is invalid: " + name)
        if receipt.get("unreportedFiles") != []:
            issues.append("Build receipt reports files outside the current Unity output inventory.")
        if not integer(receipt.get("installedPlayerBytes")) or receipt["installedPlayerBytes"] != total:
            issues.append("Receipt installed total differs from actual file bytes.")
        if not integer(receipt.get("reportedPlayerBytes")) or receipt["reportedPlayerBytes"] <= 0:
            issues.append("Unity BuildReport summary size is missing or invalid.")
        if receipt.get("targetInstalledBytes") != TARGET_INSTALLED_BYTES or receipt.get("targetMet") is not result["target_met"]:
            issues.append("Receipt's 5,000,000,000-byte target or result contradicts actual bytes.")
        for key, number in (("installedDecimalGB", total / 1_000_000_000), ("installedGiB", total / 1_073_741_824)):
            value = receipt.get(key)
            if type(value) not in (float, int) or not math.isfinite(value) or not math.isclose(value, number, rel_tol=1e-6, abs_tol=1e-9):
                issues.append("Receipt size unit conversion is invalid: " + key)
        if require_minimum is not None and total < require_minimum:
            issues.append(f"Installed player has {total} bytes; required minimum is {require_minimum} bytes.")
        result["passed"] = not issues
    except (AuditError, OSError, ValueError, TypeError, OverflowError) as error:
        issues.append(str(error))
    return result


def positive_bytes(value):
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Minimum must be a positive integer byte count.") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("Minimum must be a positive integer byte count.")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_root", type=Path, help="Folder containing AlcatrazEscape.exe and the colocated Unity receipt.")
    parser.add_argument("--require-minimum", type=positive_bytes, help="Fail below this installed byte count; use 5000000000 for the requested 5 GB.")
    parser.add_argument("--require-source-commit", help="Require a specific full Git object ID recorded at build time.")
    parser.add_argument("--require-clean-source", action="store_true", help="Fail if the receipt records a dirty source checkout.")
    args = parser.parse_args(argv)
    if args.require_source_commit is not None and not COMMIT.fullmatch(args.require_source_commit.lower()):
        parser.error("--require-source-commit must be a full hexadecimal Git object ID.")
    result = audit_build(args.build_root, args.require_minimum, args.require_source_commit, args.require_clean_source)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
