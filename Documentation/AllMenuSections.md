# All ten pause-menu sections

The supplied [design PDF](Alcatraz_All_Menu_Sections.pdf) guides the connected pause screens in both exploration and Chapter 01. They share the cinematic background and condensed headings, with a compact ten-row sidebar, cream text, gold rules and red active-page highlighting.

| Section | Game behavior |
| --- | --- |
| Map | Current island/cellhouse map, player and objective markers; an annex schematic for the factory, carport, warehouse and return door. |
| Mission | Live Chapter 01 objective and stage, or the exploration objective. |
| Inventory | ID, uniform, knife location, phone and tattoo status from actual chapter state. Unacquired items are labelled accordingly. |
| Character | Actual health and boxing stamina, gang respect, contacts, day and successful combat hits. |
| Weapons | All eleven exploration loadouts with actual ammunition, equipment selection and scrollable cards. Story equipment remains mission-controlled. |
| Journal | Notes unlocked by actual contacts, knife concealment/stashing, gang membership, phone, isolation, family news and escape agreement. |
| Settings | Display mode/resolution, available quality presets, master/effects/music/dialogue volumes, camera sensitivity/inversion and subtitles. Only the implemented English language is shown. |
| Save Game | Latest/autosave plus three separate manual checkpoint slots, timestamps and overwrite confirmation. |
| Load Game | Valid saved slots, empty/invalid-slot labels, and confirmation before replacing current progress. |
| Exit to Main Menu | Return-to-title confirmation with a cancel option. |

The PDF’s sample cigarettes, radio parts, stealth scores, suspicion values, save times and completion percentages are not presented as live game data. Existing story state and equipment provide the displayed values instead. Inventory/character line illustrations are original UI drawings, not in-game model captures.

Arrow keys or controller D-pad move between sections. Left/right choose the save slot or loadout; Enter/controller A selects the action. Esc/Start resumes through the existing input system. Clicking menu actions stays paused. A save/load confirmation disables the controls underneath it. Menus use the existing uniformly fitted 1920 × 1080 canvas.

## Checkpoints

Chapter checkpoints retain the existing autosave filenames and backup compatibility. Manual slots use `.slot1.json` through `.slot3.json` alongside the original file. Loading a missing/corrupt chapter checkpoint is refused rather than silently starting a new game. Decoded story invariants and position bounds are checked before loading or writing.

Exploration checkpoints use a separate scene-specific namespace and restore player location, island/cellhouse/annex context, selected equipment and ammunition. They do not restore NPC health, world physics, story progression or temporary sparring state. The save/load screen states this limit. Safe exploration autosaves run at thirty-second intervals during active play; the title’s first action resumes a valid latest checkpoint. Explicit location shortcuts take precedence over checkpoint restoration. Exploration saves require grounded control outside vehicles/activities, and loading checks the floor and space at the destination. These live physics checks still require Unity verification.

The shared disk writer uses temporary files, atomic replacement and a retained `.bak`; invalid primary saves fall back to a valid backup. Rejected ammunition restores leave the weapon state unchanged, and accepted restores copy their arrays and clear pending reload/cooldown state.

## Preview and validation

Browse [all ten sections](AllMenuSections.html), view the [preview gallery](AllMenuPreviews.html), or download the [ten-page preview PDF](AllMenuSectionsPreview.pdf). The previews use example initial exploration values and are explicitly labelled as offline layouts. Their widgets illustrate layout; game actions are implemented in Unity. Regenerate HTML with `python Tools/create_all_menu_previews.py`, and line art with `python Tools/author_menu_assets.py`.

- 34 executable checkpoint/file/ammunition assertions passed, including slot separation, atomic replacement, corrupted-primary recovery, rejected writes and invalid ammunition.
- The existing 160,041 poker/weapon assertions passed after the weapon snapshot change.
- All 80 C# files passed grammar parsing; native asset integrity and 214 map/binding checks passed.
- All ten browser layouts passed font/image loading, unique active selection and uniform-fit checks at 1920 × 1080, 1280 × 720, 3440 × 1440 and 1024 × 768. Browser sidebar click and arrow navigation passed.

Results are recorded in `Validation/AllMenuSectionsChecks.json`. Unity import, C# compilation against Unity assemblies, final font metrics, menu click targets, physics restoration and gameplay transitions remain unverified because the editor is unavailable. The PDF preview is not a Unity capture.
