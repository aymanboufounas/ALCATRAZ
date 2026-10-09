# The Silent Blueprint: Blackstone Island — Chapter 01

Updated **inside the supplied DesertShift Unity project**. Original desert scene and assets are retained. The default build scene is now the original Blackstone prison chapter requested in Arabic: earn gang respect, receive a phone, fight a rival, serve isolation, learn of the father’s kidnapping, and agree an escape plan.

**Revision 04 / version 0.4.1:** Elias is clearly identified as the prisoner: orange shirt and trousers, printed INMATE / Elias Vale / B-04 identification, a prisoner title screen and a permanent escape objective. The cell block now has **32 cells across two floors**, two upper galleries and a 21-step stairway. The eastern court contains an accessible canteen and showers, and the existing workshop contact now has an open-front workshop. Prison signs, gallery lamps, checkpoints and perimeter razor wire make the setting clearer. The approved player anatomy, movement, contact footsteps, dialogue recordings and shipping mission logic are preserved. The chapter still ends at the agreement to escape together.

The coastal island, detailed human face/neck/hand meshes, 2K skin and scanned surface textures from Revision 03 remain included. Ambient light has been increased for interior readability; its final appearance needs checking in Unity.

**Status:** source prototype with a mixture of original procedural art and adapted CC0 art and packaged neural English voices. Unity Editor import, compilation against real Unity assemblies, Play Mode, skin deformation, final URP output and Windows build remain unverified because Unity was unavailable. No precompiled .exe is included.

## Open and play

1. Extract the complete ZIP to a new folder. Open the included **DesertShift** folder in Unity Hub with **6000.0.62f1**.
2. Let URP 17.0.4, Input System 1.11.2, Cinemachine 3.1.7 and built-in modules resolve.
3. Choose **Blackstone > Open Chapter 01**. This opens `Assets/Game/Scenes/SC_BlackstoneIsland.unity`.
4. Press Play, then select **New game — Enter Cell B-04**. Elias starts inside his cell. Use **Continue checkpoint** to resume an existing save at its saved location.

Rendering package references and native animation bindings receive a one-time editor repair after import. This does not generate, erase or replace the map. The manual **Blackstone > Repair Rendering and Animation** command is also available.

## This chapter

| Segment | Playable behavior |
| --- | --- |
| First respect | Meet three contacts, explore the yard, watch the fight after the four-minute routine, conceal Niko’s fallen knife within 22 seconds. Green `Mission completed` on success; red `Missed`, failure sound and R/Y retry on expiry. |
| Gang initiation | Niko introduces Malik; Elias joins Blue Meridian, gets the visible forearm tattoo and must store the knife in B-04 before the phone unlocks. |
| Trust line | Receive a phone from Niko and answer Malik’s voiced call. The phone remains available afterwards. |
| Yard trouble | Confront and punch a rival. Three valid strikes cause the guard arrest scene; both fighters go into separate solitary cells. |
| Isolation | Interact with the bed and sleep for 60 seconds of active, unpaused play, representing 24 hours. The guard wakes Elias by knocking. |
| Visit | Use the near-side visitation receiver. Theo cries and reveals their father was kidnapped by the Cinder Syndicate, the same gang that framed Elias. |
| Escape agreement | Return to B-04, reflect, then talk to Malik. Six days until next week; Malik will escape with Elias if he earns enough cooperation. This is the requested stopping point. |

The first mission usually takes about 5–6 minutes at normal pace, but slower exploration or dialogue interactions can extend it. The player starts in **Cell B-04**, as **Elias Vale the prisoner**. The guard is an NPC. Yard activities are optional; when the story incident begins, poker closes and the mission takes priority.

## Controls

| Keyboard / mouse | Xbox-style controller | Action |
| --- | --- | --- |
| WASD | Left stick | Camera-relative movement / analog speed |
| Mouse | Right stick | Orbit camera |
| Left Alt | Light stick pressure | Slow walk |
| Left Shift | L3 | Sprint |
| Left Ctrl held | B held | Crouch with head clearance |
| Space | A | Jump |
| Space during dialogue | A during dialogue | Advance the current line after its brief opening |
| E | X | Contextual interaction |
| LMB | RT | Unarmed punch during the rival fight |
| RMB | LT | Aim / strafe movement and closer camera |
| Q | RB | Switch camera shoulder |
| P | D-pad right | Answer/open/close phone |
| R | Y | Retry missed knife incident / new game at title |
| F | D-pad up | Flashlight |
| Esc | Start | Pause / resume |
| F3 | — | Diagnostics |

