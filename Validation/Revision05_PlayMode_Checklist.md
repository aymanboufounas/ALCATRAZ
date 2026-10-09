# Revision 05 — required Unity verification

These checks have not been performed. Record Unity version, platform, Console output and pass/fail results before distributing a build.

## Import/setup

- [ ] Open `DesertShift` in Unity 6000.0.62f1; finish import with no compiler errors.
- [ ] Run **Prepare Character Foundation**. All five Generic avatars are valid and the Resources controller is generated.
- [ ] Inspect body/head/hair materials, normals and hair alpha. No pink/default Standard slots.
- [ ] Open **Character Foundation**, enter Play Mode: one visible orange prisoner and 21 NPCs; old bodies stay hidden.

## Movement/map/camera

- [ ] Test keyboard/controller walk, slow walk, run, start/stop, turns, backward, strafe, jump and crouch. Check sliding, bones, clipping and head clearance.
- [ ] Walk B-04, both galleries/stairs, canteen, showers, workshop, yard and visitation; open exploration doors.
- [ ] Check camera against bars/walls/stairs/doors, aim zoom, shoulder switch, sensitivity and pause/resume.
- [ ] Observe five routes, player/wall avoidance, speech pauses, seated models/furniture and size variants.
- [ ] Review skin, normals, lighting, shadows, probes, quality presets and measured target-device frame rate.

## Audio/equipment

- [ ] No idle/air footsteps. Contacts sound correctly; concrete, metal, wood and turf differ; crouch is quieter.
- [ ] Verify 3D attenuation, obstruction/reverb, dialogue clarity and volume sliders.
- [ ] Equip all slots; check grips, orientation, support hand, melee and reload poses.
- [ ] Shoot all targets; check hit flashes/counts, aim rays, tracers, flash, recoil and sound variations.
- [ ] Shots do not bypass walls between body/muzzle and target.
- [ ] Test partial/full reloads, depletion, reserve exhaustion, equip interruption and pause midway. Time freezes and ammo is finite.
- [ ] Test Resources loading/shaders in a standalone build. FMOD is disabled; validate real events/banks separately if later enabled.

## Upgraded chapter

- [ ] Open **Story With New Characters**; test new game, checkpoint restoration and prisoner start in B-04.
- [ ] Complete the opening naturally in about 5–6 minutes. Check fight, knife from Niko's new hand, 22-second hide window, green success/red failure and sounds.
- [ ] Fail/retry the knife incident; activity tables yield to the mission.
- [ ] Complete initiation/tattoo, B-04 knife storage, phone reward/call; check props, subtitles and voice timing.
- [ ] Play poker/use conversation table; check seats/hands/camera transitions and exit poses.
- [ ] Finish rival three-strike fight and arrest; both fighters enter separate solitary cells.
- [ ] Sleep 60 active seconds. Pause stops the clock. Check horizontal pose and wake reset.
- [ ] Check knock, guard, visitation receiver, Theo crying/kidnapping reveal, return and final Malik agreement. No later mission starts.
- [ ] Check classic/upgraded scenes and save compatibility independently.
- [ ] Build with **Build Foundation Windows x64**, then test exploration/chapter loading in the executable.
