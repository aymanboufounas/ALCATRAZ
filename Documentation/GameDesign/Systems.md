# ALCATRAZ — gameplay systems and interaction contracts

This document describes the current source behavior and the acceptance checks needed before calling that behavior playable. It is a design and implementation reference, not evidence that Unity gameplay, imported animation, physics, or a packaged build has passed. Values below are code defaults unless identified as fixed rules; serialized scene or prefab values can override serialized defaults.

The intended presentation is a visible third-person prisoner in a readable, grounded prison environment. The user's graphics target is a high-end PC at 1440p / 4K. That target does not establish a measured frame rate, hardware specification, finished animation quality, or build size. See [MovementQuality](../MovementQuality.md), [player visibility and NPC grounding](../PlayerVisibilityAndNPCGrounding.md), and [hourly checks and graphics](../HourlyChecksAndGraphics.md) for previous implementation notes and their validation limits.

## 1. Modes and scene boundaries

The [build scene list](../../ProjectSettings/EditorBuildSettings.asset) enables these three scenes, in this order:

| Scene | Source configuration | Gameplay contract |
| --- | --- | --- |
| `SC_AlcatrazSuppliedIsland` | `storyMode: 0`, supplied exterior layout | Exploration with supplied environment, cellhouse/annex travel, equipment and placed activities. |
| `SC_AlcatrazIsland` | `storyMode: 0` | Exploration using the classic island layout and components present in that scene. |
| `SC_AlcatrazChapter01` | `storyMode: 1` | Scripted Chapter 01 progression, dialogue and rival brawl. |

[FoundationBootstrap](../../Assets/Game/Foundation/Scripts/FoundationBootstrap.cs) creates the shared imported avatars, third-person camera, swimming and player vitals. It attaches `FoundationWeapons` only in exploration. General NPC `FoundationDamageable` components are attached in exploration; the story player is damageable in both modes. A scene having a shared pause section does not mean every exploration activity is available there.

[FoundationHUD](../../Assets/Game/Foundation/Scripts/FoundationHUD.cs) loads Chapter 01 as another Unity scene. Supplied cellhouse and annex visits use controlled teleportation within the active exploration scene through [SuppliedIslandWorld](../../Assets/Game/Supplied/Scripts/SuppliedIslandWorld.cs) and [SuppliedExtrasWorld](../../Assets/Game/Supplied/Scripts/SuppliedExtrasWorld.cs). Death and restricted-water failure reload the current scene, then resume its latest usable checkpoint or starting session.

**Unexecuted Unity acceptance — SYS-SCENE:** enter each enabled scene through its title, exercise its available actions, travel into and out of supplied interiors, open Chapter 01, and return to the title. Record the active scene, player visibility, control state and checkpoint behavior at each transition. An unavailable component must yield an unavailable option or explicit message, rather than silently substituting another mode.

## 2. Input, capture and state ownership

[PlayerInputHandler](../../Assets/_DesertShift/Scripts/Player/PlayerInputHandler.cs) defines the common action map. `CanControl` is `IsCaptured && !GameplayBlocked`. Capture locks the cursor and sets `Time.timeScale` to 1; releasing capture frees the cursor and sets it to 0. `GameplayBlocked` suppresses ordinary movement and combat while allowing a captured cinematic, phone or activity to advance. Losing application focus releases capture.

Several systems cooperate through booleans and explicit restoration; there is no single authoritative gameplay-state stack. The table describes current responsibilities, not a claim that every conflicting transition has passed testing.

| State owner | Movement / input | Camera / presentation | Exit responsibility |
| --- | --- | --- | --- |
| Title HUD | Blocks gameplay; capture released | Presents title over scene | Enter session only when foundation setup reports `Ready`. |
| Normal player | CharacterController owns collision; `CanControl` required for actions | `FoundationCamera` follows imported body | Pause, activity or cinematic hands off ownership. |
| Pause / focus loss | Capture released; scaled gameplay time stops | Pause HUD uses shared sections | Resume capture; do not reopen gameplay during a blocking activity. |
| Story director | Blocks gameplay during dialogue, phone and cinematics | Story shots / letterbox can own view | Restore story input and camera on cinematic completion. |
| Vehicle | `ExternalControl` disables walking controller | Vehicle follow target; passenger mesh deliberately hidden | Release seat, visibility and camera before safe disembarkation. |
| Poker | Blocks gameplay and sets `ExternalControl` | Seated body and activity camera; cursor available | Restore saved position, rotation, poses, NPC states and camera. |
| Fall / ragdoll | `ExternalControl` suspends normal walking | Follows pelvis for player knockdown | Find safe standing point, blend to animation, release control; death stays down. |
| Failure controller | Reasserts gameplay block; stops boxing / closes poker | DEAD or WANTED overlay | Reload scene after countdown; restore a fresh session. |
| Shared graphics | Does not own player motion, camera pose or culling | Runtime URP clone and game-camera rendering options | Restore prior pipeline and camera options on owner destruction. |

