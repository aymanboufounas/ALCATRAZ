# Finished-player size and verification

The requested minimum is **5,000,000,000 installed bytes**: 5.00 decimal GB, approximately 4.657 GiB. It applies to a real Windows player export. Source checkout size, Git history, downloaded archives, generated pictures and runtime VRAM do not measure that target. Existing compression remains in use; duplicated or padded files do not qualify as game content.

No Unity player has been built in this cloud instance. Unity 6000.0.62f1, usable activation and Windows Build Support are unavailable here. The current source checks and synthetic audit fixtures cannot establish an installed size, launch, gameplay completion, visual quality or performance.

## Produce and measure a real build

On a machine with the licensed **Unity 6000.0.62f1** editor and **Windows Build Support (Mono)**, pull the intended commit and let import/preparation finish. Use a clean source checkout and export to an empty `Builds/Windows` directory. Preserve any wanted older build elsewhere before exporting; the audit reports stale files rather than deleting them automatically.

Build with **Alcatraz → Build Windows x64**, or from PowerShell:

```powershell
.\Tools\BuildAlcatrazWindows.ps1
```

The Alcatraz wrapper records the exact three-scene invocation, options, source commit/dirty state, Unity build GUID/result and the real exported file inventory after the build and postprocessors finish. An unrelated generic Unity build is explicitly nonqualifying. A failed wrapped build invalidates the prior receipt.

Successful measurement writes:

- `Builds/Reports/LatestPlayerBuild.json`, plus its SHA-256 sidecar.
- `Builds/Windows/AlcatrazPlayerBuildReceipt.json`, plus its SHA-256 sidecar, beside the executable.

The receipt includes each exported file's relative path, SHA-256, actual byte count and Unity output membership; installed GB/GiB; the 5 GB target/result; scene/build/source provenance; and available packed-asset contributors. Packed-object contributions are diagnostic and are not added to the installed total. The build log lives under ignored `Builds/Reports`, outside the installed-player directory, so it cannot inflate the game size or dirty the recorded source by itself.

With **Python 3.12 or newer** installed, audit the actual exported files (the Windows junction checks require this version):

```powershell
python .\Tools\verify_player_build.py .\Builds\Windows
python .\Tools\verify_player_build.py .\Builds\Windows --require-minimum 5000000000 --require-clean-source
```

For a specific source revision, also pass `--require-source-commit` with its full Git object ID. The verifier rejects missing, changed, unexpected/stale or unreported files, invalid receipts, incomplete Windows/Mono/scene output, and an unmet requested minimum. It fails an absent player. Ordinary small development exports remain measurable when the minimum flag is omitted; development exports do not qualify as the complete release player.

The PowerShell build helper can run minimum-size qualification after building:

```powershell
.\Tools\BuildAlcatrazWindows.ps1 -RequireMinimumSize
```

Use `-UnityEditor` for a nondefault editor path and `-PythonExecutable` for a nondefault Python 3.12+ command. The PowerShell helper and Unity callback require execution on the build machine; they have not run in this cloud instance.

## What the evidence proves

The receipt's digest detects accidental edits; it is not a trusted signature or proof that Unity produced the files. The audit checks export structure, recorded provenance and the current filesystem. Its regression fixtures are tiny synthetic data, not a playable game. Both `runtimeVerified` and `finishedGameVerified` remain false.

After an export passes integrity and the requested size threshold, launch the executable and test the title/pause/settings flow, visible third-person player, walking/running/jumping/crouching, gun/knife/punch damage, swimming/restricted-water restart, zero-health restart, checkpoint reload, NPC support and the full mission/activity routes. Review the rebuilt tower/roof in Unity and capture target-PC CPU/GPU times at 1440p/4K. Those results are separate from size qualification. Measure the distribution archive separately after accepted content is packaged.

The next content work must add useful playable areas, missions, animations, sound and authored environments. A 5 GB export by itself does not establish those qualities, and the current source update does not claim that the minimum finished-player size has been reached.
