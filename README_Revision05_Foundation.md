# Blackstone Island — rebuilt character foundation

**Revision 05 / version 0.5.0 · Unity 6000.0.62f1**

Elias Vale is the prisoner in orange clothing. This complete Unity source project recreates the character, movement, equipment and audio upgrade inside the existing 32-cell coastal prison. The original chapter is preserved, and a second story scene applies the new characters to it. The chapter ends when Elias and Malik agree to plan their escape together.

## Download, open and play

1. Extract the entire ZIP. In Unity Hub, choose **Add project from disk** and select the included **DesertShift** folder containing `Assets`, `Packages` and `ProjectSettings`.
2. Open it with **Unity 6000.0.62f1**. Allow package resolution and asset import to finish. URP, Input System and Cinemachine dependencies are declared in `Packages/manifest.json`.
3. Choose **Blackstone > Open Character Foundation**, then press **Play**. Select **Enter the prison** with the mouse, Enter or controller A.
4. To play the requested chapter with the new characters, choose **Play Chapter 01** on the exploration title/pause screen, or **Blackstone > Open Story With New Characters** in the editor.

The editor generates the locomotion controller from the supplied FBX clips after first import. If the title reports an incomplete setup, choose **Blackstone > Prepare Character Foundation** and check the Console. Model and sound files are already included; only Unity's normal package resolution requires downloading after extraction.

The optional `Blackstone_ArtAuthoring_SourceFiles.zip` contains raw art/audio authoring inputs and the offline geometry inventory. Extract it beside the main ZIP's extracted `DesertShift` folder to merge those inputs into the project. It is needed only for reauthoring and full offline source audits; opening, playing and building in Unity use the main project alone.

## Included

| Area | Rebuilt behavior and assets |
| --- | --- |
| Characters | Five complete rigged human models, 2K body/head textures, normal maps and URP materials. Orange prisoner clothing, separate guard clothing, Black inmates and heavier/leaner NPC variants. All 22 original actor bindings receive new models. |
| Movement | Twelve actual source clips: idle, three walks, two runs, start/stop, two turns, crouch idle and seated idle. Blending uses measured gait speeds; contact IK and pose overlays supplement the clips. |
| Camera | Shoulder camera, aim zoom, shoulder switch, damping, recoil and collision checks. Directed chapter shots are retained. |
| Audio | 44 new recorded/derived effects: four footstep surfaces, pistol/rifle shots, reloads, impacts and handling. Contact footsteps, 3D placement, reverb and obstruction filtering. Existing 68 voiced dialogue clips, ambience and score remain included. |
| Equipment | Original knife, pistol and rifle prototype prefabs, aiming, finite ammunition, timed reloads, recoil, muzzle flash, tracers, melee and three training targets. |
| Prison | 32 cells, two floors, stairs, yard, canteen, showers, workshop, visitation, isolation cells, coastal scenery, lighting and scanned surface textures. Exploration adds a small range and footstep pads. |
| NPCs/tables | Five walking routes, six seated actors and nearby voiced remarks. Poker and the conversation table remain playable in the chapter. |

Exploration mode opens doors for map testing and leaves mission logic inactive. Firearms are range practice equipment; general NPC health and firearm combat are not implemented. The chapter's rival fight retains its three-strike interaction.

## Exploration controls

| Keyboard / mouse | Controller | Action |
| --- | --- | --- |
| WASD | Left stick | Move |
| Mouse | Right stick | Camera |
| Left Alt | Light stick pressure | Slow walk |
| Left Shift | L3 | Run |
| Left Ctrl held | B held | Crouch |
| Space | A | Jump |
| E | X | Door interaction |
| Q | RB | Switch shoulder |
| 1 / 2 / 3 / 4 | D-pad left cycles | Unarmed / knife / pistol / rifle |
| RMB | LT | Aim |
| LMB | RT | Use equipment |
| R | Y | Reload |
| Esc | Start | Pause / resume |

Volume and camera sliders use the mouse. Chapter dialogue, phone, poker, failure retry and checkpoint controls are in [the chapter guide](README_Chapter01_Revision04.md).

## Requested first chapter

The upgraded story retains the timed gang fight and fallen knife; green **Mission completed** or red **Missed** with sound; initiation and tattoo; mandatory knife storage in B-04; phone reward and call; rival fight and arrest; 24 hours of isolation compressed to 60 seconds sleeping; the guard's knock; Theo's tearful kidnapping reveal; and the escape agreement with Malik before next week. No later missions are added.

The opening is designed for roughly 5–6 minutes at normal pace. Taking longer to explore/read dialogue extends it. Current text and voices are English; the Arabic breakdown is included at `Documentation/Chapter01_Story_AR.md`.

## Build and verification

After checking Play Mode, install Windows Build Support and choose **Blackstone > Build Foundation Windows x64**. Both new scenes build to `Builds/Windows/BlackstoneIsland.exe`. A batch alternative is `Tools/BuildFoundationWindows.ps1`. The older build menu builds the preserved classic chapter.

Offline checks passed for file integrity, FBX skin weights/matching skeleton paths, sound recordings, preserved story assets and pure ammunition/story/poker logic. The logic suites executed **254 + 84 + 1,171 assertions**. C# source was checked against temporary API scaffolds.

**Unity Editor was unavailable during reconstruction. Real Unity compilation, import, animation/IK, live physics/camera/audio, URP output, performance and a Windows build remain unverified. No compiled executable is included.** Follow `Validation/Revision05_PlayMode_Checklist.md` before distributing a build.

These are older rigged human assets and original prototype equipment. They do not reproduce RDR2/GTA V graphical quality or the exact reference face. Opsive and paid audio libraries are not included. Built-in Unity audio is the default; the optional FMOD bridge requires a separately supplied SDK, events and banks.

## Files and credits

- [Foundation details and integration](Documentation/Revision05_Foundation.md)
- [New asset credits/licenses](Documentation/Revision05_AssetCredits.md)
- [Character source preview](Documentation/FoundationPreviews/Characters.png)
- [Source walking video](Documentation/FoundationPreviews/Walking.mp4)
- [Original map previews](Documentation/BlackstonePreviews/)
- [Preserved chapter guide](README_Chapter01_Revision04.md)

Previews are labelled offline source/geometry renders, not Unity screenshots or gameplay. Rocketbox's MIT notice is included. New recordings use credited CC0 sources and original Foley. Existing MakeHuman, Poly Haven and voice credits are retained; scanned surfaces are **Powered by Poly Haven**. No commercial-game assets are redistributed.
