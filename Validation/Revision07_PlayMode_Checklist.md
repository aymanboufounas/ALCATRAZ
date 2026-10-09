# Revision 07 — checks requiring Unity

Not executed in this environment. Run with Unity 6000.0.62f1 after full package and FBX import.

1. Open Alcatraz > Open Island; Prepare Characters if needed. Confirm no compilation errors and the orange prisoner is the player.
2. Confirm Elias' texture seams and B-04 text, Harrow's badge, valid rigs and contact with the floor. Compare tall/short and seated actors.
3. Walk from the yard through the cellhouse, all galleries, dining hall, showers, industries, storehouse and dock. Check collision at new benches, shelves and workstations.
4. Inspect all 16 roof apertures and daylight at different camera angles. Check transparent glazing, shadows and point-light performance in URP.
5. Confirm ten NPC patrols run, pause when obstructed and resume after the player moves. Check ambient workers do not intersect stools; verify NPC foot placement and idle offsets.
6. Open Chapter 01; start a new game. Complete knife concealment/stash, phone, rival fight, isolation and visitation. Check that extra NPCs do not take over mission triggers or dialogue.
7. Pause/resume and reload a checkpoint. Confirm additional NPC scripts stop with paused time and the existing mission state resumes.
8. Test keyboard/mouse and gamepad, especially M map, E interaction, chapter dialogue and poker.
9. Profile CPU/GPU/frame time and memory on the target machine; reduce lights or visible detail if needed.
10. Install Windows Build Support and use Alcatraz > Build Windows x64. Smoke-test the resulting executable.
