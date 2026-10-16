# Offline environment material studies

These images are **offline material studies, not Unity captures**. They show the actual native island chunks, packaged helicopter geometry, original atlas pixels and current surface-profile textures at identical before/after camera positions. Textures retain their original resolution in this study, including the scan's 8K atlas; the existing generic preview helper's 4K texture limit is not used. Pale neutral upward-facing ground selectively blends toward the packaged concrete texture, matching the source shader's mask, distance fade and current replacement strength. The helipad keeps its original dimensions, gains the same perimeter/H paint rectangles authored by the runtime component, and rises to the actual runtime fix's full-footprint clearance level. Before uses the previous nine height probes and .08 m margin; after uses the current 25 by 25 probes at .5 m spacing across the full 12 m deck and .12 m margin. The helicopter moves with the raised landing level, and the camera stays fixed. No new buildings, foliage, terrain detail or character assets were invented for these pictures.

The lighting is a simple GLSL approximation of the current warm key light. Both sides use identical lighting so the material changes remain visible. It does not reproduce URP shadows, sky illumination, baked/global illumination, reflection probes, SSAO, exposure, fog, animation, UI, physics or GPU performance. Native Unity shader compilation and appearance remain unverified. These modest surface changes do not demonstrate the supplied commercial-game reference quality.

- [Helipad before/after](HelipadBeforeAfter.png)
- [Scanned surface before/after](SurfaceBeforeAfter.png)

Reproduce from the repository root with `python Tools/render_environment_quality_preview.py` using `Tools/requirements-supplied.txt`. The tool reads the current `IslandSurface.mat` parameters and actual texture pixels; it does not modify runtime assets.
