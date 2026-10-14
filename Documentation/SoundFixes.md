# Combat sound corrections

Gunshots, reloads, empty magazines, drawing equipment, surface footsteps and impacts already have Unity audio hooks. The 44 foundation effect clips include recorded CC0 gunshots and reloads, Kenney impact recordings and prototype handling effects; see Revision05_AudioProvenance.json. These are not newly recorded weapon-specific sounds.

Punch and knife windups now use the existing Handling/Swing prototype rather than a punch contact recording. A successful boxing contact plays the Punch group at the delayed contact time; misses do not play a contact sound. Knife and bullet contacts retain the Impact group.

Spatial occlusion uses the actual AudioListener position, including while the camera follows a vehicle. Room reverb checks for overhead world geometry instead of coordinates from an older map. Pause and effects/master volume handling are retained.

Helicopter and boat engine loops are still missing. Supplied speakers and radios are static props. Unity is unavailable here, so audible playback, mix levels and reverb need a Unity play-mode check.
