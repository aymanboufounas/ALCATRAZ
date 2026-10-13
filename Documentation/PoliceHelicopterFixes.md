# Police equipment and Little Bird fixes

The supplied police officer's helmet is now centered on its named head mesh,
rather than on bounds that include its arms and holstered gun. The helmet is raised
to keep the face clear. Helmet and vest anchors correct the supplied equipment's
opposite forward direction, and the vest is fitted around the torso at 0.56 metres.
The officer's original mesh and three textures are unchanged. This remains the
supplied static OBJ officer, not a newly animated or higher-resolution character.

The Little Bird's original glTF cockpit uses a transmission material. Its previous
native conversion lost that setting and produced an opaque gray window. The native
material now uses double-sided transparent URP glass with depth writing disabled.
This is a transparency approximation, not the source renderer's exact refraction
or index-of-refraction effect. The native bake preserves this correction.

The vehicle root now follows the cockpit's horizontal center instead of the center
of the helicopter's combined rotor/tail bounds. The tail collision box is moved
and extended for that origin. Rotor pivots use transformed local mesh centers so
rotation of the entire aircraft does not shift the axle using a world-aligned
bounding box.

Boarding holds the current altitude instead of automatically requesting a
2.5-metre climb. Keyboard Space/Ctrl and gamepad A/B lift inputs combine: an idle
connected gamepad cannot suppress the keyboard; duplicate rise inputs remain at
normal strength; opposing rise/descend inputs cancel; blocked controls supply zero
lift. Vehicle exit clearance now includes other vehicle colliders, preventing
standing exit points inside the aircraft or another vehicle.

## Validation

- All 74 C# files passed grammar checks; this does not compile against Unity APIs.
- 32 executable mixed-device/blocked helicopter input assertions passed under Mono.
- 17 source material/geometry checks passed. All 7,814 police and 27,453 helicopter
  triangles are retained, with police texture bindings and transparent glass settings
  verified. Results: `Validation/PoliceHelicopterChecks.json`.
- Existing supplied-asset dependency/floor checks passed (18,426 checks).
- Labelled [police front](PoliceHelicopterPreviews/Police.png),
  [police rear](PoliceHelicopterPreviews/PoliceRear.png) and
  [helicopter](PoliceHelicopterPreviews/Helicopter.png) previews were rendered and
  visually inspected offline. These are not Unity screenshots.

In Unity 6000.0.62f1, open the supplied island and use
**Alcatraz > Validate Supplied Gameplay (Play Mode)**. The checks now load either
native or prepared models, verify the head-aligned equipment, cockpit transparency,
both rotors, seat/camera origin and absence of an automatic takeoff command.
Leave any vehicle or seated activity before running the menu.

Then inspect the officer from front/back, board the Little Bird, test keyboard
controls with a connected idle gamepad, take off, turn, land and exit beside clear
ground. Inspect rotor axles, transparent windows and tail collision clearance.
These live Unity checks, flight physics and a Windows build remain unexecuted
because the editor is unavailable in this cloud machine.