### Current controls

Xbox-style button names below describe Unity's generic gamepad bindings; device labels can differ. The direct keyboard/gamepad reads in foundation components supplement the common action map.

| Context / action | Keyboard / mouse | Gamepad | Notes |
| --- | --- | --- | --- |
| Move / swim / vehicle steering | WASD | Left stick | Stick dead zone is configured in the action map. |
| Look | Mouse movement | Right stick | Disabled while gameplay is blocked. |
| Sprint / fast swim | Hold left Shift | Hold left-stick press | Sprint is suppressed by aim, walk, crouch and external control. |
| Slow walk | Hold left Alt | No dedicated binding | Do not advertise a separate gamepad walk button. |
| Crouch | Hold left Ctrl | Hold B | Hold action, not a toggle; in helicopter this button descends. |
| Jump / surface stroke / low shore clamber | Space | A | Clamber additionally requires movement toward a qualifying shore. |
| Interact / board / attempt exit | E | X | Nearby prompts and mode gates decide the interaction. |
| Aim / boxing guard | Hold right mouse | Hold LT | Guard applies with unarmed equipment; swim disables aim. |
| Attack | Left mouse | RT | Fire, exploration punch or knife according to equipment; story brawl has its own handler. |
| Reload in exploration / retry missed story incident | R | Y | Same key has different context-specific behavior. |
| Exploration equipment slots | 1 unarmed, 2 knife, 3 pistol, 4 rifle, 5 revolver | D-pad left cycles all equipment | Mouse wheel also cycles all 11 entries. |
| Swap camera shoulder | Q | RB | Normal third-person view. |
| Restore third-person view | V | Right-stick press | Refused while activity, cinematic, failure or ragdoll owns the player/view. |
| Exploration inventory overlay | Hold Tab | Hold LB | HUD overlay; not a persistent inventory simulation. |
| Exploration full map | Hold M | Hold View / Select | Chapter 01 also has its pause-menu Map section; do not promise this exploration shortcut in every mode. |
| Story phone | P | D-pad right | Available when story state and cinematics allow it. |
| Flashlight | F | D-pad up | Action binding exists; requires the scene's flashlight bootstrap. |
| Pause / resume | Esc | Start | Requires `PauseEnabled`; focus loss also pauses. |
| Advance dialogue after minimum hold | Space | A | Uses captured input even when normal gameplay is blocked. |
| Helicopter rise / descend | Space / left Ctrl | A / B | Simultaneous rise and descend cancel. |
| Leave poker | P | B | Overrides the ordinary meaning of these buttons while table is active. |
| Poker check/call / fold | On-screen buttons | X / Y | Raise and all-in use the on-screen controls; full pad navigation is not established. |
| Title / pause navigation | Up/down arrows, Enter | D-pad up/down, A | Pause left/right changes save slot or selected weapon. |
| Cancel save/load confirmation | Backspace | B | Confirmation keeps navigation focus until resolved. |
| Chapter title shortcuts | E to continue if possible; R to start new | X / Y | Separate from highlighted option selection with Enter / A. |

**Unexecuted Unity acceptance — SYS-INPUT:** verify the table with keyboard/mouse and a gamepad, including reused keys in story, poker and vehicles. Pause, lose focus and resume in each context. Inputs must not leak through an active confirmation, title, failure screen or cinematic into attacks or movement. Full input rebinding, complete controller-only settings/poker operation and per-device remapping screens are proposed improvements, not established features.

## 3. Visible prisoner and third-person camera

At startup, [FoundationBootstrap](../../Assets/Game/Foundation/Scripts/FoundationBootstrap.cs) waits for supplied assets when required, loads the generated locomotion controller, creates an imported body, enables its renderers and parent objects, normalizes its orientation and fits its measured skinned geometry to the player controller. Original visuals are retained until replacement geometry has passed setup. Measurements exclude held weapon `MeshRenderer` props, so a gun cannot make a missing body pass validation. The body must have usable skinned geometry, an acceptable size and an acceptable offset from its controller.

The bootstrap installs [FoundationCamera](../../Assets/Game/Foundation/Scripts/FoundationCamera.cs), includes body layers in the gameplay camera's culling mask, hands legacy third-person controllers to the external driver and disables a competing Cinemachine brain on that camera. A missing or invalid avatar/controller causes an explicit setup failure and blocked gameplay rather than an invisible controllable prisoner. This fallback cannot guarantee a visible character if the scene's retained legacy visuals are themselves invalid.

