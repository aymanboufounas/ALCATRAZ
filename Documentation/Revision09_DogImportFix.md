# Dog import repair

The supplied-island setup stopped with `Model has not imported: .../Dog/Dog.gltf` when Unity did not produce the dog prefab. This message alone does not identify the underlying glTFast import error.

The source export is valid glTF but carries 838 skin joints, 1,152 nodes and 42,687 animation channels. Only 200 joints have nonzero skin weights. The packaged dog now has 200 skin joints, 344 nodes and 17,289 channels, reducing its JSON from 9.9 MB to 4.0 MB. This reduces the imported rig and curve count while retaining all 17 clips.

`Tools/prepare_dog_import.py` preserves every weighted joint's complete ancestor chain, the mesh nodes and scene roots. It checks the positions, normals, UVs, weights, triangle indices, retained animation inputs/outputs and inverse bind matrices against the previous source. It remaps joint indices; it removes only branches and animation channels that cannot affect the visible skinned meshes. Original archive hashes remain in the catalog. Archive reimport runs this compaction automatically.

Source equivalence and repeatability checks passed. The official Khronos glTF Validator reports zero errors on both exports. Unity Editor import and Play Mode still require checking on a machine with Unity 6000.0.62f1; source checks do not establish successful Unity import.