Settings and pause buttons use the mouse. Gameplay, title continue/new game, pause/resume and mission retry have controller bindings.

At the poker table, use **E / X** to sit down. Click cards to keep them, then click **Draw & reveal** or press **R / Y**. On a controller, D-pad left/right selects a card and X toggles KEEP. **P / B** leaves the table; Esc/Start pauses. One deck supplies both hands and both draws. Scores follow five-card poker rules including ace-low straights and tied kickers. This is a friendly game without a betting economy. Wins are per-session; story progress is saved separately.

Use **E / X** at the conversation table to sit and hear the optional yard conversation. It does not advance a mission or award duplicate respect.

## Included implementation

- 26 data-driven dialogue scenes, **68 packaged neural speech clips**, five voice identities, and **25 original SFX/ambience/music clips**. Dialogue timing follows the recorded clips. Talking actors look toward their partner and receive jaw/head/hand gestures. Subtitles are larger and lines can be advanced with Space/A.
- Separate indoor and yard ambience with a location-dependent crossfade, quieter tension music, spatial footsteps and nearby conversation, softer door/knife/phone/card effects, and a filtered phone voice. Master, dialogue, effects and music controls remain available. Audio pauses with gameplay.
- Ten body/face/clothing profiles include heavy, lean and athletic bodies, different skin tones including Black inmates, and haircuts. The player/model prefabs at `Assets/Game/Prefabs/Characters/PF_EliasVale_Player.prefab` and `PF_EliasVale_Model.prefab` use newly authored clothing and retargeted CC0 anatomical meshes and a 23-bone articulated rig with a jaw. Forearm colors match the source wrist atlases; collar, wrist and waist joins have been refined.
- Displacement-driven gait, stance-foot planting, two-bone leg posing, ankle/toe rollover, breathing, pelvis movement, arm swing and blended seated poses. Foot sounds follow contact events and choose concrete or metal variants. Walking, acceleration, braking and camera damping were retuned.
- Four roaming inmates and a patrolling guard stop along authored routes; six inmates sit at the two tables, and another exercises. Routes use obstacle checks and pause during story cinematics. The yard also has cards, chips, cups, newspapers, benches, a basketball hoop, weights and perimeter details.
- A two-floor cell block with 32 cells, walkable upper galleries, stairs and rails. B-04 retains its original story spawn and knife stash. Upper cell interiors are furnished behind locked bars.
- An accessible canteen with tables, benches and food counter; showers with changing bench, sinks and stalls; and an open-front inmate workshop around the original mission contact. The eastern checkpoint opening remains connected to visitation and isolation. Administration remains exterior scenery.
- Coastal terrain, 68 rock outcrops, procedural pine/olive trees and groundcover, a service court, perimeter barriers, razor wire and directional signs. The minimap reflects the prison facilities and indicates the current gallery level. The next escape chapter is still outside this deliverable.
- Six scanned 2K surface sets with URP normal/metallic-smoothness/AO maps, real face/hand UVs, physical box UVs and subtle cloth folds.
- Late-afternoon daylight, warmer indoor lamps, clouded sky, animated water shading/shore foam, higher-resolution shadow atlases, restrained ambient fill and warmer color grading. Cell block, yard, two solitary cells, visitation booth, props, cameras and interactions are native Unity assets; no generation step is required to play.
- Camera-relative movement, aim strafing, controller deadzones, crouch clearance and Cinemachine collision remain part of the player controller.
- Checkpoints store phase, contacts, respect, membership, tattoo, knife location, phone, game day, sleep time, abduction revelation and escape agreement. Saves live under Unity’s persistent application directory, with a backup JSON file. Save timers and cinematics pause with gameplay.
- Low/Medium/High/Ultra settings change shadow distance/cascades, MSAA, render scale and texture mip limit; resolution/fullscreen, VSync, camera sensitivity/invert and audio volumes are available.
- `CharacterTest.unity` has a floor, stairs, slope and low-ceiling passage. It uses the same prisoner controller and camera.

## Verification

Read `Validation/Revision04_PrisonChecks.json`, `Validation/Revision03_ArtChecks.json`, `Validation/Chapter01_OfflineValidation.json`, `Validation/OfflineValidation.json`, `Validation/Revision02_AssetChecks.json`, `Validation/Chapter01_LogicChecks.txt` and `Validation/Chapter01_PlayMode_Checklist.md`. Earlier-named asset reports are regenerated against the current files.

