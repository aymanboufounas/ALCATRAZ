# Supplied-island geometry rebuild

This pass adds actual replacement façade geometry, closely fitted courtyard surfaces and coastal vegetation to selected parts of the **current supplied island**. It advances the detailed-material pass described in [EnvironmentQuality.md](EnvironmentQuality.md). It does not rebuild the whole map or establish the quality shown in the user's reference image.

## Scope in the project

The rebuilt exterior now follows the exposed tower's south, east and north faces, with a short west return into its attached wing. Including the existing retaining wall and solid upper bands, the five wall sections have **358.965 m² of nominal face area**, **24 recessed windows**, and a closed **6 × 13.2 m roof**. The assembled walls/roof have **28,880 triangles in 24 renderers**. Three visual scan replacements (`Island_0_5`, `Island_0_7` and `Island_0_8`) clip selected old fragments while retaining surrounding geometry. The reusable [architecture kit](../Assets/Game/Alcatraz/Resources/Alcatraz/ArchitectureKit/Manifest.json) contains ten modules and **7,014 triangles**; that kit total is separate from the assembled building. The [façade manifest](../Assets/Game/Alcatraz/Resources/Alcatraz/FacadeRebuild/Manifest.json) records authoritative dimensions, clipping volumes, roof geometry, support measurements and totals.

Projected old-layer removal counts scan layers, ledges and both windings; it is separate from nominal face area. Source-wall support and actual window-pane samples are recorded per face. Adaptive-width bays preserve fixed-size glass, frames and bars; unsupported bay samples receive solid wall rather than an unsupported window. Source-wall collision stays unchanged, so visual planes do not exactly match every old projection. Some lower windows still sit partly behind original foreground geometry. These windows do not create enterable rooms.

The former roof center hit original floors roughly 4.66–8.81 m below the new roof. A closed beveled slab, membrane, seams, coping and flashing now meet at **Y59.8 m**. Exactly **one new static roof BoxCollider** matches the measured 6 × 0.2 × 13.2 m support volume. The membrane and collider top agree within native float precision; original floors, source colliders and higher chimney/ruin features remain intact. A narrow elevated corner volume removes the confirmed old scan wedge, with outside fragments preserved. Its old collider projection remains, so helicopter clearance and close camera/physics behavior still need Unity review.

The [courtyard bake](../Assets/Game/Alcatraz/Resources/Alcatraz/CourtyardSurfaces/Manifest.json) skins **826.4822 m² of original surface triangles**: approximately 747.57 m² near arrival and the helipad, plus 78.91 m² near the upper cellhouse gate. These totals measure sloped source triangles rather than a unique flat footprint. The courts are independent floors at approximately 31 m and 49 m elevation. Every surface polygon follows its original upward source triangle; no flat plaza connects the two heights. Full existing CC0 2K concrete albedo, normal and packed AO/smoothness maps repeat every 2 m. Thin expansion joints remain on those same supported polygons. The **1,108 triangles** sit at most **0.006603 m** from their authoritative source faces, below the 0.01 m limit. The authored courts are repaved continuously: source colors do not leave arbitrary square gaps. Actual missing/steep source faces, region boundaries and continuous architecture-wall setbacks remain excluded, along with the helipad footprint plus 0.35 m.

The [coastal vegetation bake](../Assets/Game/Alcatraz/Resources/Alcatraz/CoastalVegetation/Manifest.json) adds **8 trees and 36 shrubs in 25 spatial chunks**. Branched trunks and leaf/needle geometry use original generated textures and two native geometry LODs: **45,136 triangles at LOD0** and **16,296 at LOD1**, with 61,432 stored triangles across both levels. Supported source-green anchors and access margins constrain placement. Foliage uses cutout textures and needs GPU profiling; the pass does not add dynamic wind.

The [runtime component](../Assets/Game/Alcatraz/Scripts/AlcatrazEnvironmentDetails.cs) loads these resources only when the supplied island is present. It validates the full visual replacement set and finite roof metadata before changing scan `MeshFilter` references. All native dressing prefabs remain collider-free; the component installs only the intentional roof box, enabling it after visual swaps. Original mesh/material references are restored and the added roof collider is disabled on teardown. Original source mesh files, scan `MeshCollider` references and mission/travel anchors remain unchanged. The separate authored story/original-island scenes do not receive this supplied-world reconstruction.

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

The [offline before/after comparisons](WorldRebuildPreviews/README.md) show the arrival court, front façade, whole tower block and coastal planting using repository geometry outside Unity. They cannot establish URP appearance, camera behavior, collision, frame rate or player-build quality. No Unity Editor was available. There is no verified 1440p/4K performance result, complete-island reconstruction, reference-quality parity or new playable build. The [finished-player verification guide](PlayerBuildVerification.md) describes the requested 5 GB installed-player target and its separate build/launch requirements.

## Unity verification still required

After import, enter supplied exploration and run **Alcatraz → Validate Map Surface Detail (Play Mode)** and **Alcatraz → Run All Gameplay Checks (Play Mode)**. Walk the arrival court, complete helipad perimeter, retaining wall and upper gate. Inspect the whole tower from all sides, its roof/landing support, wall/corner collision and camera clearance, courtyard depth fighting, vegetation roots, LOD transitions and access to NPCs/vehicles. Reload the scene to verify restoration and compare the separate story scene for unintended changes. Capture actual gameplay images and GPU frame times at the chosen resolution before judging visual quality or performance.

The remaining coarse scan buildings, roofs, terrain silhouettes and unselected walls still need reconstruction. Resolve foreground scan occlusion and review the new façade's visual/collision offset in Unity before treating it as finished architecture. Lighting/probe review, vegetation density, texture repetition and foliage overdraw also require assessment before expanding this treatment across the island.
