# Alcatraz map adaptation

This is original authored geometry using the island's recognizable outline and landmark relationships. It is a game adaptation, not a surveyed reconstruction. The contemporary gang/phone/kidnapping story uses Alcatraz as a fictional active prison.

## References

- [National Park Service map](https://www.nps.gov/goga/planyourvisit/upload/Alcatraz-map-Access-508.pdf): summit cellhouse, west yard/water tower, north industries, east landing and south lighthouse/parade areas.
- [User's Unity WIP reference](https://discussions.unity.com/t/alcatraz-breakout-concept-wip/606269): visual direction only. The author's source, models and screenshots are not included.
- [NPS: The New Prison](https://www.nps.gov/places/the-new-prison-seven-prisons.htm): cellhouse reference. Our cell numbering, isolation and administration rooms are adapted for gameplay.
- [Suggested Sketchfab listing](https://sketchfab.com/3d-models/alcatraz-cb2c47cd3aea4074a14bffe69f46b313): no authenticated source download/license attachment was obtained, so this project contains our authored map instead. Paid Modular Prison Pack and ArtStation assets are not purchased/bundled.

## Native implementation

Tools/build_alcatraz.py creates native Unity meshes, materials and scenes. AlcatrazLayout.json records roads, landmarks, cells and mission anchors in metres, Y up and north +Z. Ground level is around 30 m at the cellhouse, 27.28 m at the yard and 5 m at the east dock. Original geometry uses existing licensed scanned surfaces.

SC_AlcatrazIsland and SC_AlcatrazChapter01 replace the older architecture in the default scenes. The classic scene remains unchanged. The existing 22 actors, tables, props, dialogue/mission bindings and cinematic controls are retained and repositioned.

Four runtime scripts receive map integrations: the director's scripted placements, checkpoint bounds/identity, chapter HUD and interior ambience. The foundation HUD selects the Alcatraz title/chapter through serialized fields. AlcatrazMap supplies navigation and water recovery. AlcatrazPreparation opens/prepares scenes and provides a Windows build entry point.

Locomotion controllers are generated inside Unity after FBX import; imported subasset identifiers are not guessed in the source package. The original mission/poker/weapon pure rules, voice recordings, character models and walking clips remain included.

## Verification

Revision 06 checks native references, hashes, road grades/stair rises, sampled stationary obstacles and native collider floor support. Operable doors are assumed open on exit routes; dynamic NPC avoidance and swept controller physics need Play Mode.

Tools/render_alcatraz_preview.py renders the actual authored meshes, materials and rigged skins with Mesa/OpenGL. Lighting, shadows and water differ from Unity. Images are source previews, not gameplay captures.

Earlier reports describe earlier snapshots. Current reports are Revision06_AlcatrazChecks.json, Revision06_SyntaxChecks.json, Revision06_LogicChecks.json, Revision06_PackageManifest.json and the refreshed OfflineValidation.json.

Unity import, Play Mode, player compilation, runtime IK/camera/audio, URP shaders and performance have not run here. This is a source prototype.
