# Revision 09 — supplied weapons and reference HUD

The exploration scenes now use the supplied 10mm pistol and PBR revolver as the actual held equipment, alongside the original service rifle and knife. The HUD follows the reference's dark panels, amber accents, upper goal/identity panels, lower-left minimap and right-side weapon cards. Every card reads its magazine/reserve values from the same `WeaponState` used to fire and reload. The source-mesh thumbnails are packaged PNG assets.

| Key | Equipment | Starter ammunition |
| --- | --- | --- |
| 1 | Unarmed | — |
| 2 | Combat knife | — |
| 3 | Supplied 10mm pistol | 15 / 75 |
| 4 | Original service rifle | 30 / 120 |
| 5 | Supplied revolver | 6 / 36 |

D-pad left cycles all five slots. RMB / LT aims, LMB / RT uses the selected weapon and R / Y reloads. The rifle supports a held trigger; the pistol and revolver use individual trigger presses. Switching equipment interrupts a reload. Pause freezes reload/cooldown time. The imported gun models are scaled to a 23 cm pistol and 32 cm revolver, aligned along the weapon's forward axis and given a muzzle transform for the existing raycast/flash/tracer handling. The revolver uses the existing pistol sound recordings with a stronger recoil; no new recorded revolver audio was supplied.

Chapter 01 retains its mission-controlled equipment and existing scripted interior. The exploration inventory does not bypass its mission state.

Executed .NET 8 C# tests passed **468 assertions** covering finite ammo, cooldowns, magazine transfers, canceled reloads, pause, inactive-card readouts and complete depletion of all 42 revolver rounds. C# grammar and native asset integrity checks also passed. Unity API compilation, weapon alignment in the animated hand, shader import and Play Mode still require verification in Unity 6000.0.62f1.

Visual inspection of the source house also identified two below-ground reflection objects using ordinary materials (`TreeBranches.001` and `WindowLightRefl`). Preparation now excludes them, avoiding a misleading house bounding height and mirrored geometry beneath the dock.
