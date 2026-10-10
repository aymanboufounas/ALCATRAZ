# Revision 09 — supplied asset imports

All nine archives supplied on 10 October 2026 are now packaged as native Unity FBX/OBJ models or glTF 2.0 assets. `Catalog.json` records the original archive SHA-256 hashes. Original source archives stay in the local `SourceAssets` folder; no authorship or new asset license is claimed.

| Upload | Imported resource | Use |
| --- | --- | --- |
| alcatraz.zip | Island | Scanned exterior island, cropped along its coastline in the prepared prefab |
| gun-10mm.zip | Pistol10mm | 10mm pistol with the colored textures from its nested RAR |
| high-poly-pbr-revolvergun.zip | Revolver | Six-round revolver |
| tactical-helmet-with-headset-game-ready.zip | Helmet | Guard head equipment |
| tactical-plate-carrier-vest-game-ready.zip | Vest | Guard chest equipment |
| police.zip | Police | Stationary police model; the OBJ has no skeleton or animation |
| police-dog.zip | Dog | Native rig with all 17 original animation clips |
| helicopters-mh-6-little-bird.zip | Helicopter | Little Bird exterior prop |
| the-house-lost-at-sea.zip | House | Coastal house set piece |

Unity 6000.0.62f1 uses the official `com.unity.cloud.gltfast` package pinned to 6.14.1. The package imports the `.gltf` files directly as native model assets; the game does not download models at runtime. Geometry, skin and animation buffer views are preserved byte for byte. Base color images are resized/compressed for practical import sizes; the island retains an 8192-pixel atlas. Weapon normal maps use normal texture import settings, and metallic/roughness textures are packed into a linear URP metallic/smoothness map.

The house FBX is stored as two byte-exact parts. `SuppliedAssetPreparation` joins and SHA-256 checks them before import. **Alcatraz > Prepare Supplied Assets** prepares all nine native prefabs automatically on editor initialization and before Play Mode/build. Generated assets are reproducible and excluded from Git. The house's source sea, sky, mist and reflection geometry is hidden so it does not cover the island environment. The scanned island includes surrounding water; the prepared mesh removes triangles outside the documented coastline instead of making water walkable.

Asset extraction, buffer integrity and source syntax were checked here. Unity Editor import, shader compilation and Play Mode require validation in Unity; this environment has no Unity Editor.
