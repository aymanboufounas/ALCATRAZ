# Revision 03 art sources

The game uses adapted **CC0** art from the following sources. Story text, gangs, signs, gameplay, generated clothing, vegetation and prison layout remain original. No Rockstar or Red Dead Redemption assets are included.

## MakeHuman

The MakeHuman Community base mesh and bundled caucasian/african/asian male-young target assets are distributed under CC0. Only head, neck and hand regions enter the clothed runtime characters; helper and anatomical body geometry do not enter the gameplay meshes. Geometry was morphed, cropped, retargeted to the existing 23-bone rig, smoothed and converted to native Unity meshes. Fingers share a hand bone and are not individually animated.

- [MakeHuman asset license](https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.ASSETS.md), also included at `Tools/ArtSources/mh_license.md`.
- [Base mesh](https://github.com/makehumancommunity/makehuman/blob/master/makehuman/data/3dobjs/base.obj).
- [Natural male CC0 skin pack](https://static.makehumancommunity.org/assets/assetpacks/skins02.html).
- **Mindfront**: Aksel skin diffuse/normal and African middle-age skin diffuse/normal.
- **Margaret Toigo**: young male bronze skin, used with color variants for tan/olive skin.
- The source pack also supplied freckles and mature skin references by Margaret Toigo and **jartur69**, retained in the authoring source directory. Those references are not selected by the current runtime materials.

Skin maps were resized to 2K. Facial/hand UVs follow the source atlas, with profile-specific geometry variations, tint, scalp surfaces and separate eyes. The MakeHuman application, its code and its executable are not redistributed.

## Poly Haven — Powered by Poly Haven

The following scanned surface assets are CC0. Their 2K diffuse, OpenGL normal, roughness and ambient-occlusion textures were downloaded, verified against the published MD5 values and converted to PNG/native URP materials. Roughness was inverted into the smoothness alpha channel; AO was packed into green. No live API calls occur during gameplay.

| Asset | Current use |
| --- | --- |
| [Brushed concrete](https://polyhaven.com/a/brushed_concrete) | Concrete/plaster/painted prison walls |
| [Concrete floor worn 001](https://polyhaven.com/a/concrete_floor_worn_001) | Interior floors, yard and service court |
| [Brick wall 001](https://polyhaven.com/a/brick_wall_001) | Laundry/workshop/admin exteriors and buttresses |
| [Seaside rock](https://polyhaven.com/a/seaside_rock) | Coastal outcrops, coping and foundations |
| [Wood planks](https://polyhaven.com/a/wood_planks) | Furniture, crates, doors and bark reference |
| [Forest floor](https://polyhaven.com/a/forest_floor) | Coastal earth |

Original asset URLs and published checksums are retained in `Tools/ArtSources/download-provenance.json`. The API was used during authoring with the required credit above. See [Poly Haven API information](https://polyhaven.com/our-api) and [CC0 information](https://polyhaven.com/license).