The normal camera boom is 3.15 m; aiming requests 1.9 m. It smooths following, swaps shoulders, applies gun recoil, contracts immediately against obstruction, separates an already-overlapping camera probe and considers alternative horizontal orbit angles. When all normal candidates fail, it considers elevated views at 35°, 55° and 70°. The pure [CameraFramingRules](../../Assets/Game/Foundation/Scripts/CameraFramingRules.cs) rank candidates with minimum usable distances and a field-of-view policy: normal open view 58°, suitable aim view 48°, close/elevated framing up to 72°.

The foundation camera deliberately keeps character rendering enabled in narrow spaces. Geometric constraints can still prevent a clear full-body frame; the source reports failed recovery rather than proving universal visibility. It does not implement a first-person camera mode.

On the first ordinary controllable frame, automatic view recovery is attempted once. V/R3 can retry. Recovery restores the imported body and its parents, render flags, culling layers, camera tag and driver, clears stale activity overrides only when no current activity owns them, then checks presentation and framing. It refuses unsafe resets during vehicles, poker, cinematics, phone use, failure and recovering ragdolls. Vehicle boarding intentionally hides the passenger mesh and is an explicit exception to normal visible-prisoner presentation.

**Unexecuted Unity acceptance — SYS-VIEW:** record the entire prisoner on entering all three scenes, then walk/run, rotate 360°, aim, crouch and jump in open ground. Repeat in cells, gallery corners, under low ceilings and alongside cliffs; camera must not enter solid geometry or deliberately hide the body. Verify V/R3 after a normal teleport and after leaving each activity. A failed reset must produce a useful message. Use **Alcatraz → Inspect Player and Camera** to capture mesh bounds, active camera, renderer and driver evidence; do not close a visibility defect based on source checks alone.

## 4. Locomotion, animation and falls

[PlayerMovement](../../Assets/_DesertShift/Scripts/Player/PlayerMovement.cs) uses a CharacterController. Serialized defaults are walk 1.45, jog 2.15, sprint 5.5 and crouch 1.15 m/s, acceleration 8.5 and deceleration 12 m/s², gravity −19.6 m/s² and jump height 1.05 m. Input magnitude is clamped. Free movement rotates toward travel; aiming preserves camera-relative strafing. Air control is reduced, landing recovery reduces speed and direction changes use [MovementResponseRules](../../Assets/Game/Foundation/Scripts/MovementResponseRules.cs).

Jump input has a 0.12 s input buffer and ground grace window, followed by a 0.09 s preparation. Overhead collisions cancel upward movement. Landing captures impact speed and recovery duration. The controller shrinks toward a 1.13 m crouch capsule and refuses to stand into an obstruction. Step support prevents normal downward stairs from becoming repeated falls; slope travel uses the supporting plane. Wall and protected-ledge contact reject blocked velocity so a sprint does not retain momentum into a wall. Unsafe ledge protection is an optional exploration setting, not universal invisible fencing. A player below −40 m is teleported to its last supported point.

[FoundationAvatar](../../Assets/Game/Foundation/Scripts/FoundationAvatar.cs) drives imported animation from measured travel, local direction, crouch, air and seated state. `applyRootMotion` is false; animation follows controller movement. [LocomotionAnimationRules](../../Assets/Game/Foundation/Scripts/LocomotionAnimationRules.cs) selects start, stop, run-start, run-stop and stationary-turn signals with hysteresis and elapsed-time logic. Recent running memory lasts 0.35 s while lower-speed movement continues; releasing movement freezes the stop choice during braking. Dedicated strafe clips are not shipped by this path: existing gait playback direction plus leg/torso correction approximate aiming movement.

Foot correction lifts a mildly penetrating foot toward local support without dragging a normal swing foot down. Moving crouch, swimming, weapon grips, punches, jump preparation and landings include procedural bone overlays. Swimming uses procedural treading/paddling on the imported rig, not an authored swimming clip. Their existence does not establish commercial motion-capture fidelity or Rockstar animation behavior.

[FoundationFall](../../Assets/Game/Foundation/Scripts/FoundationFall.cs) builds a jointed ragdoll on the imported skeleton. Hard landings over 10.5 m/s can knock the player down. Nonfatal recovery waits, finds a floor and clear standing capsule or falls back to a supported point, then blends to animation over 0.85 s. `StayDown` prevents lethal ragdolls from automatically standing. Airborne and landing overlays cooperate with held weapon hands.

**Unexecuted Unity acceptance — SYS-MOVE / SYS-ANIM:** compare 30/60/120 FPS captures for acceleration, stop distance and turning. Test wall stops, side steps, stair descent, slopes near the controller limit, crouch ceilings, buffered jump, ledge jump and head collision. Sprint → release must select one run-stop; sprint → walk for 30 s → release must select an ordinary stop. Check aim strafing, foot clearance, held grips, nonfatal ragdoll recovery and lethal stay-down visually. Pure rule assertions establish arithmetic/state behavior only; they do not prove final poses or floor contacts in an imported scene.

