# Alcatraz Escape — Unity source project

**Revision 08 · version 0.8.0 · Unity 6000.0.62f1 · URP**

The playable character is **Elias Vale, a prisoner in orange**, with an escape story. The two default scenes now use an original Alcatraz island adaptation. They retain the five rigged character models, walking animations, footsteps, equipment, NPCs, poker/conversation tables and requested first chapter.

## Open and play

1. Clone this repository, or choose **Code > Download ZIP** and extract it. In Unity Hub, choose **Add project from disk** and select the repository folder containing **Assets**, **Packages** and **ProjectSettings**.
2. Open with **Unity 6000.0.62f1**. Wait for package resolution and FBX import to finish.
3. Choose **Alcatraz > Open Island**, press **Play**, then enter the prison. This is exploration mode with movement, audio and equipment practice.
4. Choose **Play Chapter 01** on the exploration title/pause menu, or **Alcatraz > Open Chapter 01** in the editor, to play the story.

The editor generates the locomotion controller from the included clips after import. If setup is incomplete, choose **Alcatraz > Prepare Characters** and inspect the Console. Assets are included; Unity's declared packages require normal internet access during first resolution.

## New in Revision 08

- User-approved [map and character concept](Documentation/ApprovedConcept/Alcatraz_MapCharacters.png) included as the visual target.
- Original fractured pale shoreline strata and additional coastal scrub, with a new generated ground albedo.
- Connected 2.3 metre coastal service trail, carved terrain, native floor collider, stone parapets and rusty handrails.
- Marine sky, atmospheric daylight, restrained ACES post-processing and depth-aware animated bay water.
- Pale waterfront barracks, blue-gray water tank, facade cornices, downpipes, coping and roof utilities.
- Elias has a dark-haired, lightly stubbled face material and faded orange workwear. Harrow has graying hair and a matte navy uniform. The existing skeletons, facial meshes and animations are retained.
- Source validation workflow, current source previews, and reproducible compressed authoring inventories.

**The approved image is concept art. The included scene is an adaptation using the project's existing character rigs and original environment geometry; it does not exactly reproduce the photorealistic concept.**

See [Revision 08 notes](Documentation/Revision08_ApprovedConcept.md) for the current scope and validation limits.

## Previous Revision 07 additions

- Real openings under all 16 cellhouse skylights; glass no longer casts opaque shadows.
- Dining trays, service grilles, workshop machines, laundry bins, storehouse shelves, shower fittings, a small yard court and dock details.
- A plain orange B-04 outfit for Elias and a blue uniform with badge for Officer Harrow, using edited diffuse textures on the existing rigs.
- Eight additional native NPCs: two guards and six work-detail inmates. There are now 30 actor identities and ten local walking routes.
- Character roster with individual height, build, walking speed and staggered idle phase. Ambient routines check floor support and yield to nearby actors.
- Updated source previews, route checks and opening instructions.

See [Revision 07 notes](Documentation/Revision07_MapCharacters.md) for scope and validation limits.

## Included

| Area | Source implementation |
| --- | --- |
| Alcatraz island | Irregular island mesh, rocky coastline, bay water shader, vegetation and connected roads/paths at multiple elevations. Landmark positions use the NPS map as a reference; dimensions and interiors are adapted for gameplay. |
| Prison | Three tiers; 336 B/C cells; abbreviated A/D rows; 512 regular cell chambers plus seven wider isolation rooms. Furnished cells, stairs, catwalks, bridges, skylight geometry, dining hall, showers and visitation. |
| Landmarks | Recreation yard, lighthouse/keeper, water tower, warden's house, Model/New Industries, power house, storehouse, Building 64, sally port, parade ground and connected dock. Some landmark buildings have simple interiors. |
| Characters | Five MIT-licensed rigged human models with source 2K textures, two edited 1254-pixel uniform atlases, normal maps and URP materials. Orange inmate, separate guard, Black inmates, jacket/hoodie clothing, heavier/leaner variants and 30 actor bindings. |
| Movement/camera | Twelve imported clips, measured walk/run blending, starts/stops/turns, contact IK and pose overlays; shoulder camera, aiming, damping and collision queries. |
| Sound | 44 foundation effects: concrete/metal/wood/grass footsteps, shots, reloads and impacts. Spatial playback, reverb/filtering and the existing 68 English dialogue clips, ambience and score. |
| Equipment | Original prototype knife/pistol/rifle, aiming, finite ammunition, reloads, recoil, muzzle flash, tracers, melee and three targets. General NPC firearm combat/health is not implemented. |
| NPC activities | Ten walking routes, six seated actors and nearby voiced remarks. Poker/conversation tables remain playable in the chapter. |
| Navigation/save | Hold M for the island map, player/objective markers and separate Alcatraz checkpoints. Falling below the bay returns the player to the last grounded position; swimming is not included. |

