#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using DesertShift.Core;
using DesertShift.Player;
using DesertShift.Interaction;

namespace DesertShift.Editor
{
    /// <summary>Manual tools only. No InitializeOnLoad, asset watcher or scene regeneration.</summary>
    public static class ProjectTools
    {
        const string ScenePath = "Assets/_DesertShift/Scenes/SC_DesertTown.unity";
        const string Settings = "Assets/_DesertShift/Settings/";
        [MenuItem("Desert Shift/Open Desert Town", priority = 0)]
        public static void OpenScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(ScenePath);
        }
        [MenuItem("Desert Shift/Validate Scene", priority = 10)]
        public static void ValidateScene()
        {
            int errors = 0, renderers = 0, colliders = 0;
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
            {
                int missing = GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject);
                if (missing > 0) { errors += missing; Debug.LogError("Missing script on " + t.name, t); }
                foreach (var r in t.GetComponents<Renderer>())
                {
                    renderers++;
                    foreach (var material in r.sharedMaterials)
                    {
                        if (material == null || material.shader == null || !material.shader.isSupported)
                        { errors++; Debug.LogError("Missing or unsupported material on " + r.name, r); }
                    }
                }
                var mesh = t.GetComponent<MeshFilter>();
                if (mesh != null && (mesh.sharedMesh == null || mesh.sharedMesh.vertexCount == 0))
                { errors++; Debug.LogError("Missing or empty mesh: " + t.name, t); }
                var skin = t.GetComponent<SkinnedMeshRenderer>();
                if (skin != null && (skin.sharedMesh == null || skin.bones.Length == 0 || skin.bones.Any(b => b == null)))
                { errors++; Debug.LogError("Incomplete skin on " + t.name, t); }
                colliders += t.GetComponents<Collider>().Length;
                var door = t.GetComponent<DoorController>();
                if (door != null && (door.hinge == null || door.leaf == null))
                { errors++; Debug.LogError("Door references are incomplete: " + t.name, t); }
            }
            var player = UnityEngine.Object.FindFirstObjectByType<PlayerMovement>();
            if (player == null || UnityEngine.Camera.main == null || GraphicsSettings.defaultRenderPipeline == null)
            { errors++; Debug.LogError("Player, camera or URP pipeline is missing."); }
            string report = $"Desert Shift scene validation: {errors} errors; {renderers} renderers; {colliders} colliders.\n" +
                "This check does not certify traversal, animation appearance, frame rate or Play Mode stability.";
            Directory.CreateDirectory("Validation"); File.WriteAllText("Validation/UnitySceneValidation.txt", report);
            if (errors == 0) Debug.Log(report); else Debug.LogError(report);
        }

        [MenuItem("Desert Shift/Repair Rendering Configuration", priority = 30)]
        public static void ConfigureRendering()
        {
            // Repairs configuration in place; never touches environment or player geometry.
            var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(Settings + "DesertShift_Renderer.asset");
            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                AssetDatabase.CreateAsset(renderer, Settings + "DesertShift_Renderer.asset");
            }
            var pipe = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(Settings + "DesertShift_URP.asset");
            if (pipe == null)
            {
                pipe = ScriptableObject.CreateInstance<UniversalRenderPipelineAsset>();
                AssetDatabase.CreateAsset(pipe, Settings + "DesertShift_URP.asset");
            }
            var so = new SerializedObject(pipe);
            var renderers = so.FindProperty("m_RendererDataList");
            renderers.arraySize = 1; renderers.GetArrayElementAtIndex(0).objectReferenceValue = renderer;
            so.FindProperty("m_DefaultRendererIndex").intValue = 0;
            so.ApplyModifiedPropertiesWithoutUndo();
            var rendererSO = new SerializedObject(renderer);
            var postData = rendererSO.FindProperty("postProcessData");
            if (postData != null && postData.objectReferenceValue == null)
            {
                string[] assets = AssetDatabase.FindAssets("t:PostProcessData");
                if (assets.Length > 0)
                    postData.objectReferenceValue = AssetDatabase.LoadMainAssetAtPath(AssetDatabase.GUIDToAssetPath(assets[0]));
                rendererSO.ApplyModifiedPropertiesWithoutUndo();
            }
            var aoType = typeof(UniversalRenderPipelineAsset).Assembly.GetType(
                "UnityEngine.Rendering.Universal.ScreenSpaceAmbientOcclusion");
            if (aoType != null && !renderer.rendererFeatures.Exists(f => f != null && f.GetType() == aoType))
            {
                var ao = ScriptableObject.CreateInstance(aoType) as ScriptableRendererFeature;
                if (ao != null)
                {
                    ao.name = "Desert Contact Occlusion";
                    AssetDatabase.AddObjectToAsset(ao, renderer);
                    renderer.rendererFeatures.Add(ao); ao.Create();
                }
            }
            GraphicsSettings.defaultRenderPipeline = pipe; QualitySettings.renderPipeline = pipe;
            var bootstrap = UnityEngine.Object.FindFirstObjectByType<GameBootstrap>();
            if (bootstrap != null) { bootstrap.renderPipeline = pipe; bootstrap.rendererData = renderer; EditorUtility.SetDirty(bootstrap); }
            renderer.SetDirty(); EditorUtility.SetDirty(pipe); EditorUtility.SetDirty(renderer);
            AssetDatabase.SaveAssets();
            Debug.Log("Desert Shift rendering assets repaired in place. Your scene geometry was preserved.");
        }
        [MenuItem("Desert Shift/Rebuild Animation Bindings", priority = 31)]
        public static void RebuildAnimationBindings()
        {
            foreach (var id in AssetDatabase.FindAssets("t:AnimationClip", new[] { "Assets/_DesertShift/Animations/Character" }))
            {
                var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(AssetDatabase.GUIDToAssetPath(id));
                if (clip == null) continue;
                // Saving each native curve lets this exact editor version refresh binding constants.
                foreach (var binding in AnimationUtility.GetCurveBindings(clip))
                {
                    var curve = AnimationUtility.GetEditorCurve(clip, binding);
                    AnimationUtility.SetEditorCurve(clip, binding, curve);
                }
                clip.EnsureQuaternionContinuity(); EditorUtility.SetDirty(clip);
            }
            AssetDatabase.SaveAssets(); Debug.Log("Animation bindings refreshed without replacing clips or the controller.");
        }
        [MenuItem("Desert Shift/Capture Six Cinematic Views", priority = 40)]
        public static void CaptureViews()
        {
            if (!Application.isPlaying) { Debug.LogWarning("Enter Play Mode first so the atmosphere and humanoid rig are active."); return; }
            var main = UnityEngine.Camera.main;
            if (main == null) return;
            var views = UnityEngine.Object.FindObjectsByType<CinematicView>(FindObjectsSortMode.None).OrderBy(v => v.name).ToArray();
            Directory.CreateDirectory("Captures");
            var go = new GameObject("Temporary capture camera"); var camera = go.AddComponent<UnityEngine.Camera>(); camera.CopyFrom(main);
            camera.GetUniversalAdditionalCameraData().renderPostProcessing = true;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32); rt.Create();
            var previousRT = RenderTexture.active;
            var player = UnityEngine.Object.FindFirstObjectByType<PlayerMovement>();
            Vector3 previousPosition = player != null ? player.transform.position : Vector3.zero;
            Quaternion previousRotation = player != null ? player.transform.rotation : Quaternion.identity;
            try
            {
                foreach (var view in views)
                {
                    if (player != null)
                    {
                        player.Teleport(view.stagePlayer ? view.playerPosition : previousPosition);
                        player.transform.rotation = view.stagePlayer ? Quaternion.Euler(0, view.playerYaw, 0) : previousRotation;
                        Physics.SyncTransforms();
                    }
                    camera.transform.SetPositionAndRotation(view.transform.position, view.transform.rotation);
                    camera.fieldOfView = view.fieldOfView;
                    var request = new UniversalRenderPipeline.SingleCameraRequest { destination = rt };
                    if (!RenderPipeline.SupportsRenderRequest(camera, request))
                        throw new InvalidOperationException("The active pipeline cannot render this capture request.");
                    RenderPipeline.SubmitRenderRequest(camera, request);
                    RenderTexture.active = rt; var image = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
                    image.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); image.Apply();
                    File.WriteAllBytes(Path.Combine("Captures", view.name + ".png"), image.EncodeToPNG()); UnityEngine.Object.Destroy(image);
                }
            }
            finally
            {
                if (player != null) { player.Teleport(previousPosition); player.transform.rotation = previousRotation; }
                RenderTexture.active = previousRT; camera.targetTexture = null; rt.Release();
                UnityEngine.Object.Destroy(rt); UnityEngine.Object.Destroy(go);
            }
            Debug.Log("Six 1920 × 1080 Unity captures written to Captures/.");
        }
        [MenuItem("Desert Shift/Build Windows x64", priority = 50)]
        public static void BuildWindows()
        {
            if (EditorApplication.isPlaying) throw new InvalidOperationException("Exit Play Mode before building.");
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64))
                throw new InvalidOperationException("Install Windows Build Support in Unity Hub for this editor.");
            ConfigureRendering(); RebuildAnimationBindings();
            Directory.CreateDirectory("Builds/Windows");
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { ScenePath }, locationPathName = "Builds/Windows/DesertShift.exe",
                target = BuildTarget.StandaloneWindows64, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("Windows build failed: " + report.summary.result);
            Debug.Log("Windows build ready: Builds/Windows/DesertShift.exe");
        }
    }
}
#endif
