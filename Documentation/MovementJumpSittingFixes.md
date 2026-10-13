# Movement, jump and sitting fixes

Blocked gameplay input now clears horizontal momentum and cancels both buffered
and prepared jumps. Blocking input preserves an existing crouch rather than
forcing the character to stand under an obstacle. Gravity still applies to an
unseated character during dialogue.

Poker and yard conversations temporarily disable the character controller while
the player is seated. Leaving restores the previous position and orientation,
and restores control without stale jumping or landing state. Conversation cleanup
also runs when its coroutine is disposed. Vehicle seating is no longer overwritten
by the story actor's idle pose.

The generated locomotion controller accepts sitting and crouching from transient
start, stop, turning and airborne states. Sitting takes priority over airborne
animation. Transient animation triggers are cleared while sitting, crouching or
airborne. The character preparation revision changed so Unity regenerates the
controller instead of reusing the previous transition graph.

## Verification

C# grammar validation is available through `Tools/check_csharp_syntax.py`.
Character forward/gait validation is `Tools/validate_character_forward.py`.
These checks do not compile against Unity APIs or verify gameplay.

In Unity 6000.0.62f1, allow automatic character preparation to finish, then use
**Alcatraz > Validate Movement and Camera (Play Mode)**. The menu now includes
checks that blocked sprint momentum stops, a prepared jump is canceled, external
control disables gravity, seating remains anchored, and standing restores a clean
controller state. These added Unity checks have not been executed in the cloud
environment because the editor is unavailable.

Also verify the following in both exploration and Chapter 01:

- Walk, sprint, strafe while aiming, and stop without sliding after opening a
  dialogue or activity.
- Jump from standing and running; block input during jump preparation and confirm
  there is no delayed jump after the activity ends. Test landing and overhead
  collisions.
- Crouch under a low ceiling and start dialogue without clipping through it.
- Enter poker while moving or during a start/stop animation; remain seated without
  drifting or falling, then leave and walk/jump normally.
- Use the yard conversation table and return to the prior position afterward.
- Board and leave a vehicle; confirm the seated pose stays active while aboard.

Visual foot placement, seat height, jump appearance, swept physics and the Windows
player build still require Unity validation.