## 5. Exploration equipment and damage

[FoundationWeapons](../../Assets/Game/Foundation/Scripts/FoundationWeapons.cs), [WeaponState](../../Assets/Game/Foundation/Scripts/WeaponState.cs) and [CombatHealth](../../Assets/Game/Foundation/Scripts/CombatHealth.cs) implement equipment actions in exploration. Equipment is immediately selectable when its resource and required hand binding exist; the current source does not implement a weapon acquisition economy, loot progression or carry-weight system. A missing native model keeps the current equipment and reports an error.

| Equipment | Magazine capacity | Starting reserve | Damage per accepted contact |
| --- | ---: | ---: | ---: |
| Unarmed | — | — | Jab 9; cross 17; hook 21 |
| Knife | — | — | 35 |
| Pistol | 15 | 75 | 34 |
| Rifle | 30 | 120 | 30 |
| Revolver | 6 | 36 | 50 |
| Machete | — | — | 45 |
| M9A3 | 17 | 68 | 34 |
| PX4 | 17 | 68 | 34 |
| PMX | 30 | 120 | 20 |
| BRX1 | 10 | 40 | 45 |
| ColtM5 | 30 | 120 | 30 |

Firearms start with full magazines. Rifle, PMX and ColtM5 use held automatic fire at a 0.13 s cooldown. Other firearms use a new attack press; revolver cooldown is 0.40 s, other semiautomatic firearms 0.26 s. Reload takes 2.7 s for revolver, 2.2 s for automatic weapons and 1.7 s for other firearms. It transfers only available reserve up to capacity. Switching equipment cancels reload; blocked gameplay pauses state ticking.

Gun aiming first finds the nearest non-self camera-ray contact within 90 m, then tests the chest-to-muzzle path and muzzle-to-aim path. The nearest wall or actor remains solid; actor layers are not globally removed merely because they match the shooter. A successful contact can damage an NPC or practice target and produces an appropriate hit marker, spatial impact sound, muzzle light/tracer and camera recoil. There is no projectile ballistics, penetration, weapon accuracy simulation, headshot multiplier or general NPC shooting AI in this path.

Knife and machete begin a 0.35 s action with contact scheduled at 0.16 s; use cooldown is 0.58 s. Contact checks a close overlap, then a camera-directed sphere sweep up to 1.7 m, filtering the player's hierarchy and respecting the nearest obstacle. Attack gating blocks equipment while seated, swimming, under external control, paused or without normal control. Swimming hides the held weapon and cancels a pending melee contact. Firearms do not share the boxing controller's grounded-only restriction.

[FoundationDamageable](../../Assets/Game/Foundation/Scripts/FoundationDamageable.cs) starts at 100 health, rejects invalid or duplicate post-death damage and flashes the affected renderer. Lethal NPC damage disables story/routine motion, footsteps, activity posing and boxing; a fall component stays down, otherwise a Rigidbody fallback receives the impulse. This is a damage/death response, not a complete retaliation, investigation or police response system.

**Unexecuted Unity acceptance — SYS-COMBAT:** fire each firearm at a practice target and NPC, with and without a wall between camera, muzzle and victim. Verify nearest hit, no self-hit, one ammo decrement, empty handling, held automatic behavior, reload reserve/capacity and reload interruption. Check knife windup, range and obstruction, cancellation when entering water, seated NPC damage and persistent NPC death. Inspect weapon scale, grip and muzzle alignment for every imported model; state tests cannot verify their appearance.

## 6. Boxing and the story brawl

[FoundationBoxing](../../Assets/Game/Foundation/Scripts/FoundationBoxing.cs) implements exploration unarmed jab/cross/hook contacts. Combo durations are 0.42/0.55/0.64 s, with contact at 43% of the action. Stamina costs are 12/20/20; stamina regenerates at 18 per second or 8 while guarding. A frontal guard with enough stamina reduces received damage to 15% and spends stamina. Attacking requires an active animator, unarmed equipment, normal control and a grounded, non-swimming player. Seated NPCs can still receive damage even though seating prevents their own attacks.

The punch overlap selects the closest eligible target in front within 1.2 m and checks a world-layer line of sight. It can strike fighters, damageable NPCs, a punching bag or a practice target. Procedural arms and chest motion present the combo. Nearby exploration Tomas can initiate a 45 s sparring session; sparring has temporary health and AI approach/guard/attack behavior, distinct from lethal general combat.

