# Revision 11 source previews

These images were rendered from the packaged assets and placements in game
revision 0.11.0 (source commit `9835391c373fb610f494a03976533f38b746e7e4`).
They are **offline source previews, not Unity screenshots**. The renderer uses
mesh geometry and base color textures, with approximate daylight. It does not
reproduce URP shadows, ocean shading, normal maps, post processing or game UI.
Static character poses do not verify walking, camera collision or gameplay.

- [Island overview](Island.png): the cropped supplied scan, coastal house and pier.
- [Helicopter starting area](HelicopterStart.png): Elias and the Little Bird at the current spawn.
- [Connected cellhouse](Cellhouse.png): the native prison prefab, furniture and characters.

To reproduce from the repository root:

```sh
python3 -m pip install -r Tools/requirements-supplied.txt
python3 Tools/render_current_previews.py
```

The renderer requires an EGL/OpenGL context. It writes documentation images and
reconstructs the packaged house FBX in the ignored `SourceAssets` directory when
necessary. Game assets remain unchanged. Unity Editor playback is required to
verify the final lighting and gameplay.
