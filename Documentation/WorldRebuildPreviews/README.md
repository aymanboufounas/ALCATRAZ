# Actual source geometry: offline comparison

These are **offline source-asset renders, not Unity captures or AI concept art**.
Both sides use identical cameras, material decoding, key light, shadow method,
exposure and the current helipad height. Before includes the ff62e76 world-scale
surface profiles and existing ground cover. After replaces exactly the scan
mesh resources listed by FacadeRebuild/Runtime.json before applying the source
island world offset, then adds the current world-space facade, courtyard and
vegetation prefabs. Only LOD0 vegetation is drawn; duplicate LOD1 meshes are omitted.

The unchanged packaged helicopter is rendered from its native baked prefab and
placed with the same runtime height/yaw/grounding rule. No models, sky artwork,
buildings or plant instances are invented for the images. Source textures retain
their original dimensions, including the island's 8192×8192 atlas. Native PBR
normal/AO/smoothness maps and fixed directional geometry shadows are approximated
by this study's GLSL shader. The flat background is a clear color, not a sky asset.

- [Arrival court before/after](ArrivalCourtBeforeAfter.png)
- [Exposed prison tower before/after](PrisonWindowsBeforeAfter.png)
- [Whole tower block before/after](TowerBlockBeforeAfter.png)
- [Coastal planting before/after](CoastalPlantingBeforeAfter.png)
- [Arrival court after](ArrivalCourtAfter.png)
- [Exposed prison tower after](PrisonWindowsAfter.png)
- [Whole tower block after](TowerBlockAfter.png)
- [Coastal planting after](CoastalPlantingAfter.png)
- [Inputs, dimensions and camera/light metadata](Manifest.json)

The tower comparison includes the actual surveyed shell, closed roof, coping and
metal flashing from the current native resources. The whole-block view uses one
fixed three-quarter camera to show the old scan and repaired structure with the
same neighboring geometry. The roof is visual source geometry in this renderer;
the separately authored runtime support collider is not executed here.

Only explicitly surveyed building regions are replaced. Much of the scanned
island still has coarse silhouettes, inconsistent baked detail and sparse
vegetation. On the 6 × 10.5 m tower face, the upper four windows are clear while
the two lowest windows remain partly behind unchanged foreground scan geometry.
The replacement wall continues down to the existing terrain; no foreground ridge
was removed or hidden to expose it. These comparisons show local progress, not the requested commercial
reference quality across the full map. The offline renderer does not execute URP,
the custom Unity shaders, ocean rendering, reflection probes, SSAO, baked/global
illumination, Unity sky/exposure/fog, physics, animation or gameplay UI. The coast
view therefore shows the cropped scan edge against the clear background; this
does not show how the runtime ocean covers that edge. Native shader/API
compilation, Unity appearance and target-PC performance remain unverified.

Reproduce with `python Tools/render_world_rebuild_preview.py` after installing
`Tools/requirements-supplied.txt`. The tool reads runtime assets and writes only
this documentation directory.
