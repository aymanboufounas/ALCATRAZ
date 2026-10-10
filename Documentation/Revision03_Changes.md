# Revision 03 — realistic art direction and coastal prison map

This update moves the existing Unity prison prototype toward a more grounded visual style. It does **not** reproduce Red Dead Redemption 2's graphical quality, open world, engine or character animation system.

- The assembled procedural faces and hands were replaced with adapted MakeHuman anatomy, including real facial loops, eyelids, ears, nose, lips and fingers. The imported skin atlases and normal maps are 2K. Heavy, lean, athletic and different skin-tone profiles remain. The lower neck is fitted inside the shirt, tapered forearms meet the hands with blended wrist weights and matching atlas colors, and cloth folds fade at the waistband to avoid overlapping seams. The 23-bone rig and existing gait/interaction system are retained; fingers are not articulated.
- Six scanned surface sets provide diffuse color, normal relief, roughness and occlusion. Brick orientation and box UV scale are corrected in metres. Collider size/centres and child transforms are preserved when box dimensions are baked into the meshes.
- The former ellipsoid island backdrop is replaced by a coastal terrain mesh, rock outcrops, procedural trees and groundcover. An accessible eastern service courtyard adds laundry/workshop exteriors, carts, crates, lamps and directional signs. The administration facade, prison roof, chimneys, coping and buttresses add silhouettes and landmarks.
- A clouded sky shader, animated water normal/specular/shore-foam shading, subdued ambient fill, warmer grading and larger shadow atlases improve the lighting setup. Water/sky effects require URP; shader compilation has not been run here.
- The original mission sequence, five walking NPC routes, six seated actors, poker, optional dialogue table, 68 voices, knife/phone/tattoo logic, one-minute isolation and escape agreement remain. This update does not add the subsequent escape mission. New building exteriors are scenery and have no playable interiors.

## Open

Extract the full archive and open `DesertShift` in Unity **6000.0.62f1**. Choose **Blackstone > Open Chapter 01**, press Play and choose **New game — Chapter 01**. Existing compatible checkpoints remain available. The one-time rendering repair uses a new revision key so it runs on this update.

## Verification limits

Offline checks inspect native mesh data, asset references, source code with temporary Unity stubs, mission/poker logic, texture/audio bytes, physical collider dimensions and coarse navigation. None of those certify Unity import, shader compilation, live character skinning, collisions, input, audio, final lighting or performance.

The nine images in `BlackstonePreviews` are labelled geometry/material previews rendered outside Unity. They approximate materials/lighting; they do not execute the new Unity sky/water shaders or gameplay. Unity Editor was unavailable, so Play Mode and a Windows executable build still need the supplied checklist.

## Authoring

`Tools/build_blackstone.py` rebuilds the native chapter using `realistic_characters.py`, `coastal_art.py` and the included `ArtSources`. Python, NumPy, SciPy and Pillow are required for this optional authoring step. No Python or network access is needed to play the imported Unity project. Source credits are in `ThirdParty_Art_Credits.md`.
