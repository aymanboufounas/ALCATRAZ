# Revision 09 — playable supplied island exterior

**Alcatraz > Open Island** now opens `SC_AlcatrazSuppliedIsland`, which is the first enabled build scene. It loads the supplied scanned island at the documented transform, with an ocean surface, a matching minimap and native mesh collision. The original exploration scene and Chapter 01 interior remain available from the Alcatraz menu and are included in Windows builds.

Elias spawns on the road beside the cellhouse. Walk to its marked entrance and press **E / X** to play Chapter 01. The supplied scan has closed roofs, so its facade is an exterior; the doorway opens the existing playable chapter scene. The pause menu also opens Chapter 01.

The new exterior includes the uploaded stationary police model with the tactical helmet and plate carrier, an animated dog walking between two points beside the entrance and barking when approached, the Little Bird parked on its dock landing deck, and the house on a coastal platform reached by a sloped service pier. Water falls return Elias to his last grounded location. The police OBJ has no rig and is deliberately stationary. The helicopter is a parked prop, rather than a flight system.

`Tools/create_supplied_scene.py` writes the compact native scene. `Tools/validate_supplied_assets.py` checks source dependencies, house reconstruction, internal scene references and sampled triangle support beneath the actual spawn/prop/dog positions. The cropped island retains 205,423 triangles; the rest of the scan's surrounding water is removed from the prepared render and collision mesh. Dog route samples avoid abrupt floor changes.

These are source and static geometry checks. Unity Editor import, Play Mode collisions, the dog clip playback and final lighting still need checking in Unity 6000.0.62f1. No Unity Editor is available in the authoring environment.
