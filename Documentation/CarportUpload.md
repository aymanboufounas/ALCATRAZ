# Wooden carport map addition

The original `garage-roof-carport.zip` model is placed in the northeast factory yard. Choose **Workshop & recreation annex**, walk north through the perimeter opening, then follow the right side of the yard past the speaker and radio. Its annex-relative centre is (27, 0, 120); its grounded height is 3.2 metres and footprint is approximately 5.96 × 6.99 metres. It is clear of the factory and perimeter.

The native prefab keeps all 780 source triangles, the original 2048 × 2048 base-colour texture and static mesh colliders for the roof and supports. No mesh simplification or texture resizing is used. The original ZIP is retained byte for byte in SourceArchives; Source.json records the hash and conversion details. Carport is registered in the importer catalog and full-quality conversion is its default.

Validation: all 27 extras catalog entries passed reference, provenance and placement registration checks in Validation/CarportAssetsChecks.json. All 77 C# files passed grammar parsing. The native geometry was inspected in an [offline preview](CarportPreview.png), reproducible with `python Tools/render_carport_preview.py`. Unity import, physics and gameplay are unverified because the editor is unavailable.

`rusty-roof-house-3d-model-free.zip` remains unimported: the uploaded archive exceeds the attachment transfer tool’s 32 MiB limit. Upload it as split archive parts each below 32 MiB, or provide the model and textures in smaller archives, to finish adding the original house.
