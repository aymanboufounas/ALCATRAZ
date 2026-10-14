# Solitary door and prison toilet uploads

The original supplied door and toilet are placed in a small solitary-cell area at the north end of the workshop/factory annex. Choose **Workshop & recreation annex**, walk north into the factory yard, and continue past the carport towards the north perimeter. The cell centre is annex-relative (12, 0, 138). It also has a marker on the annex pause map.

| Upload | Native model | Source/native triangles | Texture resolution |
| --- | --- | ---: | --- |
| door-of-the-solitary-cell-of-the-prison-14mb.zip | SolitaryDoor | 3,228 / 3,228 | 2048 × 2048 |
| filthy-prison-toilet-4096px2.zip | PrisonToilet | 3,652 / 3,652 | 4096 × 4096 |
| dp3-hw9-prison-room.zip | Existing PrisonRoom | Existing 10,335 | Original images at most 2048 pixels |

The new ZIP for PrisonRoom has exactly the same SHA-256 as its catalogued original: `4d3f8e8aebb5dc367eae9d78fac728fa2c8f9f4e628dafe5ea73e9fe68076f7e`. That room remains at annex-relative (-15, 0, 22); no duplicate room was placed. All three ZIPs are retained byte for byte in SourceArchives.

The two new native conversions keep every triangle, full texture dimensions and lossless PNG output. Their FBX materials omit texture links, so the supplied base colour, normal, metallic and roughness files are bound explicitly. Metallic and inverse roughness are packed into Unity’s metallic/smoothness channels, preserving their dimensions. The supplied incidental `internal_ground_ao_texture.jpeg` is retained in the toilet ZIP but is not treated as a model occlusion map. URP material reconstruction is not an exact recreation of the source application's shader or lighting.

The surrounding cell walls/roof use existing annex construction materials; these are newly constructed geometry, not the uploaded prison-room mesh. The door and toilet face the entrance. The door has an existing DoorController interaction, hinged at its left edge, and a moving box collision proxy. Its detailed visual mesh remains unchanged. The box proxy closes the leaf’s barred aperture for physics purposes. The toilet is static scenery.

The new footprint is approximately 3.8 × 4.7 metres, clear of the forest's imported bounding extent, factory, carport and north wall. The 1.01-metre-wide, 2.1-metre-tall door fits the 1.2 × 2.2-metre opening. The toilet footprint is approximately 0.48 × 0.69 metres and clears the rear wall. Existing annex floor and recovery boundaries cover the cell.

All 29 extras passed catalog, dependency, image, triangle-count, source archive hash and CRC checks in Validation/SolitaryAssetsChecks.json. Native integrity passed across 2,606 files with zero errors, and all 80 C# files passed grammar parsing. The doorway, toilet, terrain and perimeter clearances were checked from source bounds. [Door](SolitaryPreviews/SolitaryDoor.png) and [toilet](SolitaryPreviews/PrisonToilet.png) previews render native geometry/base colour offline; regenerate them with Tools/render_solitary_previews.py. They do not reproduce Unity’s full material response.

Unity import, door interaction, collision sweeps, final rendering and performance remain unverified because the editor is unavailable here.
