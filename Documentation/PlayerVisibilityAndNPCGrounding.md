# Player visibility and NPC floor checks

This revision strengthens character preparation and third-person camera ownership, corrects two NPC placements, and adds checks that run on the actual loaded Unity scene. Offline checks do not reproduce the reported eyes-only view or establish that the live game is fully working.

## What changed

- Character preparation runs before Play for the selected start scene and for the current Foundation scene. It validates imported meshes, skeletons, avatar data, importer settings, locomotion parameters and actual animation bindings. Explicit repair reimports the source models even when an older revision stamp exists.
- Missing animation data no longer prevents creating the prisoner body and third-person camera. The body remains available as a preview, and gameplay stays blocked with a specific setup error until preparation succeeds. `Ready` requires an active renderable prisoner, correct main camera and exclusive camera driver.
- Camera obstruction queries ignore the player's own hierarchy and handle full query buffers. Tight-space framing also searches higher angles when ordinary horizontal views cannot show the player safely.
- Returning to the exploration title recreates the scene. Hidden vehicle passengers, poker cameras, external movement ownership and ragdolls cannot leak into a new Continue session.
- Standing NPCs recheck nearby floor support. Both patrol drivers require a walkable floor and clear standing space before each step. Small buried/floating placements can recover within 1.1 m; actors are never moved to a gallery several metres away. Scripted, seated, sleeping, ragdoll and dead states retain their owning systems.
- Samir was moved clear of a yard bench; Theo was moved clear of a visitation seat. Native validation now checks all 30 authored actor stations, including stationary NPCs. The supplied police uses its mesh-foot offset, and the police dog refuses unsupported steps.
- The supplied scene's incorrectly serialized camera component is now a proper `AudioListener`. New startup validation checks native component types, scripts, player ancestry, camera bindings and render layers across every enabled scene.

## Checking in Unity

Stop Play Mode, pull `main`, and let Unity finish compiling/importing. **Alcatraz → Open Island** selects the supplied island; **Alcatraz → Open Chapter 01** selects the chapter. Character preparation now runs automatically before Play. **Alcatraz → Prepare Characters** explicitly repairs imports when needed.

About one editor second after entering Play, loading a scene, resuming control, or teleporting, the project checks the actual imported player/camera and every standing NPC's floor. Unity logs **Alcatraz loaded-scene checks PASS/FAIL** and saves details to:

`Library/AlcatrazVerification/LatestSceneChecks.json`

The report distinguishes standing actors, intentionally excluded poses, dog support, camera distance and errors. Vehicle, activity, death and cinematic framing are handled separately from ordinary third-person framing.

After entering normal gameplay, run **Alcatraz → Run All Gameplay Checks (Play Mode)**. This runs the movement/camera, NPC floor, combat, swimming, health/checkpoint and HUD fixtures, plus supplied-island travel where applicable. It records passed, failed and skipped suites. It refuses to report a test run while paused or during an activity/cinematic. These fixtures do not replace walking, running, jumping, crouching and fighting while visually observing the imported character.

## Verification scope

Cloud verification covers executable world-independent rules, native scene bindings, all authored NPC stations, sampled routes, source character anatomy and asset integrity. Unity 6000.0.62f1 and its assemblies are not installed in this cloud environment. Unity API compilation, the new Play Mode checks, actual camera behavior and a player build remain unexecuted here. The saved loaded-scene report is produced by Unity when the project is played, not by offline source validation.
