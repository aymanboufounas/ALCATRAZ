# Map surface and lighting improvement

This document records the earlier surface/lighting pass and its verification counts. The later [supplied-island geometry rebuild](WorldRebuild.md) now replaces selected runtime visual meshes and adds fitted courtyards/coastal vegetation. Original scan source assets and colliders remain authoritative; the historical pass described below did not replace those visual meshes.

This pass responds to the blurred terrain, stretched walls, flat helipad and sparse environment in the earlier preview. The user's landscape reference is the visual direction: coherent natural light, readable materials and detailed ground. This is an actual runtime/material/geometry change, rather than a generated picture. It does not establish that the current scanned map matches the reference game's fidelity.

## Changes in the project

The supplied scan already has an **8192×8192 atlas**, covering a roughly 600 m wide island. The original material used only that color atlas. Raising its import limit or enlarging the image cannot reconstruct the missing close-range detail or building geometry.

[AlcatrazEnvironmentDetails.cs](../Assets/Game/Alcatraz/Scripts/AlcatrazEnvironmentDetails.cs) now applies one shared runtime detail material to all **11 scan chunks**. The [surface shader](../Assets/Game/Shaders/IslandSurfaceDetail.shader) keeps the original atlas UVs and large features, then projects existing licensed 2K concrete and masonry albedo, normal and packed AO/smoothness maps in world space. Ground and vertical surfaces use separate scales. Detail fades from 45 to 120 m, with distant detail reads skipped. Pale, neutral upward ground also blends toward the real concrete albedo to reduce the blurred scan appearance. The mask preserves vertical features, dark asphalt and strongly colored vegetation; this is a material classification heuristic, not a manually painted terrain layer. Color variation is bounded, and normals/roughness add material response without erasing scanned doors/windows.

The source atlas, scan vertices, UVs, scan colliders and travel anchors remain unchanged. Material replacement uses runtime copies and restores the original materials on teardown. Existing authored Chapter 01/original-island PBR surfaces are retained. All three enabled Alcatraz scenes receive the shared lighting; the scan material/dressing and supplied helipad/dock replacements apply to supplied exploration.

The helipad now uses real concrete albedo/normal/surface inputs, with a painted perimeter and H. The coastal pier and house dock use timber PBR inputs. Textures repeat at approximately metre scale rather than stretching one image over an entire platform. Paint geometry adds no collider. A confirmed scan ridge pierced the old deck by about 7.4 cm: the nine original height probes missed it. The pad now samples its full footprint once at startup and clears the exact clipped source geometry by about 10 cm; its top is about 18 cm higher. The deck retains its existing size/collider, and the helicopter and markings follow the corrected height.

[Ground cover](../Assets/Game/Alcatraz/Resources/Alcatraz/EnvironmentDressing/Manifest.json) adds **458 small tufts in 120 clusters**, partitioned into **39 spatial chunks**, with **23,580 vertices and 7,860 triangles**. It uses strictly selected green scan patches, upward source faces, height/elevated-surface rejection and access margins. Blade bases lie on their source triangles. The additions have **zero colliders** and perform no runtime floor queries. These are conservative placement heuristics; visual inspection is still required. Most of the dry scanned island is not green, so this does not invent a lush grass field across streets and roofs.

Lighting now has a consistent warm afternoon key, cool ambient fill, restrained exposure/bloom and gentle marine haze. The sky uses layered arithmetic-noise clouds and a visible sun aligned with the actual directional light. These clouds are an analytic sky layer, not volumetric ray marching. The scene owns a runtime sky copy and one environment refresh; shared imported sky materials are not mutated during play.

## Verification and reproducibility

The [recorded results](../Validation/EnvironmentQuality.json) separate offline checks from Unity work. The full source runner now contains **25 independent checks**, including the new environment validator. [validate_environment_quality.py](../Tools/validate_environment_quality.py) checks PBR dependencies/import types, deterministic supported placement, source identities, native mesh buffers and geometry budgets. Exact ground-cover regeneration checks all 87 generated files.

Rebuild the additive profiles and ground cover with the existing Python environment:

```bash
python Tools/author_surface_detail_materials.py
python Tools/author_environment_dressing.py
python Tools/author_environment_dressing.py --check
python Tools/validate_environment_quality.py
```

The material author only generates the new detail profiles; source texture bytes and resolution are retained. Input credits remain in [ThirdParty_Art_Credits.md](ThirdParty_Art_Credits.md). Ground cover is original generated geometry with a source/placement manifest.

After pulling main, let Unity import shaders and assets. Enter supplied exploration and run **Alcatraz → Validate Map Surface Detail (Play Mode)**, or **Alcatraz → Run All Gameplay Checks (Play Mode)**. The new fixture checks every scan chunk's original mesh/collision/atlas, material inputs, non-colliding dressing and helipad support. It does not certify image quality. Review all enabled scenes, then walk the exterior, helipad, coastline, interiors and annex at 1440p/4K. Check shadows, wall detail, distant shimmer, visible player, floor support, boat/aircraft access, scene teardown and GPU frame times.

The [offline material studies](EnvironmentQualityPreviews/README.md) show actual source assets and texture inputs using an independent renderer. They are not Unity captures. They do not reproduce URP shadows, GI, shader compilation or performance, and do not prove that a game camera or physics passed.

## Remaining work to reach the reference

The scan's coarse silhouettes, blurred baked building features and uneven ground remain. Material detail cannot reconstruct missing window openings, bevels, roofs, curbs or a professionally authored landscape. The next art work is replacement modular facades and walkable terrain surfaces, consistent prop/vegetation sets, LOD/collision authoring and a lighting/probe pass reviewed in Unity. Existing static police also need rigging/animation work for animated behavior.

Unity API/shader compilation, imported appearance, live gameplay, GPU performance and a player build remain unverified in this cloud environment. This pass is a concrete first improvement across the current map surface and lighting, not a claim of Rockstar-equivalent graphics or a finished high-fidelity world.
