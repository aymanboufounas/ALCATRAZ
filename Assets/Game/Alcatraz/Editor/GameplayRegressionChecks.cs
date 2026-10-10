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
                camera.player = movement; camera.input = input; Invoke(camera, "Start");
                var wall = Box(root.transform, "Wall", origin+new Vector3(0, 1.45f, -2), new Vector3(5, 3, .2f));
                Physics.SyncTransforms();
                Vector3 pivot = origin+Vector3.up*1.45f;
                Vector3 resolved = (Vector3)Invoke(camera, "Resolve", pivot, pivot+Vector3.back*4);
                Check(resolved.z > origin.z-1.7f, "camera stays in front of obstructing wall");
                resolved = (Vector3)Invoke(camera, "Separate", wall.transform.position);
                Check(!Physics.CheckSphere(resolved, .225f, ~((1<<8)|(1<<2)), QueryTriggerInteraction.Ignore), "camera starts inside wall");
                resolved = (Vector3)Invoke(camera, "Resolve", pivot, origin-Vector3.up);
                Check(resolved.y >= .23f, "camera cannot cross floor while looking up");
                Check((Vector3)Invoke(camera, "Resolve", pivot, pivot) == pivot, "zero-length camera movement");
                typeof(PlayerMovement).GetProperty("Grounded").GetSetMethod(true).Invoke(movement, new object[]{true});
                resolved = (Vector3)Invoke(camera, "Resolve", pivot, origin+new Vector3(6, -1, 0));
                Check(resolved.y >= .25f, "camera orbit beside an exposed cliff stays above the player's floor");
                int version = movement.TeleportVersion;
                movement.Teleport(origin+Vector3.right*2);
                Check(movement.TeleportVersion == version+1 && !movement.Grounded, "short teleport invalidates stale camera and ground state");
                Debug.Log("Alcatraz movement/camera checks passed: 11 assertions using Unity physics. Full gameplay and visual review are still required.");
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
