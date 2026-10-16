"""Run independent offline checks and preserve failures for local and CI review.

This runner does not start Unity, import its assets, or exercise a rendered game.
Validators may update their normal reports under Validation, so use a scratch
checkout when those generated reports should not change a working tree.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys
import time


@dataclass(frozen=True)
class Check:
    name: str
    commands: tuple[tuple[str, ...], ...]


MONO_SUITES = (
    ("HoldemTests", (
        "Assets/Game/Scripts/Activities/PrisonPokerRules.cs",
        "Assets/Game/Scripts/Activities/HoldemGame.cs",
        "Assets/Game/Foundation/Scripts/WeaponState.cs")),
    ("VehicleControlTests", ("Assets/Game/Foundation/Scripts/VehicleControlRules.cs",)),
    ("CombatTests", (
        "Assets/Game/Foundation/Scripts/WeaponState.cs",
        "Assets/Game/Foundation/Scripts/CombatHealth.cs")),
    ("MenuCheckpointTests", (
        "Assets/Game/Foundation/Scripts/WeaponState.cs",
        "Assets/Game/Scripts/Save/CheckpointStorage.cs")),
    ("CameraFramingTests", ("Assets/Game/Foundation/Scripts/CameraFramingRules.cs",)),
    ("PlayerFailureTests", (
        "Assets/Game/Foundation/Scripts/WeaponState.cs",
        "Assets/Game/Foundation/Scripts/CombatHealth.cs",
        "Assets/Game/Foundation/Scripts/PlayerFailureRules.cs")),
    ("SwimmingTests", ("Assets/Game/Foundation/Scripts/SwimmingRules.cs",)),
    ("MovementResponseTests", ("Assets/Game/Foundation/Scripts/MovementResponseRules.cs",)),
    ("LocomotionAnimationTests", ("Assets/Game/Foundation/Scripts/LocomotionAnimationRules.cs",)),
    ("FootContactTests", ("Assets/Game/Foundation/Scripts/FootContactRules.cs",)),
    ("GraphicsSettingsTests", ("Assets/Game/Foundation/Scripts/GraphicsRules.cs",)),
)

PYTHON_VALIDATORS = (
    ("csharp_grammar", "check_csharp_syntax.py"),
    ("character_forward", "validate_character_forward.py"),
    ("locomotion_quality", "validate_locomotion_quality.py"),
    ("alcatraz_routes", "validate_alcatraz.py"),
    ("scene_startup", "validate_scene_startup.py"),
    ("native_asset_integrity", "validate_project.py"),
    ("supplied_assets", "validate_supplied_assets.py"),
    ("supplied_prison", "validate_supplied_prison.py"),
    ("warehouse", "validate_warehouse.py"),
    ("extra_assets", "validate_extra_assets.py"),
    ("police_helicopter", "validate_police_helicopter.py"),
    ("graphics_quality", "validate_graphics_quality.py"),
    ("environment_surface_quality", "validate_environment_quality.py"),
    ("world_rebuild", "validate_world_rebuild.py"),
)


def build_checks(root: Path, report_dir: Path, python: str,
                 mcs: str, mono: str) -> list[Check]:
    binaries = report_dir / "bin"
    binaries.mkdir(parents=True, exist_ok=True)
    checks = [Check("source_check_runner", ((
        python, str(root / "Tools/Tests/test_source_check_runner.py")),))]
    for name, sources in MONO_SUITES:
        binary = binaries / (name + ".exe")
        # A successful compiler exit must never reuse an executable from a prior
        # invocation with the same report directory.
        binary.unlink(missing_ok=True)
        paths = tuple(str(root / source) for source in sources)
        test = str(root / "Tools/Tests" / (name + ".cs"))
        checks.append(Check(name, (
            (mcs, "-out:" + str(binary), *paths, test),
            (mono, str(binary)),
        )))
    for name, filename in PYTHON_VALIDATORS:
        checks.append(Check(name, ((python, str(root / "Tools" / filename)),)))
    return checks


def run_check(check: Check, root: Path, report_dir: Path,
              timeout: float) -> dict:
    """Stop dependent commands on failure; other checks still run."""
    started = time.monotonic()
    log_path = report_dir / (check.name + ".log")
    commands = []
    status = "passed"
    with log_path.open("w", encoding="utf-8") as log:
        for command in check.commands:
            log.write("Command: " + json.dumps(command) + "\n")
            log.flush()
            command_started = time.monotonic()
            result = {"argv": list(command)}
            try:
                process = subprocess.run(
                    command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                    timeout=timeout, check=False,
                )
                result["exit_code"] = process.returncode
                if process.returncode:
                    status = "failed"
            except subprocess.TimeoutExpired:
                status = "failed"
                result["error"] = "timeout"
                log.write(f"\nTimed out after {timeout:g} seconds.\n")
            except OSError as error:
                status = "failed"
                result["error"] = str(error)
                log.write("\nCould not execute command: " + str(error) + "\n")
            result["duration_seconds"] = round(time.monotonic() - command_started, 3)
            commands.append(result)
            if status == "failed":
                break
    return {
        "name": check.name,
        "status": status,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log": log_path.name,
        "commands": commands,
    }


def write_reports(report_dir: Path, root: Path, started_at: str,
                  results: list[dict], total_checks: int) -> dict:
    failed = sum(result["status"] == "failed" for result in results)
    complete = len(results) == total_checks
    report = {
        "scope": "Offline C# rule tests, C# grammar, scene bindings, and source asset validation",
        "unity_runtime_verified": False,
        "limitations": "Unity compilation, asset import, rendered gameplay, physics, and visual quality require Unity verification.",
        "root": str(root),
        "started_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed" if failed else ("passed" if complete else "running"),
        "total_checks": total_checks,
        "completed_checks": len(results),
        "passed_checks": len(results) - failed,
        "failed_checks": failed,
        "checks": results,
    }
    temporary = report_dir / "results.json.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(report_dir / "results.json")
    summary = [
        "## Offline source checks",
        "",
        f"Status: **{report['status'].upper()}** — {report['passed_checks']} passed, {failed} failed, {len(results)}/{total_checks} completed.",
        "",
        "Unity runtime is **not verified**. These checks do not compile Unity APIs, import assets in Unity, or assess rendered gameplay.",
        "",
        "| Check | Result | Seconds |",
        "| --- | --- | ---: |",
    ]
    summary.extend(
        f"| {result['name']} | {result['status'].upper()} | {result['duration_seconds']:.3f} |"
        for result in results
    )
    summary.extend(["", "Download the source-checks artifact for JSON results and individual logs.", ""])
    temporary = report_dir / "summary.md.tmp"
    temporary.write_text("\n".join(summary), encoding="utf-8")
    temporary.replace(report_dir / "summary.md")
    return report


def run_checks(checks: list[Check], root: Path, report_dir: Path,
               timeout: float = 300) -> dict:
    report_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    results = []
    report = write_reports(report_dir, root, started_at, results, len(checks))
    for check in checks:
        print("Running " + check.name, flush=True)
        result = run_check(check, root, report_dir, timeout)
        results.append(result)
        print(result["status"].upper() + " " + check.name, flush=True)
        report = write_reports(report_dir, root, started_at, results, len(checks))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--mcs", default="mcs")
    parser.add_argument("--mono", default="mono")
    parser.add_argument("--check-timeout", type=float, default=300)
    args = parser.parse_args(argv)
    if not math.isfinite(args.check_timeout) or args.check_timeout <= 0:
        parser.error("--check-timeout must be finite and positive")
    root = args.root.resolve()
    report_dir = args.report_dir.resolve()
    checks = build_checks(root, report_dir, args.python, args.mcs, args.mono)
    report = run_checks(checks, root, report_dir, args.check_timeout)
    print(f"Results: {report_dir / 'results.json'}", flush=True)
    return 1 if report["failed_checks"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
