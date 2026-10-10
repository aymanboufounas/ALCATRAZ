# Revision 08 — approved concept implementation

The user approved the Alcatraz island and character board on 9 October 2026 and requested implementation and publication to aymanboufounas/ALCATRAZ.

The reference video guides the narrow rocky island, central prison ridge, northern industry, western yard and water tower, southern lighthouse and waterfront buildings. This remains an original game adaptation. No Sketchfab scan, third-party island mesh or commercial-game assets are included.

The existing two Alcatraz scenes were regenerated with a carved coastal service trail, fractured pale shoreline strata, coastal scrub, facade trims, blue-gray water tank and pale waterfront barracks. The new trail connects the Agave trail to the existing western road. It has a native MeshCollider and stone parapets. Decorative shrubs and garden stones are excluded from building footprints and path corridors.

`AlcatrazPresentation` configures a resource-backed marine sky, atmospheric lighting, ACES grading, subtle bloom and anti-aliasing when either Alcatraz scene starts. The bay water uses animated normals, Fresnel sky color, sun highlights and camera depth to shade shallows and foam around actual geometry. The shader has no circular island foam mask. These rendering changes need verification in Unity.

Elias's new head albedo uses the existing Rocketbox UV atlas as an edit target. His head material and faded orange body material are assigned only to the player. Other inmates keep their existing shared assets. Officer Harrow has a new graying head albedo and a matte navy uniform material on his distinct existing model. The new face is a texture adaptation on the original mesh, not a bespoke sculpt matching the portrait. All 30 identities and their walking/seated routines remain.

The chapter, checkpoint identity, interactions, poker, dialogues, footsteps and weapon practice are retained. The story still ends at the escape agreement; later escape missions are not added in this revision.

## Visual evidence

- `ApprovedConcept/Alcatraz_MapCharacters.png` is AI-generated concept art, not a Unity capture.
- `AlcatrazPreviews/A01_Island.png`, `A14_Officer.png`, `A15_CoastalPath.png` and `A16_PrisonerPortrait.png` are current Mesa renders of shipped source geometry and textures, not Unity gameplay.
- Other numbered source previews and earlier reports are historical unless regenerated for this revision.

## Validation

See `Validation/Revision08_AlcatrazChecks.json`, `Revision08_SyntaxChecks.json` and `OfflineValidation.json`. Source checks inspect native bindings, route obstacles, floor support, image/audio integrity and C# grammar. They do not compile C# against Unity assemblies or compile shaders. The Editor is not available in the authoring environment. Unity import, Play Mode, lighting, physics, UV appearance, camera depth, frame rate and Windows build are unverified. Follow the current Play Mode checklist before distributing a player build.

## Assets and reproducibility

The approved board and generated texture prompts are documented in `Revision08_GeneratedAssets.md`. Existing Rocketbox MIT and Poly Haven notices remain in `Licenses/` and the Revision 05 credits. New geometry and shader code are authored for this project. Generated textures are integrated into native materials.

Unity source does not require Python. To regenerate or inspect offline, install `Tools/requirements.txt`. Compressed authoring inventories are included; the Blackstone gzip archive is byte-partitioned into three files and joined automatically by `authoring_io.py`. Large Alcatraz render batches use smaller native meshes preserving the same triangle attributes. This accommodates the publishing connection's 16 MiB request limit. `build_alcatraz.py` and `render_alcatraz_preview.py` read the compressed inventories when raw JSON is absent. See the archive checksum and `Validation/Revision08_BatchPartitionChecks.json` for integrity evidence.

Unity reference: [URP 17 depth texture access](https://docs.unity.cn/Packages/com.unity.render-pipelines.universal%4017.0/manual/writing-shaders-urp-reconstruct-world-position.html).
