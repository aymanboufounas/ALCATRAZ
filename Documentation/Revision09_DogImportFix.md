# Dog import repair

The supplied-island setup stopped with `Model has not imported: .../Dog/Dog.gltf` when Unity did not produce the dog prefab. This message alone does not identify the underlying glTFast import error.

The source export is valid glTF but carries 838 skin joints, 1,152 nodes and 42,687 animation channels. Only 200 joints have nonzero skin weights. The packaged dog now has 200 skin joints, 344 nodes and 17,289 channels, reducing its JSON from 9.9 MB to 4.0 MB. This reduces the imported rig and curve count while retaining all 17 clips.

`Tools/prepare_dog_import.py` preserves every weighted joint's complete ancestor chain, the mesh nodes and scene roots. It checks the positions, normals, UVs, weights, triangle indices, retained animation inputs/outputs and inverse bind matrices against the previous source. It remaps joint indices; it removes only branches and animation channels that cannot affect the visible skinned meshes. Original archive hashes remain in the catalog. Archive reimport runs this compaction automatically.

Source equivalence and repeatability checks passed. The official Khronos glTF Validator reports zero errors on both exports. Unity Editor import and Play Mode still require checking on a machine with Unity 6000.0.62f1; source checks do not establish successful Unity import.

## Recover the Unity import

1. Close Unity and extract the updated repository ZIP into a new folder, or update an existing Git checkout. Open the project with Unity 6000.0.62f1 and let Package Manager finish restoring packages.
2. Choose **Alcatraz > Repair Supplied Imports**. This checks every external glTF dependency, imports buffers/textures before models, restores Legacy animation settings and forces a synchronous reimport. It then rebuilds all nine prepared prefabs.
3. Choose **Alcatraz > Open Island**, then press Play. The dog should have idle/walk/bark clips available through the existing patrol.

Ordinary preparation also retries a missing or incomplete imported model once. If the retry fails, the Console message includes glTFast's import report errors when available, or identifies missing files, incomplete buffers or an unavailable importer. Preparation verifies all nine prefab outputs and their source dependency hashes before accepting its cache, and checks every source before replacing generated assets. A supplied-model failure no longer cancels Play Mode in the separate chapter or original island scenes.

If Unity still refuses the dog import, select `Dog.gltf` in Project and inspect its import report alongside the first Console error. The screenshot's previous generic message cannot distinguish an importer failure from an incomplete project download.
