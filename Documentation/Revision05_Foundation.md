# Revision 05 implementation and integration

## Scenes

| Scene | Purpose |
| --- | --- |
| `SC_BlackstoneFoundation.unity` | Default exploration/equipment test. Chapter components are inactive; the prisoner starts in the yard. |
| `SC_BlackstoneStory_Upgraded.unity` | Original chapter plus a character bootstrap. Story, tables, checkpoints, pacing, dialogue and directed shots stay enabled. |
| `SC_BlackstoneIsland.unity` | Preserved classic chapter with original characters. |
| `SC_DesertTown.unity` | Retained DesertShift scene. |

`FoundationBootstrap.Start` runs before other Start callbacks, after the original scene's Awake callbacks. It disables legacy animation/gesture components, hides their renderers, instantiates the supplied profiles and binds the new skeletons. Story props are preserved and retargeted. Actor routes and mission references keep their original object identities.

The upgraded chapter differs from the original scene only by the bootstrap root and its SceneRoots entry. The original scene SHA-256 and all 104 protected code/anatomy/audio files are checked by `Tools/validate_foundation.py`.

## Models and movement

Five facial FBXs are in `Assets/Game/Resources/BlackstoneFoundation/Characters`. Each has approximately 3,300–3,900 control points, 6,700–7,600 source polygons and 80 skin clusters. Heavy/lean variants scale the same model; separate sculpted weight blend shapes are not supplied.

`RocketboxImporter` imports only these new models/12 clips as Generic rigs. Every material slot maps to native URP materials, including alpha cutout hair. Color and normal maps are 2K. Inmate/guard clothing is adapted; original textures and source/license provenance remain included.

`FoundationPreparation` creates `Resources/BlackstoneFoundation/Locomotion.controller` from Unity's imported clip subassets. It is generated during first import because the correct subasset IDs require Unity. **Prepare Character Foundation** repeats setup; `ImportRevision.txt` records successful preparation.

The gait sources contain horizontal root travel. The importer anchors X/Z and turn rotation; the existing controller/NPC routes own movement. Blend thresholds use source travel divided by duration and compensate for visual scale. `GaitSpeeds.json` records the measurements.

Crouch idle/seated idle use supplied clips. Moving crouch, airborne pose, grips, reload dip, melee, speaking and story gestures are code overlays, not separate captured performances. Contact/grip IK uses world directions to avoid assuming imported bone axes.

## Equipment and built-in audio

Exploration starts with 12 loaded/60 reserve pistol rounds and 24 loaded/96 reserve rifle rounds. Equipping cancels reload; pause freezes reload/cooldown time. Rifle input can be held; pistol/melee use individual presses. Aim is checked from the camera, then muzzle, with a chest-to-muzzle obstruction check. Only training targets register hits. NPC health, firearm reactions, ragdolls, cover and combat AI are outside this foundation.

`WeaponState` is independent of Unity and passed 254 executed assertions. Weapon meshes/prefabs are original prototypes.

`FoundationAudio` uses 24 3D sources, reverb/low-pass filters and nonrepeating variations. Contact footsteps raycast the floor's existing `SurfaceTag`. Sand tags use the grass/earth-like group; metal uses concrete plus plate Foley. Story mode follows the chapter mixer. Original dialogue, score and ambience remain active.

## Optional external systems

Opsive, paid audio packs and FMOD SDK/banks are not bundled or installed. The default foundation runs with built-in Unity systems. Import licensed packages into a working copy when available and avoid two systems driving the same character.

`FoundationFmodBridge` compiles only with `BLACKSTONE_FMOD`. Supply FMOD's Unity integration and built banks; create 3D events `event:/Blackstone/<WAV-stem>`; add the symbol in Player settings; set `FoundationFmodBridge.Enabled = true` after bank loading. Default is false. It controls `bus:/` pause/volume and per-event pitch/volume. Missing-event exceptions fall back to built-in audio. It has not been compiled against an FMOD SDK or tested with banks.

References: [FMOD Unity documentation](https://www.fmod.com/docs/2.03/unity/), [Opsive](https://opsive.com/assets/ultimate-character-controller/), [Unity animation postprocessing](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AssetPostprocessor.OnPostprocessAnimation.html).

## Reauthoring and verification

Assets are already included. Gameplay does not run Python. Optional authoring requires Python, NumPy, SciPy and Pillow; audio additionally requires ffmpeg. Source previews require Mesa/OpenGL and ffmpeg. Authoring scripts write assets when invoked.

Raw `Tools/ArtSources` inputs and `Documentation/BlackstoneAuthoring.json` are delivered separately in `Blackstone_ArtAuthoring_SourceFiles.zip` to keep the main download smaller. Extract both archives into the same parent directory; their `DesertShift` trees merge. Install this optional source pack before reauthoring or running the full offline audits. All files under `Assets`, the Unity packages/settings, scripts, licenses, final recordings and previews are in the main ZIP.

| Tool | Purpose |
| --- | --- |
| `download_foundation_assets.py` | Fetch MIT source models/clips, verify Git blob hashes and convert textures. Network required only for reauthoring. |
| `prepare_foundation_assets.py` | Adapt clothing, generate materials, process included source recordings and measure gait speeds. |
| `build_foundation_scene.py` | Rebuild equipment/test assets and both new scenes from the classic chapter. |
| `preview_foundation_characters.py` | Render actual source FBX samples outside Unity. |
| `validate_foundation.py` | Check skins/hierarchies, recordings, scene bindings and chapter preservation. |
| `validate_project.py` | Check native references, mesh buffers, images, audio and source syntax. |
| `validate_revision.py` / `validate_prison_revision.py` | Check retained dialogue/tables, prison dimensions and sampled static routes. |

Older `build_blackstone.py`/`build_project.py` regenerate their original scenes and reset build settings. Use them only for intentional reauthoring, then rerun the foundation scene tool to restore new build scenes.

Reports under `Validation` distinguish actual portable logic execution from API scaffold checks and file inspection. None proves Unity import/Play Mode behavior. Follow the Play Mode checklist and resolve Console errors before building.
