# Movement and animation quality

This pass improves weighted starts, braking, direction changes, ground contact and animation timing using the project's existing controller and licensed Rocketbox characters. Rockstar is the requested style reference. No Rockstar animations or implementation were copied, and this work does not establish equivalent visual quality.

## Research and implementation choices

The fetched [Unity 6 BlendTree inspector source](https://github.com/Unity-Technologies/UnityCsReference/blob/6000.0/Editor/Mono/Inspector/BlendTreeInspector.cs) matches blends and playback to measured motion speeds. These FBX clips have their root translation anchored during import, so the project keeps its original source measurements in `GaitSpeeds.json` instead of asking Unity to calculate speeds from the resulting in-place clips.

[Unity's Animator API](https://github.com/Unity-Technologies/UnityCsReference/blob/6000.0/Modules/Animation/ScriptBindings/Animator.bindings.cs) provides explicit animation damping, while the [transition API](https://github.com/Unity-Technologies/UnityCsReference/blob/6000.0/Editor/Mono/StateMachine.bindings.cs) supports fixed-duration blends and interruption conditions. The controller remains responsible for collision and travel; the animations follow measured movement. Full fetched-source references, excerpts and evidence limits are in [MovementResearch.json](MovementResearch.json). The Unity Manual and GDC websites were blocked by the environment's HTTPS proxy; their contents and Rockstar's internal animation pipeline were not verified.

## Changes

- Reversing direction brakes the old momentum before accelerating in the new direction. Releasing sprint also uses braking. Residual time is carried through the reversal so higher refresh rates do not add a pause at zero speed.
- Blocking wall contacts remove stored inward momentum while preserving sideways motion. Protected ledges remove suppressed momentum. Successful stair ascents retain forward progress.
- Short, walkable stair descents retain support within the controller's step allowance. Prepared jumps, rising jumps and larger drops keep their airborne behavior. Corrective vertical snaps do not inflate gait speed or erase horizontal movement.
- Walkable-slope projection preserves requested surface speed. Animation reads measured surface travel rather than only its horizontal projection.
- Starts, braking stops and stationary turns use persistent state and elapsed time. Invalid queued events are cleared after wall hits, changed intent, reverse movement, activities and teleports.
- Genuine non-looping **RunStart** and **RunStop** source clips distinguish running transitions from walking. They come from the same pinned MIT Rocketbox repository as the original characters. [Source URLs, license and checksums](LocomotionClipProvenance.json) are retained. `python Tools/import_locomotion_clips.py` verifies or restores them without replacing modified source files.
- The slow-walk clip receives a half-cycle offset before blending. Actual source foot-lift correlation improves from negative correlation to 0.67–0.82 across adjacent gaits. Starts crossfade into the measured matching gait phase rather than cutting to phase zero.
- Backward diagonal aiming uses the correct gait direction. Lower-body travel orientation and upper-body aiming are separated procedurally. Dedicated lateral/backward mocap clips are still absent.
- Foot grounding and sound use measured ankle-to-sole clearance instead of a fixed 5.5 cm assumption. Contact audio reads the final posed feet; idle, swimming, seating, ragdolls and travel reset contact history. Landings produce one impact-scaled surface sound. NPCs and crouching remain quieter.
- Unity regenerates the animation controller for this revision. Preparation checks actual parameter types, bound clips, gait thresholds, child phases, transitions and interruption conditions.

## Verification

The executable source suites cover braking/reversal at 30/60/120/240 Hz, animation start/stop/turn behavior across ten frame rates, diagonal gait orientation, queued-event invalidation, foot-contact cadence, landing deduplication and volume bounds. Existing combat, health, swimming, camera, vehicle, checkpoint and poker rule tests remain in the CI workflow.

`python Tools/validate_locomotion_quality.py` checks source hashes and license retention, weighted bone paths for all five characters, 90 weighted transition poses and measured gait phase alignment. Native scene, route, import-reference and C# grammar checks remain separate. These checks do not compile against Unity APIs or prove rendered quality. Results and unexecuted checks are recorded in [MovementQuality.json](../Validation/MovementQuality.json).

## Verify in Unity

Pull `main`, stop Play Mode and let Unity finish importing. Character preparation rebuilds the controller automatically; **Alcatraz → Prepare Characters** repairs it explicitly. Enter gameplay before running **Alcatraz → Run All Gameplay Checks (Play Mode)**. The combined runner includes **Alcatraz → Validate Movement Response and Stairs (Play Mode)**, with 26 real-controller assertions for walls, ascending/descending steps, jumps, ramps and ownership resets. Those Unity fixtures have not run in this cloud environment.

Visually check each enabled scene: supplied island, original island and Chapter 01. Repeat at 30, 60 and 120 FPS where hardware permits.

| Task | Expected result in Play Mode |
| --- | --- |
| Walk, jog, sprint and release | Distinct starts and braking, smooth gait blending, no stuck transition after a quick restart. |
| Reverse and run into a wall | Brake before reversing; move away from the wall promptly; keep parallel wall and ledge movement. |
| Ascend/descend stairs and use ramps | Retain support on small steps, preserve uphill progress, avoid false jumping or sped-up gait on a downward snap. |
| Jump, land and crouch | Deliberate jump remains airborne; one landing sound; calibrated foot contact; crouch respects low ceilings. |
| Aim diagonally and move sideways | Feet follow the chosen travel/playback direction; torso and weapon retain aim. Check visual twisting and hand grips. |
| Seat, swim, drive and teleport | Owning activity keeps control; no stale footstep or start/stop event afterward; third-person body recovery remains available with V/R3. |

Jumping, swimming, crouch-walking and strafing still combine existing clips with procedural posing. A richer mocap library, visual animation tuning, performance measurements and a player build remain future work. Unity is not installed here, so no complete playthrough, rendered animation-quality comparison or Steam-quality claim is made.
