# Alcatraz map and characters — Revision 07

This continues the Revision 06 project. It is a source prototype for Unity 6000.0.62f1 with URP, not a finished game or executable.

## Map work

The cellhouse keeps its existing footprint, cells, galleries, mission anchors and routes. Sixteen skylights now have real openings through both the roof and raised curbs. Transparent glass renderers do not cast solid shadows. The reference direction remains the [NPS Alcatraz map](https://www.nps.gov/goga/planyourvisit/upload/Alcatraz-map-Access-508.pdf); new interior details are original gameplay adaptations.

Added rooms and props are authored as native Unity geometry:

- Cellhouse electrical conduits, junction boxes, beams, routine board and B-04 identity sign.
- Dining trays, bowls, cups, kitchen cabinets, serving grilles and waste stations.
- Shower valves, drain grilles, changing benches and folded towels.
- Six industry workstations with original machine geometry, stools and laundry bins.
- Storehouse shelving with supply crates and a clear central loading aisle.
- A small recreation court and basketball ring, plus dock benches, rope coils and directions.

Large props have collision. Small fittings are grouped by material. Rendering, light budgets and performance must be profiled in Unity.

## Character work

The original five Rocketbox models and their rigs/animation clips are retained. The roster supplies 30 actor identities using those five models, with individual height, build, speed and idle phase. These are variants, not 30 unique sculpted faces.

Elias has a plain orange inmate outfit with B-04 identification. Harrow has a navy uniform and badge. These are 1254 × 1254 imagegen-edited diffuse atlases; inspect their seams in Unity. Source textures remain packaged, and all MIT notices are retained. The full prompts and paths are in Revision07_TexturePrompts.md.

Eight native ambient actors extend the original 22:

| Actor | Area | Routine |
| --- | --- | --- |
| Officer Mercer | Broadway | Corridor patrol |
| Officer Shaw | Landing | Dock patrol |
| Laundry orderly | New Industries | Centre aisle walk |
| Dining orderly | Dining hall | Table aisle walk |
| Workshop machinist | New Industries | Stationary at bench |
| Laundry attendant | New Industries | Stationary at bench |
| Storekeeper | Storehouse | Loading aisle walk |
| Dock orderly | Wharf | Stationary |

Ambient routines run in both Alcatraz scenes. Existing mission actors keep story control. Walkers check supporting floors and stop for nearby people; this is local route following, not a full NavMesh crowd simulation. Stationary workers use the existing idle animation, not new machine-operation clips. Idle phase offsets and small head glances reduce synchronized movement.

## Implementation and checks

- Tools/build_alcatraz.py plus Tools/alcatraz_detail_pass.py rebuild the native map and both scenes.
- Assets/Game/Alcatraz/Resources/Alcatraz/CharacterRoster.json is shared by native actor authoring, runtime appearance selection and source previews.
- FoundationBootstrap binds profiles and preserves mission ownership. FoundationAgent rejects movement without a supported floor and respects suspended/talking state.
- Tools/fbx_pose.py corrects FBX handedness in offline previews; Unity continues to use its own FBX importer.
- Revision07_AlcatrazChecks.json checks native scene bindings, actor routes, supported floors and protected assets.
- Revision07_SyntaxChecks.json checks C# grammar only. OfflineValidation.json checks native asset integrity.

Unity compilation/import, Play Mode, player physics, actual URP lighting, live NPC avoidance and Windows builds were not run. Historical Revision 04–06 reports describe earlier snapshots. The current story still ends at the escape agreement. Preview images are offline renders of the shipped source geometry, not Unity screenshots or gameplay.

Unity API references used: [Animator.Play](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Animator.Play.html), [Physics.Raycast](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Physics.Raycast.html), [axis conversion](https://docs.unity.com/ja-jp/engine/6000.0/script-reference/unityeditor/modelimporter/bakeaxisconversion).
