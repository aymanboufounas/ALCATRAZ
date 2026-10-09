# Unity acceptance checklist — not run in the authoring environment

Editor: __________  GPU: __________  Resolution: 1920 × 1080  Date: __________

These are open tests, not a record of passing results. Use a fresh extracted copy.

- [ ] Import the project, resolve all official packages and confirm C# compilation.
- [ ] Open SC_DesertTown and run Desert Shift → Validate Scene.
- [ ] Enter Play Mode; confirm no Console errors or missing scripts/materials.
- [ ] Move forward, backward and sideways using WASD.
- [ ] Orbit the camera and check both vertical limits.
- [ ] Sprint and release sprint; verify acceleration and braking.
- [ ] Hold crouch; try to stand beneath a low obstruction.
- [ ] Jump, land, and jump against a ceiling; check slope traversal.
- [ ] Walk to the RV and approach the right-side steps.
- [ ] Target and open the RV door from outside.
- [ ] Enter the RV, move along the aisle, and inspect the cab and rear dinette.
- [ ] Operate kitchen cabinet doors and leave the RV.
- [ ] Open/close a door from each side and stand in its path; verify blocking.
- [ ] Walk along the camp trail to the asphalt road.
- [ ] Follow the road to Sunset Splash and enter each wash bay.
- [ ] Enter the office, then staff/storage/restroom/utility rooms.
- [ ] Toggle the office switch and confirm wash lights change.
- [ ] Use the exterior stairs, cross the landing and reach both roof heights.
- [ ] Inspect idle, walk, backward, strafe, jog, sprint, crouch and jump blending.
- [ ] Inspect elbows, shoulders, knees and hips for unacceptable skin deformation.
- [ ] Confirm CharacterRig reports a valid Humanoid Avatar, and the Generic bone clips play.
- [ ] Check the camera beside walls, below roofs, in the RV and near the player mesh.
- [ ] Check flashlight, pause/resume, focus loss and the hidden-by-default F3 overlay.
- [ ] Listen to environment audio and footsteps on each surface.
- [ ] Confirm the sky, fog, shadows, wet materials, reflections and post-processing work.
- [ ] Capture the six cinematic views and inspect full-resolution output.
- [ ] Profile outside, inside the RV, inside bays and on the roof for at least 60 seconds each.
- [ ] Build Windows x64 and repeat the main traversal in the actual executable.

Record failures with the exact Console message, scene location, reproduction steps and screenshot. Fix and repeat the affected check. Do not infer a performance result from the offline geometry previews.
