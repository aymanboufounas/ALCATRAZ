# Connected supplied island and prison

The supplied Alcatraz scan remains the exterior. Its closed cellhouse shell does not include a navigable prison interior. Revision 11 packages the project's native furnished cellhouse as an interior prefab, with its three tiers, stairs, galleries, cell beds/plumbing, skylights, lights and dining hall. The legacy island terrain, exterior buildings, player and story director are excluded. The mixed railing batch is cropped to the interior.

Press E at the exterior cellhouse marker, or choose **Cellhouse** in the pause/title menu, to enter. The same player, character, equipment, ammunition and camera remain loaded. The south exit returns to the supplied exterior; walking across it also returns safely. **Helipad** and **Coastal house** remain available from the pause menu. The interior has six native rigged guards/inmates with three supported patrol routes and its own floorplan map. Chapter 01 is still a separate story scene, labelled as such in the menu.

The exterior now uses the project's animated coastal-water material. The interior reuses existing native architecture and PBR materials; it is an adaptation of the reference, not an exact photographic recreation of the uploaded concept.

Executed source checks cover prefab references, exclusion of the old exterior, retained furniture/lights, and 27 routes/stations with native mesh/box floor support and sampled clearance. These are static source checks, not Unity CharacterController tests.

Unity validation menus:

- **Alcatraz > Validate Character Facing**: 40 actual imported-rig orientation checks.
- **Alcatraz > Validate Supplied Gameplay (Play Mode)**: prepared assets, visible forward direction, helicopter placement, entry/exit support and preservation of equipment.
- **Alcatraz > Validate Movement and Camera (Play Mode)**: existing Unity physics regression cases.
- **Alcatraz > Validate HUD Layout**: existing resolution/font-layout cases.

Unity Editor is unavailable in this workspace. These Unity menus, shader compilation, animation playback and a Windows build have not been executed here. GitHub source CI and the offline checks are recorded separately from those remaining runtime checks.