The actual Unity-independent shipping story state was compiled and executed with Mono: **84 assertions passed**, covering gates, failure/retry, rewards, pause clocks, sixty-second isolation and the requested ending. Shipping poker rules passed **1,171 assertions** covering category order, all 1,024 ace-low suit patterns, kickers, ties, invalid hands and deck uniqueness. Chapter-specific local-reference, audio and coarse AABB navigation checks passed. The 33 runtime/editor C# files passed a temporary Unity API stub type check; this is not compilation against Unity assemblies and cannot certify package compatibility or runtime behavior.

Revision 04 checks cover the prisoner role, 32-cell layout, stair dimensions, landing alignment and five static routes through the galleries and facilities. A comparison with the supplied Revision 03 archive confirmed that 104 protected anatomy, movement, story and audio files are byte-for-byte unchanged. Static box/capsule samples do not establish that Unity movement or camera physics will behave correctly.

`Documentation/BlackstonePreviews/` contains **13 labelled offline geometry previews**, including the cell galleries, canteen, showers, prisoner identification, both tables, a portrait, the island and the service court. Invisible physics-only slabs are excluded from these previews. Seated poses are static illustrations for geometry review. These images are not Unity screenshots and do not reproduce URP lighting, live animation or gameplay.

Use **Blackstone > Validate Chapter** after Unity import. Build a Windows player with **Blackstone > Build Windows x64**, after installing Windows Build Support. Equivalent batch command: `Tools/BuildBlackstoneWindows.ps1`.

## Editing and source

- Arabic story breakdown: `Documentation/Chapter01_Story_AR.md`.
- Current prisoner/map revision: `Documentation/Revision04_Changes_AR.md`.
- Previous anatomy/coastal revision: `Documentation/Revision03_Changes.md`.
- Arabic earlier revision notes: `Documentation/Revision02_Changes_AR.md`.
- Dialogue: `Assets/Game/Resources/Blackstone/story-dialogue.json` and `Documentation/Chapter01_Dialogue.md`.
- Missions: `Assets/Game/Scripts/Missions/PrisonStoryState.cs` and `PrisonStoryDirector.cs`.
- Optional scene/art authoring: `Tools/build_blackstone.py`, `prison_character.py`, `realistic_characters.py`, `prison_details.py`, `prison_facilities.py`, `coastal_art.py`; requires Python, NumPy, SciPy and Pillow. `refine_dialogue.py` writes revised text; `refine_sounds.py` writes the sound effects. These tools can overwrite their authored assets when explicitly run.
- Optional neural voice production: `Tools/produce_neural_dialogue.py`, using an external Piper installation and `BLACKSTONE_PIPER_MODEL` pointing to the LibriTTS-R medium model. The engine/model are not bundled and are not needed to play: all WAVs are already included. Voice credits and production hashes are in `Documentation/ThirdParty_Audio_Credits.md` and `VoiceProduction_Provenance.json`.
- `author_chapter_audio.py` is the retained first-revision audio authoring tool. Running its main entry point would replace the current text and neural recordings with the older scratch version; use the revision tools above for current assets.
- Original Desert Shift readme: `README_DesertShift_Original.md`. Its old `build_project.py` regenerates the original demo and switches the default scene back; do not run it while editing this chapter.

Story text, gang names, signs, sound effects and the procedural environment are original. Character anatomy/skins use adapted CC0 MakeHuman assets and scanned surfaces use CC0 Poly Haven assets; credits are in `Documentation/ThirdParty_Art_Credits.md`. Scanned materials: **Powered by Poly Haven**. Current speech was generated locally using Piper and a LibriTTS-R model; attribution is included. No GTA, Rockstar, Prison Break or other commercial-game assets, code, animations or recordings are included. This prototype does not claim comparable graphical quality.

Primary API references: [Unity persistentDataPath](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Application-persistentDataPath.html), [Input System actions](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/Actions.html), [Cinemachine third-person follow](https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/api/Unity.Cinemachine.CinemachineThirdPersonFollow.html), [URP asset API](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/api/UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset.html), [built-in Vehicles module](https://docs.unity.com/en-us/engine/6000.0/manual/packages-list/packages-all/pack-build).
