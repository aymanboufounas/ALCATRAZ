# Third-person prisoner visibility

The supplied recording shows the prisoner visible while running and jumping (including frames at approximately 5, 15, 28 and 40 seconds). A first-person-only camera or a permanently absent player mesh therefore does not explain the entire recording. The repository did contain a specific close-obstruction failure: FoundationCamera hid every prisoner renderer whenever the camera contracted to within 0.68 metres of its pivot.

Normal third-person updates now keep the prisoner mesh enabled instead of hiding it at that threshold. If a wall crowds the rear boom, the camera tests collision-clear side/front orbit candidates and chooses a view with adequate distance, preferring more room and a smaller orbit change. A chosen side remains stable for near-equal alternatives. The view returns behind the prisoner when clearance returns. Close views widen the field of view and lower the look target; severely constrained views use a smaller near clip. A camera cannot guarantee a full-body view in every physically enclosed space, but the mesh is retained and unsafe alternate positions are rejected.

The avatar replacement is also safer. New rig geometry is measured from baked visible meshes, aligned and activated before the old visuals/animation are disabled. Missing or unusable imports keep the existing character visuals and report a setup error. Imported player skin updates offscreen, and the selected camera includes the player's renderer layers. An untagged valid gameplay camera can be selected and tagged; camera bindings are refreshed when reusing an existing driver. The camera's collision probe is reused safely.

Cinemachine ownership is explicit. The disabled legacy controller still handles story state calls, but returning from a cinematic cannot re-enable its competing brain or virtual camera while FoundationCamera owns the gameplay view. Story letterbox shots and vehicle renderer visibility remain under their existing systems.

## Load the current project revision

The screenshots show the older four-action pause menu. This branch already contains the newer cinematic ten-section pause menu with a uniformly fitted canvas. Update the Unity project from `fix/player-movement-jump-seating`; pulling `main` does not include these branch commits. Exit Play Mode, let script/asset compilation finish, then open the intended scene:

- `Assets/Game/Scenes/SC_AlcatrazChapter01.unity` for the chapter seen in the recording.
- `Assets/Game/Scenes/SC_AlcatrazSuppliedIsland.unity` for the supplied island and connected annex assets.

If imported rigs are missing, use **Blackstone → Prepare Character Foundation** and inspect the Console. Enter Play Mode and use **Alcatraz → Inspect Player and Camera** to report active meshes, renderer layers, camera ownership and current boom distance. This inspection does not edit the scene.

## Validation

Sixteen executable framing-rule assertions passed, covering rejection of blocked/invalid/too-close candidates, rear preference, symmetric side candidates, widened close framing, a clear side escape and no invented safe position in a fully blocked space. The CI workflow runs these rules.

All 82 C# files passed grammar parsing. Native integrity passed with zero errors across 2,606 native files. The existing Unity **Alcatraz → Validate Movement and Camera (Play Mode)** fixture now contains 23 assertions, including a near rear wall, clearing a previous rendering-off flag, returning behind the player, and preventing Cinemachine revival after a story camera transition.

The Unity fixture, API compilation, final appearance, animation/IK, collision sweeps and a full chapter playthrough remain unverified because Unity is unavailable in this environment. Source checks and numerical framing tests are not proof of final in-game rendering. Results are recorded in Validation/ThirdPersonVisibilityChecks.json.