The project is a source prototype with older rigged character assets. It does not reproduce GTA V/RDR2 production quality. Opsive, paid environment/audio packs and commercial-game assets are not bundled. Unity audio is the default; the existing FMOD bridge requires a separately supplied SDK, events and banks.

## Controls

| Keyboard / mouse | Action |
| --- | --- |
| WASD / mouse | Move / camera |
| Left Alt / Left Shift | Slow walk / run |
| Left Ctrl / Space | Crouch / jump |
| E / Q | Interact / switch shoulder |
| 1 / 2 / 3 / 4 | Unarmed / knife / pistol / rifle in exploration |
| RMB / LMB / R | Aim / use equipment / reload in exploration |
| Hold M / Esc | Island map / pause |

Controller support remains included. See [the chapter guide](README_Chapter01_Revision04.md) for dialogue, phone, poker, retry and checkpoint controls.

## Requested chapter

Mission 1 keeps the timed gang fight and fallen knife, green **Mission completed** or red **Missed** with sound, respect/initiation/tattoo and mandatory knife storage in B-04. Mission 2 rewards a phone and gang contact. Mission 3 includes the rival fight, arrest, 24 hours of isolation represented by 60 seconds sleeping, the guard's knock, Theo's tearful kidnapping reveal and an escape agreement with Malik before next week. The chapter stops at that agreement.

The fight trigger remains four minutes into the opening, designed around the requested 5–6 minute sequence at normal pace. Exploring, reading and travel can extend it. Current dialogue and voices are English; the Arabic story breakdown is at Documentation/Chapter01_Story_AR.md. Alcatraz is a fictional active prison for this contemporary story.

## Build and verification

Install Windows Build Support in Unity Hub, check Play Mode, then choose **Alcatraz > Build Windows x64**. Both scenes build to Builds/Windows/AlcatrazEscape.exe. The batch alternative is Tools/BuildAlcatrazWindows.ps1.

Current offline checks cover native references, static routes, floor support, roster bindings and C# grammar. GitHub Actions repeats source checks; it does not perform a Unity build. The unchanged story, poker and ammunition logic retains the earlier reports; those historical suites were not rerun in Revision 07.

**Unity Editor is unavailable here. Real Unity compilation/import, Play Mode, swept physics, live camera/audio/IK, URP output, performance and a Windows build remain unverified. No executable is included.** Follow [the current Play Mode checklist](Validation/Revision08_PlayMode_Checklist.md) before distributing a build.

## Previews, source and credits

- [Alcatraz source previews](Documentation/AlcatrazPreviews/)
- [Implementation/reference credits](Documentation/Revision06_Alcatraz.md)
- [Character preview](Documentation/FoundationPreviews/Characters.png) and [walking source video](Documentation/FoundationPreviews/Walking.mp4)
- [Asset licenses/credits](Documentation/Revision05_AssetCredits.md)
- [Earlier foundation guide](README_Revision05_Foundation.md)

Previews are labelled offline source renders, **not Unity captures or gameplay**. `Documentation/BlackstoneAuthoring.json.gz.part001` through `part003`, and `Documentation/AlcatrazAuthoring.json.gz`, contain the compressed inventories used by the current Python authoring and preview tools. `authoring_io.py` joins archive parts automatically; their original-byte checksum is in `BlackstoneAuthoring.parts.json`. Large Alcatraz render batches are partitioned into normal native Unity meshes with the same triangles, normals and UVs. This keeps individual publication requests small. See `Tools/requirements.txt`. Offline authoring uses Linux with DejaVu fonts; offline previews also require Mesa EGL/OpenGL. Run `python Tools/build_alcatraz.py` to regenerate both Alcatraz scenes, or `python Tools/render_alcatraz_preview.py A01_Island A15_CoastalPath A16_PrisonerPortrait` for labelled source renders. Opening/building in Unity uses the included native assets and does not require Python.

Earlier Blackstone scenes and reports are retained for history. The two enabled scenes and Revision 08 reports describe the current project. Older reports are historical. Rocketbox's MIT notice and existing MakeHuman, Poly Haven, audio and voice credits are included. Scanned surfaces are **Powered by Poly Haven**. No Unity WIP or Sketchfab mesh is redistributed.
