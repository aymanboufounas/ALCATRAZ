# Revision 09 source previews

These are Mesa OpenGL renders of the packaged geometry and source textures, **not Unity screenshots or Play Mode captures**. `GameplayLayout.png` is a composited source view of Elias's authored spawn with the new HUD's starter inventory. Runtime camera collision, final URP lighting, weapon/IK alignment and Unity animation playback are unverified.

- `Overview.png`: supplied map, police, gear, dog and weapon thumbnails.
- `Island.png`: the supplied island mesh cropped to its coastline.
- `Characters.png`: supplied police, tactical helmet/vest and dog.
- `Environment.png`: supplied coastal house and Little Bird.
- `GameplayLayout.png`: source geometry and reference-style HUD layout.

The scanned exterior's facades are closed and some surfaces are coarse at close range. The marker loads the existing playable Chapter 01 interior.

To reproduce: install `Tools/requirements-supplied.txt` in the Linux authoring environment with Mesa EGL, then run `python Tools/render_supplied_previews.py`. The original house FBX can be taken from the supplied ZIP under `SourceAssets/Supplied09`, or reconstructed from the packaged house parts. Opening, playing and building in Unity does not require Python.
