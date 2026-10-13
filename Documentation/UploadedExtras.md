# Uploaded asset batch

All 21 requested packs already have native Unity conversions in
`Assets/Game/Supplied/Resources/AlcatrazExtras`. The existing conversions are
reused rather than duplicated. This batch also retains the previous warehouse
and acid barrel, giving 23 catalog entries in total.

## Where to find them

Open the supplied island and select **Workshop & recreation annex** in the
locations menu, or use the dining-hall service door in the cellhouse.

| Uploads | Integration |
| --- | --- |
| Bridge pack, industrial utility building, prison room, prison hallway, guard/watchtower, forest, beach, steel staircase, abandoned store, alchemist workshop | Native scenery placed around the annex |
| Adrian Shephard | Static supplied figure in the annex; not a newly rigged playable character |
| Both poker sets | Playable poker table and decorative poker props |
| Punching/boxing bag | Suspended bag responding to the boxing system |
| Explosive barrel | Solid scenery in the warehouse bay; no explosion simulation is added |
| Machete, M9A3, PMX, PX4, BRX1, “the hardest interview” / Colt M5 | Equipment slots reached with the mouse wheel |

## Verified results

`python Tools/validate_extra_assets.py` validates all 23 catalog entries, native
prefabs, mesh/material/texture dependencies, provenance records and annex or
equipment registration. This command is now included in source-check CI.

The current batch passed with zero errors. Thirteen uploaded ZIPs were retrieved,
verified against their existing SHA-256 records, and checked for ZIP CRC errors.
They match the previously imported sources byte for byte, including the explosive
barrel now uploaded without the older `(1)` filename suffix.

The transfer tool cannot retrieve files larger than 32 MiB. The following eight
new uploads could not be compared directly: abandoned store, industrial utility
building, BRX1, steel staircase, punching bag, beach, forest and watchtower. Their
existing native conversions and dependencies passed validation. This does not
establish that these eight newly attached ZIPs match the older source records.

Full results are in `Validation/UploadedExtrasVerification.json`. A local archive
comparison can be repeated with:

```sh
python Tools/validate_extra_assets.py --archives /path/to/uploads
```

Unity import, visual scale/placement, live interactions, physics and player builds
remain unverified in this cloud machine because the Unity editor is unavailable.
