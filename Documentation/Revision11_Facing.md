# Revision 11: visible forward direction

The native Rocketbox character and walk/run source clips share the same anatomical forward direction. The previous runtime used the imported FBX root's orientation without checking whether Unity's axis conversion preserved the visible character's direction. Moving the controller forward could therefore move the visible character backward.

Each character now has an unanimated orientation parent. Before starting its Animator, the runtime projects both foot-to-toe vectors onto the ground and rotates this parent to match the actor's travel-facing direction. The imported skeleton and its animation bindings remain intact. Free movement still turns toward actual travel; aimed backward movement uses the existing backpedal playback.

`Tools/validate_character_forward.py` checks the five native FBX rigs under both horizontal reflection conventions, eight actor headings and eight imported headings. It also checks forward root travel and backward stance-foot movement in all five walk/run clips. The recorded 650 source/math checks pass. These checks do not run Unity's importer or Animator.

Unity menu **Alcatraz > Validate Character Facing** checks the actual imported rigs under 40 orientation cases. This needs to be run in Unity; it was not executed in this workspace. A Play Mode review of W/A/S/D, Shift, aiming and camera orbit is still required.
