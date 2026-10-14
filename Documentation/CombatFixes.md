# Guns, knives and punching

Exploration weapons now damage human NPCs through shared 100-point health. This
includes the supplied police officer, the static Shephard figure and the rigged
exploration cast. Scripted Chapter 01 characters retain their mission-controlled
combat; the chapter does not expose the free-exploration weapon system.

Pistol, M9A3 and PX4 hits deal 34 damage; rifle/Colt M5 deal 30; PMX deals 20;
revolver deals 50; BRX1 and machete deal 45; knife deals 35. Jab, cross and hook
deal 9/17/21 before boxing guard reductions. Sparring continues to use separate,
temporary health and does not permanently damage participants through punches.
Damage is finite, clamps at zero and cannot be reapplied to an already downed NPC.

Gun/knife impacts flash an NPC's materials briefly and show the existing hit marker.
Rigged defeated NPCs stay down using the existing ragdoll; their patrol, boxing,
footsteps and gesture overlays stop. Static supplied models tumble as rigid bodies
because they have no humanoid rig. Downed actors no longer start ambient remarks
or get moved into poker seats. NPC health resets when the scene is reloaded.

NPC ragdolls disable their standing collider while down to prevent self-collisions;
nonlethal knockdowns restore it during recovery. Successful punches also register
practice-target hits and use the same hit-marker counter as guns and knives.

## Mechanics fixes

- Weapon switches validate the required model before changing equipment, avoiding
  an invisible weapon with active ammo/firing state.
- Knife/machete damage is delayed until the swing's contact point, rather than
  occurring during windup. Close initial-overlap contacts are included, and pending
  hits cancel when switching equipment or blocking gameplay controls.
- Crouched firearm grips follow the lowered body; airborne limb poses preserve gun
  grips and active knife hand poses instead of overwriting them.
- Jab/cross/hook timing is controlled by boxing rather than a second, unrelated
  weapon cooldown. The first attack is a jab. Crosses and hooks require their full
  20-point stamina cost; stamina cannot go negative from starting a punch.
- Queued punches cancel when controls are blocked, the player sits, changes weapons
  or loses grounded/external-control readiness. Crouched contact/hand poses are
  lowered with the character.

## Checks and remaining validation

`Tools/Tests/CombatTests.cs` exercises mixed gun/knife/punch damage, invalid damage,
death/overkill handling, all weapon damage values, stamina costs and shot/ammunition
accounting. It is compiled and executed in CI alongside the existing poker/weapon
and helicopter input suites.

In Unity, resume Play Mode and use
**Alcatraz > Validate Shooting Knife and Punches (Play Mode)**. It exercises actual
shooting impact methods against temporary NPC colliders, wall occlusion, close
knife contact, canceled knife windup, lethal static-NPC damage, punch stamina and
seated attack cancellation. The fixture is removed after running.

Also review actual aiming/held models, recoil/reload motion, knife blade orientation,
jab/cross/hook animation and contact timing, crouched attacks, NPC knockdowns and
corpse collisions in exploration. Unity API compilation, this physics fixture,
visual attack motion, ragdoll stability and player builds remain unverified here
because the editor is unavailable. Passing source/rule checks is not gameplay
validation.

Cloud checks executed for this change: all 77 C# grammar files passed, 33 new
combat health/weapon/stamina assertions passed, and the existing 160,041
poker/weapon assertions passed. The ten-assertion Unity combat fixture remains
unexecuted.
