# Revision 10 — fixes from the 21-second gameplay recording

The recording shows the original exploration island. At roughly 9–10 seconds,
Elias leaves supported ground, falls beneath the shoreline and is teleported back
only when he reaches the water. Shadowed walls are almost black, the exploration
goal is truncated, and four weapon panels cover a large part of the view.

## Step 1: movement and camera

- Exploration movement checks the ground ahead before walking off an exposed
  drop. Movement along an edge, stairs and supported short drops remain possible.
- Recovery uses a clear, supported last position and catches unsupported falls
  before the player reaches the underside of the island. The two island layouts
  now use one recovery owner.
- Teleports clear stale movement/ground state and immediately reset the camera,
  including teleports shorter than ten metres.
- Camera collision resolves existing sphere overlaps as well as sweeping toward
  the desired position. Obstructions contract the camera immediately; return to
  open space is smoothed.
- A Unity menu, **Alcatraz > Validate Movement and Camera (Play Mode)**, runs ten
  assertions against actual Unity colliders, including an overlapping wall,
  floor clipping, a cliff edge and a short teleport. This harness is provided but
  has not been executed in the authoring environment.

Available verification: C# grammar, native scene bindings, existing sampled
static route clearance/floor support, and native asset integrity. Unity Editor
is unavailable here; Unity compilation, Play Mode and live lighting remain
unverified.
