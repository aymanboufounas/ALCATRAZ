# Hourly checks and high-end graphics

## Scheduled checks

[Unity source checks](../.github/workflows/source-checks.yml) is configured for minute **17 of every hour, UTC**, plus pushes, pull requests and manual runs. GitHub schedules run from the default branch and can be delayed. Committing this configuration does not prove a scheduled run has executed; check the repository's Actions tab for actual runs.

The job runs 28 independent checks: 11 executable C# rule suites, 15 source/asset validators, the runner regression suite and the player-build audit regression suite. A failed check does not hide later failures. JSON results, a Markdown summary and individual logs are uploaded as an Actions artifact with 14-day retention. An incomplete run remains explicitly incomplete. The runner rejects invalid timeouts and removes old test executables before compiling.

This is a checking/reporting workflow. It does not run Unity, inspect rendered gameplay or operate a continuing AI coding agent. New problems need a coding session to investigate and fix them. The chat cannot keep making hourly code changes after the session ends.

Run the same checks locally with Python 3.12, the packages in `Tools/requirements.txt`, and Mono:

```bash
python Tools/run_source_checks.py --report-dir /tmp/alcatraz-checks
```

Use `--root` for an existing scratch copy if historical generated reports should stay out of your working tree. `--python`, `--mcs` and `--mono` accept executable paths for environments using tool wrappers.

## High-end 1440p / 4K settings

Exploration and Chapter 01 now use one scene-owned graphics service and the same saved preset indices. The default for a fresh configuration is Ultra; existing saved choices are respected. The service changes a runtime URP clone, and scene teardown restores the original default/quality pipeline selections and related runtime settings.

| Profile | Render scale | Texture mip reduction | Main-light shadows | Camera AA |
| --- | --- | --- | --- | --- |
| Low | 80% | 2 levels | 30 m, 1 cascade, 1024 atlas | FXAA |
| Medium | Native | 1 level | 60 m, 2 cascades, 2048 atlas | SMAA Medium |
| High | Native | None | 120 m, 4 cascades, 4096 atlas | SMAA High |
| Ultra | Native | None | 180 m, 4 cascades, 4096 atlas | SMAA High |

High/Ultra preserve original texture detail. Ultra also forces anisotropic filtering and a higher LOD bias. MSAA is disabled while post-process AA is active. The streaming budgets affect only textures imported with streaming enabled; they are not a measured total VRAM budget.

**Esc → Settings** offers 2560×1440 and 3840×2160, alongside 720p/1080p. Select the resolution and apply display settings. Opening the page refreshes its staged values from the current display, preventing an old pause-menu value from undoing a title-screen resolution change. Display size is not changed automatically at startup.

The rendering changes bind URP's official post-processing data, enable baseline local-light shadow capability and HDR grading, validate a saved active SSAO feature during editor preparation, and remove runtime mutation of shared renderer features. Water samples the actual environment reflection; the marine sky schedules one environment refresh. Camera position, player culling layers and movement drivers are preserved.

Official Unity 6000 source references used for the resource bindings and water API:

- [URP post-processing resource metadata](https://github.com/Unity-Technologies/Graphics/blob/6000.0/staging/Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset.meta)
- [URP ambient-occlusion script metadata](https://github.com/Unity-Technologies/Graphics/blob/6000.0/staging/Packages/com.unity.render-pipelines.universal/Runtime/RendererFeatures/ScreenSpaceAmbientOcclusion.cs.meta)
- [URP environment reflection implementation](https://github.com/Unity-Technologies/Graphics/blob/6000.0/staging/Packages/com.unity.render-pipelines.universal/ShaderLibrary/GlobalIllumination.hlsl)

## Confirmed fixes in this pass

- Sustained walking or jogging clears old sprint history, so a normal walking stop no longer selects the sprint-stop animation from an earlier sprint. Immediate sprint release and short speed dips retain the running stop.
- The pause settings page refreshes resolution/fullscreen staging when reopened, avoiding accidental display reversion.
- Story/exploration quality choices are shared, and the graphics service restores distinct pipeline overrides and runtime settings on teardown.
- Rendering validation also runs when character imports are already cached; post-processing repair no longer depends on forcing an unrelated animation reimport.

## Build size and verification limits

No 10 GB player build was produced in this cloud environment. Existing source assets remain their original resolution; these code/settings changes do not add enough content to make a 10 GB game. File size does not establish visual quality. A successful Unity player build now writes its actual `BuildReport.totalSize` to **`Builds/Reports/LatestPlayerBuild.json`**; source checkout size and runtime VRAM are separate measurements.

The current requested minimum is **5 GB for the installed player**. The later [player-build verification workflow](PlayerBuildVerification.md) also records exact exported files, their hashes and Unity membership, scene/source provenance and packed contributors. It can qualify an actual export against 5,000,000,000 bytes; no such player has been built here.

Cloud results are recorded in [HourlyChecksAndGraphics.json](../Validation/HourlyChecksAndGraphics.json). Offline rule tests, syntax, source resource bindings and texture dimensions are distinct from Unity API/shader compilation and live rendering.

After pulling `main`, stop Play Mode and let Unity finish preparation. **Alcatraz → Run All Gameplay Checks (Play Mode)** includes the new graphics lifecycle fixture; **Alcatraz → Validate Shared Graphics Lifecycle (Play Mode)** runs it separately. Test High and Ultra in all three enabled scenes at 1440p and 4K, including title-to-pause display changes, scene travel, shadows, water and visible player animations. Capture GPU/CPU frame times and VRAM use on the target PC before judging performance or visual quality. Those Unity tests, shader compilation, a player build and a complete playthrough remain unexecuted here.
