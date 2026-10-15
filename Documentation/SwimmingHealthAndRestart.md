# Swimming, health and mission restart

The enabled Alcatraz scenes now support surface swimming and a restricted coastal water zone. This patch also connects the player to combat health, checkpoint health and mission restarts, fixes menu navigation/loading, corrects gun/knife queries that excluded real NPC hitboxes, lets seated NPCs receive punches, and restores both fighters' patrol state when a training spar ends.

## Playing

- Walk into deep water to swim. WASD / left stick paddles relative to the camera; Shift / L3 swims faster. The controller still collides with shores, piers, boats and other solid objects. The following camera stays above the ocean surface, and swimming hides weapons and prevents attacking or aiming.
- Space / A with movement toward a nearby low bank can step ashore if the entire standing body and approach are clear. Reach is at most 1.1 m and bank height at most 0.6 m above water. This is a short procedural step, not a supplied climbing animation. Tall cliffs and dock walls cannot be climbed.
- E / X boards a nearby boat. Once stopped, leaving a boat prefers a clear dry landing, then a clear water position where swimming can begin. Aircraft still require a dry landing.
- The HUD warns when swimming or boating away from the shore. Crossing into restricted water shows **WANTED** for three active seconds, then reloads the current scene and resumes the latest usable checkpoint. It does not spawn a police pursuit.
- Health displays as a percentage starting at **100%**. Rival strikes, normal combat damage and hard landings reduce it. At **0%**, **DEAD** appears for three active seconds and the mission restarts at full health. Training spars keep their temporary boxing health.
- Reloading the scene clears ragdolls, NPC deaths and vehicle activity. Story checkpoints restore mission progression; exploration checkpoints restore position, equipment and ammunition. If no usable latest checkpoint exists, restart begins at the scene's normal entry. A normal menu load restores saved health; a death/wanted restart restores 100%.
- Pausing or losing focus pauses the failure countdown. Resume it with Escape / Start or the on-screen button. Death, water and active vehicles cannot overwrite the last safe checkpoint.

## Menu fixes

Title screens support arrows / D-pad and Enter / A without starting the game while editing Settings. The ten-section pause menu keeps confirmation focus, scrolls the selected weapon into view and loads a validated checkpoint even when a paused startup controller has not grounded yet. Chapter HUD/menu scaling preserves proportions on narrow and wide screens. Legacy exploration saves without a health field remain loadable at 100%.

## Implementation limits

Water is surface-only at the existing ocean height (supplied island −0.15 m, authored Alcatraz 0 m); there is no diving or oxygen system. The restriction follows sampled dry shoreline geometry: 16 directions at 8 m intervals out to 40 m, refreshed every 0.35 s. The warning starts beyond the 24 m sample band; absence of sampled dry shore within 40 m triggers failure. This is an approximate coastal band, not a surveyed distance or a rectangular world boundary. Boats and NPCs cannot count as dry shore.

The original movement/camera, shooting/knife/boxing, poker, doors, supplied asset bindings and save paths were reviewed or covered by the repository's relevant offline checks. These checks do not establish that every game behavior is free of defects.

## Verification

Executable pure C# checks cover swimming/buoyancy/clamber thresholds, health/failure/countdown, combat, helicopter input, camera framing, checkpoint storage, poker and ammunition. C# grammar and native asset/scene integrity are checked separately. See `Validation/SwimmingHealthAndRestart.json` for the actual results.

Unity 6000.0.62f1 is unavailable in this cloud environment. Unity API compilation, physics, imported animation appearance, menu rendering and a player build remain unverified. In Unity Play Mode, run:

1. **Alcatraz → Validate Movement and Camera (Play Mode)**
2. **Alcatraz → Validate Swimming and Coast Boundary (Play Mode)**
3. **Alcatraz → Validate Player Health and Restart Guards (Play Mode)**
4. **Alcatraz → Validate Shooting Knife and Punches (Play Mode)**
5. **Alcatraz → Validate HUD Layout**

Then play the supplied island: enter/leave water, step onto a low shore, board/leave the stopped boat, cross the warning and wanted boundary, take lethal damage, confirm checkpoint resumption and restored health, and navigate all menu sections with mouse and controller.
