# Revision 09 — movement and close-wall camera

The user's 13.47-second recording shows the prisoner moving in the cellhouse,
with abrupt direction changes and camera views very close to the body.

Free movement now faces actual horizontal travel while decelerating and turning.
The imported visual no longer adds a second movement-direction rotation during
free running. Backward clip playback is confined to aiming. Ground contact
correction lifts a penetrating ankle and leaves a raised swing foot alone.
The start state can exit as soon as movement reaches the measured walk speed,
instead of remaining in a slow start animation while the controller accelerates.

The camera snaps after large teleports, retains wall collision checks, and
temporarily hides the new character visual when a wall pushes the camera within
0.68 metres of the follow point. Visibility is restored for cinematic shots and
when the camera component is disabled. It does not re-enable old character art.

The character import revision has changed, so Unity rebuilds the locomotion
controller automatically. Existing projects can run **Alcatraz > Prepare
Characters** after script compilation.

## Verification

- C# grammar: 52 files, zero syntax errors.
- Existing story and animation assets are retained.
- The protected baseline explicitly allows the requested PlayerMovement change;
  the other baseline protections remain in place.
- Unity import, type resolution, camera physics and live animation playback
  remain unverified here because Unity Editor is unavailable.

In Unity, test forward sprint, abrupt W/S changes, diagonal movement, aimed
backward walking, stopping, stairs, jumps, and running beside cell bars. Check
that close-wall hiding restores the body when moving back into open space and
that dialogue shots still show Elias.
