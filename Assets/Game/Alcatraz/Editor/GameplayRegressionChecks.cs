#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using DesertShift.Player;
using Blackstone.Foundation;

namespace Blackstone.Alcatraz.Editor
{
    // Executes the actual movement/camera methods against Unity colliders.
    // These checks require Play Mode and do not stand in for a full game playthrough.
    public static class GameplayRegressionChecks
    {
        const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        static object Invoke(object target, string method, params object[] args)
        { return target.GetType().GetMethod(method, Private).Invoke(target, args); }
        static void Check(bool condition, string name)
        { if (!condition) throw new InvalidOperationException("Alcatraz regression: " + name); }

        [MenuItem("Alcatraz/Validate Movement and Camera (Play Mode)", priority = 20)]
        public static void Run()
        {
            if (!EditorApplication.isPlaying)
            { Debug.LogError("Enter Play Mode before running movement and camera checks."); return; }
            float oldTime = Time.timeScale;
            CursorLockMode oldLock = Cursor.lockState;
            bool oldCursor = Cursor.visible;
            var root = new GameObject("Temporary Alcatraz regression checks");
            root.hideFlags = HideFlags.HideAndDontSave;
            // Keep the fixture away from the loaded island and its actors.
            Vector3 origin = new Vector3(10000, 0, 10000);
            try
            {
                GameObject floor = Box(root.transform, "Floor", origin-Vector3.up*.25f, new Vector3(10, .5f, 10));
                var hero = new GameObject("Test player"); hero.transform.SetParent(root.transform);
                hero.layer = 8; hero.transform.position = origin;
                var controller = hero.AddComponent<CharacterController>();
                controller.height = 1.78f; controller.center = Vector3.up*.89f; controller.radius = .25f;
                var movement = hero.AddComponent<PlayerMovement>(); movement.enabled = false;
                var input = hero.GetComponent<PlayerInputHandler>(); input.enabled = false;
                Physics.SyncTransforms();
                Check((bool)Invoke(movement, "SupportedPath", Vector3.forward*5.5f, 1f/60), "sprint across supported floor");
                hero.transform.position = origin+Vector3.forward*4.8f; Physics.SyncTransforms();
                Check(!(bool)Invoke(movement, "SupportedPath", Vector3.forward*5.5f, 1f/60), "sprint toward exposed edge");
                Check((bool)Invoke(movement, "SupportedPath", Vector3.right*5.5f, 1f/60), "movement parallel to edge");
                hero.transform.position = origin;
                floor.transform.position = origin-Vector3.up*1.75f; Physics.SyncTransforms();
                Check((bool)Invoke(movement, "SupportedPath", Vector3.forward*2, 1f/60), "drop onto nearby supported floor");
                floor.transform.position = origin-Vector3.up*4.25f; Physics.SyncTransforms();
                Check(!(bool)Invoke(movement, "SupportedPath", Vector3.forward*2, 1f/60), "unprotected four metre drop");
                floor.transform.position = origin-Vector3.up*.25f;

                var cameraObject = new GameObject("Test camera"); cameraObject.transform.SetParent(root.transform);
                cameraObject.AddComponent<Camera>();
                var camera = cameraObject.AddComponent<FoundationCamera>(); camera.enabled = false;
                camera.player = movement; camera.input = input;
                var visual=Box(hero.transform,"Visible prisoner proxy",origin+Vector3.up*.89f,new Vector3(.45f,1.78f,.3f));visual.layer=8;
                camera.characterVisual=visual.transform;Invoke(camera,"Start");
                var wall = Box(root.transform, "Wall", origin+new Vector3(0, 1.45f, -2), new Vector3(5, 3, .2f));
                Physics.SyncTransforms();
                Vector3 pivot = origin+Vector3.up*1.45f;
                var accessory=new GameObject("Player accessory on world layer");accessory.transform.SetParent(hero.transform);
                accessory.transform.position=pivot+Vector3.back*.6f;
                accessory.AddComponent<BoxCollider>().size=Vector3.one*.35f;Physics.SyncTransforms();
                Vector3 resolved = (Vector3)Invoke(camera, "Resolve", pivot, pivot+Vector3.back*4);
                Check(resolved.z > origin.z-1.7f&&resolved.z<origin.z-1.3f,
                    "camera ignores own accessory and still stops at the world wall");
                Check(((Vector3)Invoke(camera,"Separate",accessory.transform.position)-accessory.transform.position).sqrMagnitude<.000001f,
                    "own default-layer collider cannot displace the camera pivot");
                Check(!(bool)Invoke(camera,"BlockedAt",accessory.transform.position,.22f),
                    "own accessory cannot reject a visible third-person orbit");
                // Saturating the non-alloc sweep must still find a real world wall.
                for(int i=0;i<33;i++)
                {
                    var extra=new GameObject("Own overlapping accessory "+i);extra.transform.SetParent(hero.transform);
                    extra.transform.position=accessory.transform.position+Vector3.back*(i*.008f);
                    extra.AddComponent<BoxCollider>().size=Vector3.one*.3f;
                }
                Physics.SyncTransforms();
                resolved=(Vector3)Invoke(camera,"Resolve",pivot,pivot+Vector3.back*4);
                Check(resolved.z>origin.z-1.7f&&resolved.z<origin.z-1.3f,
                    "full collision contact buffer retains the nearest external obstruction");
                resolved = (Vector3)Invoke(camera, "Separate", wall.transform.position);
                Check(!Physics.CheckSphere(resolved, .225f, ~((1<<8)|(1<<2)), QueryTriggerInteraction.Ignore), "camera starts inside wall");
                resolved = (Vector3)Invoke(camera, "Resolve", pivot, origin-Vector3.up);
                Check(resolved.y >= .23f, "camera cannot cross floor while looking up");
                Check((Vector3)Invoke(camera, "Resolve", pivot, pivot) == pivot, "zero-length camera movement");
                var swimming=hero.AddComponent<FoundationSwimming>();swimming.enabled=false;
                movement.SetSwimming(true,0);
                resolved=(Vector3)Invoke(camera,"Resolve",pivot,origin-Vector3.up*2);
                Check(resolved.y>=.3f,"swimming camera stays above the ocean surface");
                movement.SetSwimming(false,0);
                typeof(PlayerMovement).GetProperty("Grounded").GetSetMethod(true).Invoke(movement, new object[]{true});
                resolved = (Vector3)Invoke(camera, "Resolve", pivot, origin+new Vector3(6, -1, 0));
                Check(resolved.y >= .25f, "camera orbit beside an exposed cliff stays above the player's floor");
                wall.transform.position=origin+new Vector3(0,1.45f,-.6f);wall.transform.localScale=new Vector3(1.1f,3,.2f);Physics.SyncTransforms();
                Vector3 close=(Vector3)Invoke(camera,"Resolve",pivot,pivot+Vector3.back*3.15f);
                object[] alternate={pivot,3.15f,false,close,Quaternion.Euler(12,0,0)};
                Invoke(camera,"ChooseVisibleOrbit",alternate);
                Check(camera.UsingObstructionOrbit&&Vector3.Distance(pivot,(Vector3)alternate[3])>=CameraFramingRules.MinimumDistance(false),
                    "near rear wall chooses a clear third-person side orbit");
                var sideWall=Box(root.transform,"Close left corner",origin+new Vector3(-.6f,1.45f,0),new Vector3(.2f,3,3));
                Physics.SyncTransforms();
                close=(Vector3)Invoke(camera,"Resolve",pivot,pivot+Vector3.back*3.15f);
                alternate=new object[]{pivot,3.15f,false,close,Quaternion.Euler(12,0,0)};
                Invoke(camera,"ChooseVisibleOrbit",alternate);
                Check(camera.UsingObstructionOrbit&&Vector3.Distance(pivot,(Vector3)alternate[3])>=CameraFramingRules.MinimumDistance(false),
                    "two close corner walls still select an available third-person orbit");
                sideWall.SetActive(false);Physics.SyncTransforms();
                visual.GetComponent<Renderer>().forceRenderingOff=true;Invoke(camera,"LateUpdate");
                Check(!visual.GetComponent<Renderer>().forceRenderingOff,"obstructed camera restores visible prisoner mesh");
                Check(GeometryUtility.TestPlanesAABB(GeometryUtility.CalculateFrustumPlanes(cameraObject.GetComponent<Camera>()),visual.GetComponent<Renderer>().bounds),
                    "obstructed third-person camera frustum contains the prisoner body");
                wall.SetActive(false);Physics.SyncTransforms();
                alternate=new object[]{pivot,3.15f,false,pivot+Vector3.back*3.15f,Quaternion.Euler(12,0,0)};
                Invoke(camera,"ChooseVisibleOrbit",alternate);
                Check(!camera.UsingObstructionOrbit,"rear view resumes when the wall clears");
                var cell=new GameObject("Temporary narrow cell");cell.transform.SetParent(root.transform);
                Box(cell.transform,"Cell left",origin+new Vector3(-.75f,1.5f,0),new Vector3(.1f,3,2));
                Box(cell.transform,"Cell right",origin+new Vector3(.75f,1.5f,0),new Vector3(.1f,3,2));
                Box(cell.transform,"Cell front",origin+new Vector3(0,1.5f,.75f),new Vector3(2,3,.1f));
                Box(cell.transform,"Cell rear",origin+new Vector3(0,1.5f,-.75f),new Vector3(2,3,.1f));
                var roof=Box(cell.transform,"Cell roof",origin+Vector3.up*3.05f,new Vector3(2,.1f,2));
                Physics.SyncTransforms();camera.SnapToPlayer();
                Check(camera.UsingObstructionOrbit&&camera.UsingElevatedOrbit&&camera.CurrentDistance>=CameraFramingRules.ElevatedMinimumDistance(false),
                    "a narrow cell with no horizontal boom uses available space above the prisoner");
                Check(!(bool)Invoke(camera,"BlockedAt",camera.transform.position,.22f),
                    "raised cell camera remains inside the walls and below the ceiling");
                Vector3 bodyOnScreen=cameraObject.GetComponent<Camera>().WorldToViewportPoint(origin+Vector3.up*.9f);
                Check(bodyOnScreen.z>.08f&&bodyOnScreen.x>0&&bodyOnScreen.x<1&&bodyOnScreen.y>0&&bodyOnScreen.y<1,
                    "raised cell view keeps the prisoner torso on screen");
                roof.transform.position=origin+Vector3.up*2.05f;Physics.SyncTransforms();camera.SnapToPlayer();
                Check(!camera.UsingElevatedOrbit&&!camera.UsingObstructionOrbit,
                    "a very low ceiling rejects raised views without inventing free space");
                Check(!(bool)Invoke(camera,"BlockedAt",camera.transform.position,.22f),
                    "a rejected raised view still cannot cross the cell ceiling");
                cell.SetActive(false);Physics.SyncTransforms();camera.SnapToPlayer();
                Check(!camera.UsingElevatedOrbit&&!camera.UsingObstructionOrbit&&camera.CurrentDistance>=3,
                    "ordinary third-person framing returns after leaving the narrow cell");
                wall.SetActive(true);wall.transform.position=origin+new Vector3(0,1.45f,-2);wall.transform.localScale=new Vector3(5,3,.2f);
                var brain=cameraObject.AddComponent<Unity.Cinemachine.CinemachineBrain>();
                var legacy=root.AddComponent<DesertShift.Camera.ThirdPersonCameraController>();
                typeof(DesertShift.Camera.ThirdPersonCameraController).GetField("brain",Private).SetValue(legacy,brain);
                var virtualObject=new GameObject("Temporary virtual camera");virtualObject.transform.SetParent(root.transform);
                legacy.virtualCamera=virtualObject.AddComponent<Unity.Cinemachine.CinemachineCamera>();
                legacy.SetExternalDriver(true);legacy.SetCinematic(false);
                Check(!brain.enabled&&!legacy.virtualCamera.enabled&&!legacy.enabled,"returning from a cinematic cannot revive a competing camera driver");
                int version = movement.TeleportVersion;
                movement.Teleport(origin+Vector3.right*2);
                Check(movement.TeleportVersion == version+1 && !movement.Grounded, "short teleport invalidates stale camera and ground state");
                movement.Teleport(origin); Physics.SyncTransforms();
                input.Capture(true);input.SetGameplayBlocked(true);
                typeof(PlayerMovement).GetField("velocity", Private).SetValue(movement,Vector3.forward*5.5f);
                typeof(PlayerMovement).GetField("jumpAt", Private).SetValue(movement,Time.time-.01f);
                typeof(PlayerMovement).GetField("lastGrounded", Private).SetValue(movement,Time.time);
                Invoke(movement,"Update");
                Check(Vector3.ProjectOnPlane(hero.transform.position-origin,Vector3.up).sqrMagnitude<.000001f,
                    "blocked input stops sprint momentum immediately");
                Check(!movement.JumpedThisFrame && movement.JumpPreparation==0,
                    "blocking input cancels a prepared jump");
                movement.SetExternalControl(true);
                Check(!controller.enabled && movement.Speed==0 && movement.VerticalSpeed==0,
                    "seated external control disables gravity and movement");
                Vector3 seatedPosition=hero.transform.position;Invoke(movement,"Update");
                Check(hero.transform.position==seatedPosition,"seated player stays anchored");
                movement.SetExternalControl(false);
                Check(controller.enabled && !movement.Grounded && !movement.JumpedThisFrame &&
                    !movement.LandedThisFrame && movement.AirTime==0 && movement.LandingRecovery==0,
                    "standing restores controller without stale jump or landing state");
                input.SetGameplayBlocked(false);
                movement.Teleport(origin);controller.Move(Vector3.down*.02f);
                typeof(PlayerMovement).GetField("lastGrounded",Private).SetValue(movement,Time.time);
                typeof(PlayerMovement).GetField("jumpAt",Private).SetValue(movement,Time.time-.0001f);
                Invoke(movement,"Update");
                Check(movement.JumpedThisFrame && movement.VerticalSpeed>0 && !movement.Grounded,
                    "prepared standing jump launches upward");
                Invoke(movement,"Update");
                Check(!movement.JumpedThisFrame,"prepared jump launches only once");
                for(int i=0;i<10000&&!movement.Grounded;i++)Invoke(movement,"Update");
                Check(movement.Grounded && movement.AirTime==0 && movement.VerticalSpeed<0,
                    "jump lands and restores grounded movement");
                Debug.Log("Alcatraz movement/camera checks passed: 35 assertions using Unity physics. Full gameplay and visual review are still required.");
            }
            catch (TargetInvocationException error)
            { Debug.LogException(error.InnerException ?? error); throw; }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
                Time.timeScale = oldTime; Cursor.lockState = oldLock; Cursor.visible = oldCursor;
                Physics.SyncTransforms();
            }
        }
        static GameObject Box(Transform parent, string name, Vector3 position, Vector3 size)
        {
            var box = GameObject.CreatePrimitive(PrimitiveType.Cube); box.name = name;
            box.transform.SetParent(parent); box.transform.position = position; box.transform.localScale = size;
            return box;
        }
    }
}
#endif