Chapter 01 uses [PrisonStoryDirector.UpdateBrawl](../../Assets/Game/Scripts/Missions/PrisonStoryDirector.cs), not free exploration equipment. The player must land three valid strikes near the rival with clear contact before arrest progression. The player's story strike cooldown is 0.55 s, reach 2.4 m. The rival approaches, strikes within 2 m at approximately 1.7 s intervals and deals 12 health damage when a world-layer obstruction does not block it. Leaving the brawl's yard area teleports the player back. The concealed story knife remains a mission state rather than a usable exploration weapon.

**Unexecuted Unity acceptance — SYS-BOX:** verify combo rhythm, stamina refusal, frontal versus rear guard, nearest-target contact, wall obstruction and bag motion. Finish and interrupt a Tomas spar without leaving either actor suspended. In Chapter 01, misses must not count, three valid strikes must progress to arrest, and sustained rival damage can reach the shared death flow. Confirm punches and health feedback remain readable at target resolutions.

## 7. Swimming, coast warning and restricted water

[FoundationSwimming](../../Assets/Game/Foundation/Scripts/FoundationSwimming.cs) enables water behavior only around an available active exterior island map, outside the prison interior and annex. It uses water level −0.15 m for supplied layout, otherwise 0 m, and finite exterior coordinate limits. [SwimmingRules](../../Assets/Game/Foundation/Scripts/SwimmingRules.cs) distinguishes deep water from shallow supporting ground with hysteresis: entry/exit thresholds differ to avoid flicker.

Swimming retains the CharacterController, so the player remains subject to coast, pier, wall and boat collisions. Normal/fast swimming uses 1.6/2.45 m/s, bounded buoyancy keeps the feet near 1.2 m below the surface, and the head is intended to remain above water. Jump adds a short surface stroke; moving toward a shore while jumping can attempt a clamber. A valid clamber must be within 1.1 m reach, onto a walkable surface 0.05–0.60 m above water, with clearance for the standing capsule along the lift and forward path. This is surface swimming; no underwater diving, breath meter, drowning damage, stamina exhaustion or underwater navigation is implemented here.

The restricted boundary measures approximate distance to real dry shore and docks. It samples 16 directions at 8 m radius increments through 40 m; if none finds dry land it reports 48 m. Measurements refresh approximately every 0.35 s. Thus “24 m warning / 40 m restricted” are thresholds on a sampled measure, not an exact authored polygon or precise shortest coast distance.

- Above a sampled 24 m: display **RESTRICTED WATERS AHEAD — turn back toward the island**.
- Above a sampled 40 m: latch restricted state, show **WANTED**, block control and restart through the failure controller.
- An occupied non-aircraft boat crosses the same boundary; aircraft do not use this water-failure rule.
- Interior, annex and unavailable-map contexts do not produce exterior water warnings.

The chosen user requirement is wanted alert followed by mission restart. General wanted stars, police pursuit, offshore combat and successful water escape are not implemented by this rule.

**Unexecuted Unity acceptance — SYS-WATER:** enter/leave water at several coasts, docks and shallow banks; test idle treading, fast swim, low-shore clamber and obstruction by railings, piers and boats. Approach the restricted boundary in several directions swimming and boating, verify warning → WANTED → checkpoint restart, and verify no stale warning after interior travel/restart. Record the actual sampled coast measure; do not fail the test solely because a visual estimate is not exactly 40 m.

## 8. Player health, falling damage and restart

[CombatHealth](../../Assets/Game/Foundation/Scripts/CombatHealth.cs) represents 0–100 health; new sessions start at 100. The [vitals HUD](../../Assets/Game/Foundation/Scripts/FoundationPlayerVitals.cs) displays the ceiling of health as a percentage and a proportional bar; below/equal 40 uses the low-health color. During ordinary active sessions, damage reduces health and 0 initiates death. Player damage is refused outside a playable active session, when normal control is blocked, during external control or after failure. Vehicle/poker/ragdoll immunity through these gates is current source behavior, not a simulation of exposure in every activity.

[PlayerFailureRules](../../Assets/Game/Foundation/Scripts/PlayerFailureRules.cs) applies falling damage above 10.5 m/s: `(landingSpeed − 10.5) × 8`, capped at 100. Swimming is excluded from landing damage. Nonfinite or nonpositive damage is rejected. There is no automatic health regeneration, consumable healing or armor model established by this path.

Death sets the player's fall component to stay down. Restricted water uses the same failure flow with another reason. Failure closes active poker, stops boxing, blocks gameplay and displays **DEAD** or **WANTED** for a three-second scaled countdown. Focus loss or pause stops that clock. On completion it reloads the active scene and sets a scene-specific restart marker. Startup consumes that marker, attempts the latest checkpoint and restores health to 100. With no usable exploration checkpoint it enters the starting session; story startup resumes its valid latest checkpoint when available, otherwise starts the chapter. A failed scene reload exposes a retry action instead of silently continuing a dead session.

