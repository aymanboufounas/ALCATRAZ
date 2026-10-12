# Alcatraz 0.12.1 — warehouse and barrels

The abandoned warehouse interior, acid barrel and explosive barrel uploads bring the native extras catalog to 23 packs. Original archives are unchanged; each source record records its SHA-256 hash.

In the locations menu select **Workshop & recreation annex**. Walk east through the eight-metre opening to the warehouse bay. Press **E / X** beside either west-side door to enter and again beside a door to leave. Both destinations require floor support and clear standing space. Two yellow and two red barrel models stand outside as static solid scenery.

The bay has overlapping floor support, perimeter walls and updated recovery bounds. Native collision meshes cover structural surfaces and barrel bodies. Cutout cardboard and graffiti do not obstruct the player.

Old Cycles bake graphs become standard textured materials. Hidden particle templates and HDR scenery are excluded. The authored floor mesh is preserved to maintain its baked UVs. Supplied `poutres-main.png` substitutes for three unavailable beam-bake variants, as recorded in the source record. Opaque colors use optimized JPEGs; transparency stays in PNGs. Warehouse mesh chunks contain at most 5,000 triangles.

`python Tools/validate_warehouse.py` checks native meshes, catalog records, dimensions, separation, floor UV alignment, both entry points, foot support and conservative standing clearance. Add `--archives /path/to/uploads` to verify archive hashes. CI runs this with existing source/asset and poker/weapon checks.

Previews render native geometry offline and are not Unity screenshots. Unity compilation, Play Mode, live door interactions, swept collisions and a Windows build remain unverified because the Editor is unavailable here.
