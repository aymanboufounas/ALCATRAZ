# Alcatraz 0.12.0

Open the full project in Unity **6000.0.62f1** and open `Assets/Game/Scenes/SC_AlcatrazSuppliedIsland.unity`. Allow importing to finish, then press Play. Committed native models and all 17 dog clips replace the failing model dependency preparation shown in the screenshot.

The title, exploration pause and story pause menus share a larger navigation panel, dedicated settings and controls pages. Camera and audio preferences persist.

Jumping adds takeoff preparation, reduced air control, rise/fall limb poses and landing recovery. Hard impacts above 10.5 m/s trigger a jointed ragdoll and blended get-up after checking a clear standing location. Sea recovery no longer interrupts every cliff fall. Static native scenery has collision meshes.

- **Helicopter:** E/X boards at the helipad. W/S moves forward/back, A/D yaws, Space/A rises, Ctrl/B descends. Blades rotate while powered. E/X exits after stopping beside safe ground.
- **Boat:** the original patrol boat is beside the coastal house dock. E/X boards, W/S controls throttle, A/D controls rudder. Four-point buoyancy supports the hull. Stop alongside a dock or shore to exit.
- **Boxing:** equip unarmed with 1. LMB/RT cycles timed jab/cross/hook strikes, RMB/LT guards. Stamina limits strikes. E/X beside Tomas starts 45-second sparring. The annex has the supplied suspended punching bag.
- **Poker:** E/X at the supplied annex table starts four-player Texas Hold'em with Samir, Tomas and Luis. Story poker uses the same rules. Blinds are 5/10; stacks are 500 fictional chips per session. Fold, check/call, raise and all-in; play preflop, flop, turn and river. Main/side pots, short all-ins, unmatched bets and split/odd-chip payouts are handled. AI sees its own cards and public cards. P/B leaves and settles the hand.
- **Equipment:** mouse wheel cycles 11 slots, including the supplied machete, M9A3, PX4, PMX, BRX1 and Colt M5. Keys 1–5 retain their mappings; R/Y reloads.
- **New models:** all 20 uploaded archives are converted to native prefabs in `AlcatrazExtras`. Originals are unchanged; SHA-256 provenance is recorded in `Catalog.json`. Large textures/meshes are optimized and static geometry is batched by material. The annex contains the prison room, hallway, watchtower, forest, beach, stairs, store, workshop, Shephard figure, poker sets, punching bag, bridge pack and industrial utility building. Enter through the dining-hall service door or the locations menu; return through the south door.

## Validation

160,041 executable poker/weapon assertions passed under Mono. Native asset references, mesh/weight data, images, C# grammar and the existing island/prison route/support checks pass. CI runs the source checks and executable rule tests.

**Unity is unavailable in this authoring environment.** Unity compilation, Play Mode, ragdoll stability, full swept collision coverage, URP rendering, FPS and Windows builds remain unverified. This download is the Unity source project, not a tested Windows executable.