**Unexecuted Unity acceptance — SYS-VITALS:** verify new-session 100%, damage amount/bar correspondence, finite clamping, fall threshold, lethal stay-down and one failure transition. During the failure countdown test pause/focus loss, then resume. Confirm no movement, attack or checkpoint overwrite after failure. Restart with a valid checkpoint, no checkpoint and rejected exploration location; confirm appropriate session entry, 100% health and cleared water/activity/camera state. Test reload failure handling in a controlled test context rather than claiming it happened in a normal build.

## 9. NPC floors, routines and activities

[ActorGrounding](../../Assets/Game/Scripts/AI/ActorGrounding.cs) addresses NPC roots without controller gravity. Standing actors periodically seek a nearby walkable world-layer floor and clear standing capsule. Recovery is bounded to ±1.1 m so it cannot intentionally jump between distant tiers; patrol steps use ±0.35 m. The nearest appropriate support is chosen without lifting a blocked actor onto intervening furniture. Seated, sleeping, suspended, talking, dead and recovering ragdoll actors are excluded as appropriate.

[FoundationAgent](../../Assets/Game/Foundation/Scripts/FoundationAgent.cs) follows authored routes at actor speed, waits at waypoints, checks world obstacles, nearby player and other NPCs, and commits a step only when `ActorGrounding.TryStep` finds support. It is local route following, not a general NavMesh path planner, crowd simulation or procedural city-life system. Story actors also use their authored director/actor path. [FoundationActorPose](../../Assets/Game/Foundation/Scripts/FoundationActorPose.cs) presents activity poses; [FoundationConversations](../../Assets/Game/Foundation/Scripts/FoundationConversations.cs) can play selected nearby ambient lines with occlusion and dead-actor guards.

**Unexecuted Unity acceptance — SYS-NPC:** inspect every living standing NPC at startup and after a patrol cycle in each enabled scene, including all gallery levels, exterior slopes and stairs. Feet should meet a nearby supporting floor; a temporarily blocked route should wait rather than enter a wall, furniture or a void. Verify seating, conversation, sleep and dead/ragdoll exceptions do not get forcibly stood up. The runtime inspector's floor report supplements visual inspection and does not prove all future route states.

## 10. Boat and helicopter

[FoundationVehicle](../../Assets/Game/Foundation/Scripts/FoundationVehicle.cs) implements Rigidbody patrol-boat and helicopter controls where those vehicles are placed. Only one vehicle may be active. Boarding requires ordinary control, no current external-control owner and proximity within 4 m. It disables normal walking collision, hides passenger renderers while remembering their prior values, marks the avatar seated and uses a follow distance of 7 m for boat / 9 m for helicopter.

The boat applies four-point buoyancy, throttle, steering torque and sideways damping. The helicopter uses target-height lift control, forward acceleration, yaw and stabilizing pitch/roll; target altitude is clamped relative to the sea and 180 m. This is an accessible prototype flight model, not a real helicopter simulation. Rotor speed ramps visibly; vehicle controls require current player control. [VehicleControlRules](../../Assets/Game/Foundation/Scripts/VehicleControlRules.cs) resolves rise/descend input consistently across keyboard/gamepad.

Exit requires speed at or below 1.4 m/s and a clear candidate. Four nearby directions are tested for acceptable dry ground with standing capsule clearance. The boat can instead release into available, clear swimmable water. Aircraft require suitable ground; there is no midair exit/parachute mechanic. Release restores passenger renderers, walking control and third-person follow; disabling an active vehicle also releases ownership.

**Unexecuted Unity acceptance — SYS-VEHICLE:** board, steer, pause and disembark both vehicle types with keyboard and pad. Reject exit while moving or without a safe destination. Test boat exit onto dock and into water, aircraft landing/blocked exit, vehicle disable during occupancy and subsequent view recovery. The prisoner must reappear on exit; deliberate hidden passenger rendering must not persist into walking. Verify boat restriction failure and record helicopter stability/performance in a real scene.

## 11. Texas Hold'em and activity return

[PrisonPokerTable](../../Assets/Game/Scripts/Activities/PrisonPokerTable.cs) starts a four-seat table with Elias, Samir, Tomas and Luis, each at 500 chips. The table uses [HoldemGame](../../Assets/Game/Scripts/Activities/HoldemGame.cs) for game rules, legal actions, AI decisions and hand progression. The UI exposes fold, check/call, raise, all-in, next hand and leave. This session's chips are an activity resource; no persistent prison economy, real-money flow or saved in-progress hand is implemented.

