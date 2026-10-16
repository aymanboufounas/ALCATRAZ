# Supplied-island geometry rebuild

This pass adds actual replacement façade geometry, closely fitted courtyard surfaces and coastal vegetation to selected parts of the **current supplied island**. It advances the detailed-material pass described in [EnvironmentQuality.md](EnvironmentQuality.md). It does not rebuild the whole map or establish the quality shown in the user's reference image.

## Scope in the project

Two continuous façade faces cover a **105 m² nominal footprint**: a 12 × 3.5 m retaining wall (42 m²) and an exposed 6 × 10.5 m prison-tower face (63 m²) with six recessed window bays. The final façade has **7,764 triangles in seven renderers**. Two visual scan replacements (`Island_0_7` and `Island_0_8`) clip selected old wall fragments while retaining surrounding geometry. The reusable [architecture kit](../Assets/Game/Alcatraz/Resources/Alcatraz/ArchitectureKit/Manifest.json) contains seven modules and **6,018 triangles**; that kit total is separate from the assembled façade. The [façade manifest](../Assets/Game/Alcatraz/Resources/Alcatraz/FacadeRebuild/Manifest.json) records the authoritative patch dimensions, clipping volumes, support measurements and geometry totals.

The projected old-layer area removed, recorded in the manifest, counts scan layers, ledges and both windings; it is a different measure from the nominal footprint. Both faces have **100% coverage at their recorded native-wall support samples**. That confirms backing geometry, not an exact visual/collision match: deep native wall geometry remains sealed behind opaque recessed panes, and source-wall collision stays unchanged. In the offline source preview, the tower's upper four windows are clear while its two lowest windows remain partly behind distorted original foreground geometry. The replacement wall continues down to the existing terrain. These windows do not create enterable rooms.

The [courtyard bake](../Assets/Game/Alcatraz/Resources/Alcatraz/CourtyardSurfaces/Manifest.json) skins **826.4822 m² of original surface triangles**: approximately 747.57 m² near arrival and the helipad, plus 78.91 m² near the upper cellhouse gate. These totals measure sloped source triangles rather than a unique flat footprint. The courts are independent floors at approximately 31 m and 49 m elevation. Every surface polygon follows its original upward source triangle; no flat plaza connects the two heights. Full existing CC0 2K concrete albedo, normal and packed AO/smoothness maps repeat every 2 m. Thin expansion joints remain on those same supported polygons. The **1,108 triangles** sit at most **0.006603 m** from their authoritative source faces, below the 0.01 m limit. The authored courts are repaved continuously: source colors do not leave arbitrary square gaps. Actual missing/steep source faces, region boundaries and continuous architecture-wall setbacks remain excluded, along with the helipad footprint plus 0.35 m.

The [coastal vegetation bake](../Assets/Game/Alcatraz/Resources/Alcatraz/CoastalVegetation/Manifest.json) adds **8 trees and 36 shrubs in 25 spatial chunks**. Branched trunks and leaf/needle geometry use original generated textures and two native geometry LODs: **45,136 triangles at LOD0** and **16,296 at LOD1**, with 61,432 stored triangles across both levels. Supported source-green anchors and access margins constrain placement. Foliage uses cutout textures and needs GPU profiling; the pass does not add dynamic wind.

The [runtime component](../Assets/Game/Alcatraz/Scripts/AlcatrazEnvironmentDetails.cs) loads these resources only when the supplied island is present. It resolves the complete façade replacement set before changing scan `MeshFilter` references. Original mesh and material references are restored on teardown. Original source mesh files, scan `MeshCollider` references, mission/travel anchors and existing gameplay collision remain authoritative. All new façade, courtyard and vegetation geometry adds **zero colliders**. The separate authored story/original-island scenes do not receive this supplied-world reconstruction.

## Reproduction and evidence

Run the deterministic author checks with the repository's Python dependencies installed:

```bash
python Tools/author_prison_architecture.py --check
python Tools/author_facade_rebuild.py --check
python Tools/author_courtyard_surfaces.py --check
python Tools/author_coastal_vegetation.py --check
```

Remove `--check` to regenerate an owned bake after intentional source changes. The manifests retain source identities, placement rules, geometry totals and limitations. Texture credits remain in [ThirdParty_Art_Credits.md](ThirdParty_Art_Credits.md). Prior verification counts in [EnvironmentQuality.md](EnvironmentQuality.md) describe that earlier pass and are preserved as historical evidence.

The [source validation report](../Validation/WorldRebuildSource.json) and [verification record](../Validation/WorldRebuild.json) distinguish executable offline checks from unexecuted Unity work.

The [offline before/after comparisons](WorldRebuildPreviews/README.md) show the arrival court, exposed tower façade and coastal planting using repository geometry outside Unity. They cannot establish URP appearance, camera behavior, collision, frame rate or player-build quality. No Unity Editor was available for this pass. There is no verified 1440p/4K performance result, complete-island reconstruction, reference-quality parity or new playable build.

## Unity verification still required

After import, enter supplied exploration and run **Alcatraz → Validate Map Surface Detail (Play Mode)** and **Alcatraz → Run All Gameplay Checks (Play Mode)**. Walk the arrival court, complete helipad perimeter, retaining wall and upper gate. Inspect façade seams/recesses from both sides, source-wall collision, camera clearance, courtyard depth fighting, vegetation roots, LOD transitions and access to NPCs/vehicles. Reload the scene to verify restoration and compare the separate story scene for unintended changes. Capture actual gameplay images and GPU frame times at the chosen resolution before judging visual quality or performance.

The remaining coarse scan buildings, roofs, terrain silhouettes and unselected walls still need reconstruction. Resolve foreground scan occlusion and review the new façade's visual/collision offset in Unity before treating it as finished architecture. Lighting/probe review, vegetation density, texture repetition and foliage overdraw also require assessment before expanding this treatment across the island.
