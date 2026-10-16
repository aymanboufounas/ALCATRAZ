# Restored original texture detail

Two previously reduced inputs now retain the original texture bytes supplied in the user's archives. This changes real material detail without resizing, AI reconstruction or mesh/collider changes.

| Pack | Previous native image | Restored original |
| --- | --- | --- |
| PokerProps playing cards | 2048 × 915 JPEG | 6500 × 2904 PNG |
| Workshop table | 2048 × 2048 PNG | 4096 × 4096 PNG |

The original archive and PNG SHA-256 values, material bindings, preserved texture GUIDs and unchanged native-file inventory are recorded in each pack's report:

- [PokerProps provenance](../Assets/Game/Supplied/Resources/AlcatrazExtras/PokerProps/QualityRestoration.json)
- [Workshop provenance](../Assets/Game/Supplied/Resources/AlcatrazExtras/Workshop/QualityRestoration.json)

The poker PNG takes over the existing JPEG's GUID, preserving references from existing materials. The reduced JPEG and its old importer are removed. Mip streaming remains enabled, NPOT scaling is disabled, importer caps match the real source sizes and high-quality platform compression remains enabled. Unity import/residency and material appearance still require editor and target-PC review.

Regenerate or verify from the committed original archives:

```bash
python Tools/restore_supplied_texture_detail.py
python Tools/restore_supplied_texture_detail.py --check
```

The check verifies exact source bytes and checksums, importer settings, material references, GUID uniqueness, removed reduced duplicates and **156 unchanged non-target native files**. It reads only the two explicitly named image members; it does not extract or execute archive contents. Original mesh/material/prefab/collision bytes stay unchanged.

The actual texture payload increases by **3,644,790 bytes**. The two original archives outside `Assets` add **45,080,192 source bytes** for reproducibility; those archive bytes do not increase a Unity player. Restored detail and source size are separate from the [5 GB finished-player target](PlayerBuildVerification.md). No installed game size or new player build is claimed.