Entry requires ordinary control, no other external-control owner and, in story mode, an allowed yard-activity stage. It saves the player's return position/rotation and previous state, seats the player, suspends/repositions eligible opponents, blocks ordinary gameplay, enables the activity camera and shows the cursor without pausing the table. Story can close it when progression makes the activity unavailable.

Closing settles the departing player's hand through fold or already-committed all-in, then restores player and surviving captured opponents, camera, input block and cursor. Story saves taken during poker use the return position, not the seat, to avoid resuming trapped inside an activity. Exploration pause save/load is unavailable while the player's external control is owned by poker.

**Unexecuted Unity acceptance — SYS-POKER:** complete a legal hand including check/call, fold, raise, all-in, showdown and AI turns; test leave mid-hand, next hand and empty-stack handling. Pause/resume and allow story progression to close the table. Confirm return position, camera, NPC poses/patrol state and ordinary control are restored, and that a dead NPC is not revived/repositioned by cleanup. Assess controller usability separately: X/Y/B shortcuts exist; complete controller-only raise and slider navigation remains a proposed improvement.

## 12. Menu, settings and information contracts

[FoundationHUD](../../Assets/Game/Foundation/Scripts/FoundationHUD.cs) owns exploration title/gameplay overlays; [PrisonHUD](../../Assets/Game/Scripts/UI/PrisonHUD.cs) owns the chapter title and story information. Both use [PrisonPauseMenu](../../Assets/Game/Foundation/Scripts/PrisonPauseMenu.cs) for ten paused sections: **Map, Mission, Inventory, Character, Weapons, Journal, Settings, Save Game, Load Game, Exit to Main Menu**. Sections read current runtime state; chapter weapons do not become free-use equipment because the shared menu contains a Weapons page.

[PrisonMenuTheme](../../Assets/Game/Foundation/Scripts/PrisonMenuTheme.cs) defines the dark/gold visual treatment and menu scaling. [FoundationViewport](../../Assets/Game/Foundation/Scripts/FoundationViewport.cs) uniformly scales gameplay HUD against a 1600×900 reference; menus use their own 1920×1080 reference. The user's supplied cinematic reference is an art target, not evidence of final pixel-level matching. Existing [all-menu documentation](../AllMenuSections.md) records the section concept; current source controls actual availability.

Settings expose windowed/fullscreen, 720p/1080p/1440p/2160p, Low/Medium/High/Ultra, available audio channels, camera sensitivity, inverted Y, subtitles and VSync. Display staging refreshes when entering pause settings so applying after title-screen resolution changes does not reuse an old choice. Resolution is changed only on explicit display apply. Graphics preset changes use the shared [FoundationGraphics](../../Assets/Game/Foundation/Scripts/FoundationGraphics.cs) service and [GraphicsRules](../../Assets/Game/Foundation/Scripts/GraphicsRules.cs); they do not create independent title/story pipeline owners. High/Ultra use full mip detail and native render scale, with higher shadow/LOD settings. This configuration is not a 4K performance benchmark or a guarantee all imported textures become 4K.

Confirmation overlays retain navigation focus for overwrite/load decisions. Unavailable content should show the reason or disabled state. Exit-to-title warns that progress after the latest checkpoint can be lost. Exploration return-to-title reloads the scene to clear stale passenger, ragdoll or poker state; story return uses the director's save/reset routine. Full localization, configurable key bindings and a complete accessibility suite are proposed product work, not verified menu features.

**Unexecuted Unity acceptance — SYS-UI:** inspect each section in both exploration and story; empty/unavailable data must be truthful. Exercise keyboard, mouse and pad navigation and confirmation cancellation. Review at 1280×720, 1920×1080, 2560×1440, 3840×2160 and a non-16:9 window for text fit, scroll access and overlap with minimap, health, objective, inventory, phone and failure overlays. Choose 4K at title, enter gameplay and apply pause settings; actual resolution must stay 4K until explicitly changed. Verify settings persistence and graphics lifecycle across scene reloads; do not infer usability from scaling arithmetic alone.

## 13. Save and load contracts

There are **four slots total**: slot 0 is autosave/latest, and slots **1–3 are three manual slots**. [CheckpointStorage](../../Assets/Game/Scripts/Save/CheckpointStorage.cs) enforces slot range 0–3, writes through a temporary file, retains the prior file as `.bak`, and tries primary then backup when loading. Data is stored under Unity's `Application.persistentDataPath`, separate from the Git repository. A failed write preserves the current session and reports unavailable saving.

