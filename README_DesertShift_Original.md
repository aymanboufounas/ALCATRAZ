# Desert Shift

An original Southwest desert exploration slice, authored as a populated Unity scene with editable native mesh assets, materials, prefabs and C# source. Start with **START_HERE.txt**.

**Delivery status:** implementation and offline asset checks are provided. The required Unity import, compilation, Play Mode, humanoid validation and performance tests remain unverified because the Unity Editor was unavailable. This is not a certified production release or a built `.exe`.

## Open and play

Extract the whole archive, add the `DesertShift` folder in Unity Hub, and use Unity **6000.0.62f1 / 6.0 LTS**. Let the official packages resolve. Open `Assets/_DesertShift/Scenes/SC_DesertTown.unity`, press Play and click the Game view. The map is already saved in the scene; you do not need Python or a generation step to open it.

| Control | Action |
| --- | --- |
| W / A / S / D | Camera-relative movement |
| Mouse | Orbit camera |
| Left Shift | Sprint forward |
| Left Ctrl, held | Crouch; standing is blocked by low ceilings |
| Space | Jump |
| E | Use the targeted door, cabinet or switch |
| F | Flashlight |
| Esc | Pause and release cursor |
| Click / Esc while paused | Resume |
| F3 | Toggle diagnostics; hidden by default |

## Included world

- A 600 × 600 metre principal terrain with coarse surrounding ground and distant mesas, a two-lane road, shoulders, utility lines, guardrail, signs, sparse sage/grass/yucca, rock formations, worn trails and environmental clues.
- The original **Sundowner 84** motorhome: approximately 8.6 × 2.5 × 3.2 metres; cream body, orange stripe, glazed openings, mirrors, lights, tires, arches, vents, bumpers, badging, license plates, exhaust, side door and entry steps.
- An RV interior with cab seats, dashboard and wheel, wood floor, kitchenette, sink, cupboards, overhead storage, benches, table and fictional field-science props. The centre aisle and actual door opening are preserved.
- A composed campsite: two lawn chairs, table, radio, lantern, cooler, toolbox, water containers, crates, spare tire, barrels, generator, cables and refuse.
- **Sunset Splash Car Wash**: three through bays, hoses, spray lances, controls, brushes, drains, wet surfaces, puddles, residue and lights. An office, staff room, storage, restroom and utility room sit in the attached block.
- Office equipment, cleaning stores, a vending machine, bench, parking lines and stops, pylon sign, dumpster, fence, cameras, roof equipment and a usable exterior staircase with roof access.
- Reusable environment, character, prop and door prefabs. Meshes and materials are actual assets, not missing Asset Store references.

## Elias Calder

The original character uses a 22-transform rig, weighted native meshes, glasses, facial details, a pale jacket, muted green shirt, brown trousers, shoes, belt and watch. The rig builds a Humanoid Avatar at runtime for retargeting.

The supplied original animation clips contain **direct bone curves** and use a separate Generic playback Avatar on the same skeleton. This avoids treating bone curves as muscle-based Humanoid clips. `CharacterRig.HumanoidAvatar` exposes the Humanoid mapping for later retargeted animation. This is a procedural stylized character pass; the rig and deformation still need inspection in Unity before production use.

The Animator Controller includes a directional movement blend tree, a crouch blend, and jump/landing states. Fourteen clips cover idle, forward/backward walking, both strafes, jog, run, crouch idle/walk, jump start/loop/land and left/right turns.

## Runtime systems

- Unity Input System actions; CharacterController movement with acceleration, braking, gravity, jump buffering, short coyote time, slope handling and a crouch clearance test.
- Cinemachine 3 third-person follow with mouse orbit, pitch limits, shoulder offset, collision avoidance and configurable sensitivity.
- `IInteractable`, camera spherecast targeting with distance/occlusion limits, reusable opening/closing/locked doors, and a wash-light switch.
- Hinged doors open away from the player and check small movement increments for player obstruction. This needs a live collision test in Unity.
- Warm sun, atmospheric sky/fog, runtime URP Volume with ACES, subtle bloom and vignette. Depth of field, motion blur and chromatic aberration are not added.
- Reflection probes refresh once on entering Play Mode. A light-probe layout is included for a future bake. The current scene uses ambient lighting without baked GI.
- The official URP SSAO feature is added at runtime where the installed package exposes it. The manual rendering repair/build workflow saves that feature into the renderer asset for build stripping. Its runtime output has not been verified here.
- Original synthesized wind, bird, generator, wash and drip clips; surface-based footsteps for sand, concrete, metal, wood, wet concrete and asphalt.
- Shared materials with instancing enabled, static flags on eligible renderers, batched vegetation chunks, distance culling through LOD Groups, restrained textures, a 90 metre shadow distance and 128px reflection probes. No measured FPS claim is made.

## Manual tools

Nothing regenerates or deletes the map when Unity opens.

| Desert Shift menu command | Purpose |
| --- | --- |
| Open Desert Town | Open the supplied scene after handling unsaved changes |
| Validate Scene | Check loaded meshes, materials, scripts, skins, doors and core references |
| Repair Rendering Configuration | Repair URP assets in place and resolve post-processing data |
| Rebuild Animation Bindings | Resave native curves using the installed Unity editor |
| Capture Six Cinematic Views | Write 1080p captures while in Play Mode; staged player positions are restored |
| Build Windows x64 | Build to `Builds/Windows/DesertShift.exe` |

`Tools/BuildWindows.ps1` provides the equivalent batch build. Windows Build Support must be installed for the selected Unity editor. The player is not included precompiled.

The optional Python authoring source is in `Tools/`. `build_project.py` manually recreates authored assets and overwrites the supplied scene. Keep a copy before running it after your own edits. It requires NumPy, SciPy and Pillow; Unity itself does not require those tools.

## Validation and remaining gates

`Validation/OfflineValidation.json` records native YAML parsing, internal file references, asset GUIDs, vertex/index buffer sizes, finite geometry values, normalized skin weights, bone indices, required scene objects, C# delimiter checks and Python syntax checks. A delimiter check is **not C# compilation**.

`Documentation/Previews/` contains geometry previews rendered through a separate Mesa/OpenGL renderer from the same authoring data. They are labelled and are not Unity screenshots. URP appearance may differ.

Complete `Validation/PLAY_MODE_CHECKLIST.md` in Unity before calling the project stable. Unity import compatibility, exact animation playback/deformation, avatar validity, rendered shader output, live traversal, collision edge cases and 60 FPS performance are open verification gates. Baked lighting and baked occlusion data are not provided.

## Originality and dependencies

The models, fictional signs, textures, procedural animation data and synthesized audio were created for this project. No television screenshots, show logos, exact actor likeness, real branded RV model, Asset Store packs, multiplayer, accounts, ads, shop or backend are included. The field equipment supplies environmental storytelling and no chemistry instructions.

Only official Unity packages are requested by `Packages/manifest.json`: URP 17.0.4, Input System 1.11.2, Cinemachine 3.1.7, their official transitive dependencies and built-in modules. Unity downloads these; Unity source/binaries are not redistributed in the archive.

API references consulted: [Unity target editor release](https://unity.com/releases/editor/whats-new/6000.0.62f1), [Cinemachine for Unity 6.0](https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.cinemachine.html), [Cinemachine Third Person Follow API](https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/api/Unity.Cinemachine.CinemachineThirdPersonFollow.html), [URP renderer data API](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/api/UnityEngine.Rendering.Universal.UniversalRendererData.html), [URP render requests](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/User-Render-Requests.html).