| Contract | Exploration | Chapter 01 |
| --- | --- | --- |
| Data | Scene, position/yaw, health, interior/annex flags, equipped item, magazines/reserves, save timestamp | Validated story state, position/yaw, player metadata, health, timestamp |
| Source | [ExplorationSave](../../Assets/Game/Foundation/Scripts/ExplorationSave.cs) | [PrisonSave](../../Assets/Game/Scripts/Save/PrisonSave.cs), [PrisonStoryState](../../Assets/Game/Scripts/Missions/PrisonStoryState.cs) |
| Validation | Matching active scene, finite coordinates, allowed world/interior bounds, health >0 through100, valid equipment/ammunition arrays | Valid progression invariants, finite/bounded positions/yaw, health >0 through100 |
| Restore | Destination floor and standing clearance checked before teleport; correct interior/annex, equipment/ammo and camera restored | Director resets transient state, loads progression, uses stage spawn for special states and resumes appropriate cinematic/sleep sequence |
| Automatic save | Attempts at 30 s unscaled intervals while controllable and safe; no save while paused/activity/water/dead | Periodic source check every10scaled seconds when not busy, plus progression-specific saves; guarded against failed/water/vehicle states |
| Not persisted | NPC health/death, patrol position, vehicle transforms, poker hand/chips and general world state | An arbitrary full-world snapshot or future chapter campaign; normal story actors reset through the director |

Manual exploration saving requires safe grounded normal control ownership; manual story save/load excludes busy/phone activities and unavailable player states. Loading from a title is allowed before the controller's first grounded update, but exploration still checks destination support and blockage. Overwriting or loading a valid existing slot prompts a confirmation. Normal checkpoint load restores saved health; the death/water restart flow explicitly restores 100 after session resume.

**Unexecuted Unity acceptance — SYS-SAVE:** create slot0 and all three manual saves, change location/equipment/ammo/health, then reload and compare the exact intended fields. Verify exploration scene separation, interior and annex restoration, story stage-specific spawn and progression invariants. Test a corrupt primary with valid backup, both invalid, out-of-bounds location, blocked destination and denied file write. Save/load must not revive NPCs through an undocumented world snapshot or claim to resume a poker hand. Restart must not overwrite the good latest checkpoint with failed/water state.

## 14. Sound feedback and verification boundary

[FoundationAudio](../../Assets/Game/Foundation/Scripts/FoundationAudio.cs) loads grouped surface, firearm, impact, punch and handling clips into a spatial voice pool, varies clips without immediate repetition where possible, applies world-layer occlusion/indoor reverb and pauses effects with scaled gameplay. [FoundationFootsteps](../../Assets/Game/Foundation/Scripts/FoundationFootsteps.cs) connects movement/animation contact to surface audio; story dialogue and its audio mix use [PrisonAudio](../../Assets/Game/Scripts/Audio/PrisonAudio.cs). Audio routing may use the optional FMOD bridge when available. Read [audio credits](../ThirdParty_Audio_Credits.md) for source/license provenance.

**Unexecuted Unity acceptance — SYS-AUDIO:** listen to footsteps on each tagged surface, weapon fire/reload/empty, knife/punch contact, story dialogue, table and vehicle contexts. Check pause/focus behavior, indoor/outdoor transitions, occlusion, slider persistence, clipping and repeated sound fatigue. Loading clips or passing source checks is not a listening test.

The editor entry **Alcatraz → Run All Gameplay Checks (Play Mode)** in [LiveSceneVerification](../../Assets/Game/Alcatraz/Editor/LiveSceneVerification.cs) runs temporary fixtures for movement/camera, view recovery, NPC support, combat, swimming, vitals, HUD, graphics and conditional supplied-world travel. It requires entered/resumed gameplay on safe ground, reports failed and skipped suites, and complements a full recorded playthrough. The [offline source-check runner](../../Tools/run_source_checks.py) exercises independent rules and source/assets; it cannot import Unity assets, evaluate rendered poses, compile shaders on the target GPU or certify these acceptance checks.

## 15. Proposed completion work

These items are design proposals requiring implementation and fresh verification; they are not features added by this document:

1. Capture and resolve the reported missing-prisoner defect with Unity evidence in every enabled scene before accepting view reliability.
2. Profile and tune movement/foot contact, authored strafe/swim/combat transitions and camera framing using recorded target-hardware sessions; acquire appropriately licensed animation when needed.
3. Introduce explicit activity/control ownership transitions if regression evidence demonstrates conflicts between the current cooperative flags.
4. Complete controller-only menu/poker operation, key rebinding and accessibility requirements, then verify each screen at target resolutions.
5. Author later missions and a playable escape conclusion. Chapter01 currently ends at an escape agreement; its six-day deadline value is not a finished multi-day campaign simulation.
6. Define and implement broader NPC reactions or policing only as a deliberate future scope change. The accepted water behavior remains alert then restart.
7. Measure real player build size and 1440p/4K performance. A 10GB download is not an acceptance proxy for graphics, asset quality or gameplay completeness.
