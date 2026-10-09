#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using DesertShift.Player;
using Blackstone.Story;
using Blackstone.Interaction;

namespace Blackstone.Editor
{
    public static class BlackstoneProjectTools
    {
        public const string Scene = "Assets/Game/Scenes/SC_BlackstoneIsland.unity";
        [InitializeOnLoadMethod]
        static void ResolveInitialBindings()
        {
            // Package-owned render references and clip bindings only; no map generation.
            EditorApplication.delayCall += () =>
            {
                string key = "Blackstone.NativeBindings.v4.1." + Application.dataPath;
                if (EditorPrefs.GetBool(key, false) || !File.Exists(Scene)) return;
                try { Repair(); EditorPrefs.SetBool(key, true); }
                catch (Exception e) { Debug.LogWarning("Blackstone rendering setup: " + e.Message); }
            };
        }
        [MenuItem("Blackstone/Open Chapter 01", priority = 0)]
        public static void OpenChapter()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            DesertShift.Editor.ProjectTools.ConfigureRendering();
            EditorSceneManager.OpenScene(Scene);
        }
        [MenuItem("Blackstone/Open Character Test", priority = 1)]
        public static void OpenCharacterTest()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            DesertShift.Editor.ProjectTools.ConfigureRendering();
            EditorSceneManager.OpenScene("Assets/Game/Scenes/CharacterTest.unity");
        }
        [MenuItem("Blackstone/Validate Chapter", priority = 10)]
        public static void ValidateChapter()
        {
            int errors = 0;
            if (UnityEngine.Object.FindObjectsByType<PlayerMovement>(FindObjectsSortMode.None).Length != 1) errors++;
            if (UnityEngine.Object.FindObjectsByType<PlayerInputHandler>(FindObjectsSortMode.None).Length != 1) errors++;
            if (UnityEngine.Object.FindObjectsByType<AudioListener>(FindObjectsSortMode.None).Length != 1) errors++;
            var story = UnityEngine.Object.FindFirstObjectByType<PrisonStoryDirector>();
            if (story == null || story.player == null || story.input == null || story.mainCamera == null || story.audioBus == null
                || story.cellSpawn == null || story.solitarySpawn == null || story.visitSpawn == null || story.sleepPosition == null
                || story.niko == null || story.leader == null || story.rival == null || story.guard == null || story.brother == null
                || story.playerVisual == null || story.tattooMark == null || story.droppedKnife == null) errors++;
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
            {
                errors += GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject);
                var interact = t.GetComponent<StoryInteractable>();
                if (interact != null && interact.director == null) errors++;
                foreach (var r in t.GetComponents<Renderer>())
                    if (r.sharedMaterials.Any(m => m == null || m.shader == null || !m.shader.isSupported)) errors++;
            }
            var book = Resources.Load<TextAsset>("Blackstone/story-dialogue");
            if (book == null) errors++;
            else
            {
                var scenes = JsonUtility.FromJson<DialogueBook>(book.text);
                foreach (var scene in scenes.scenes)
                    foreach (var line in scene.lines)
                        if (Resources.Load<AudioClip>("Blackstone/Dialogue/" + line.id) == null) errors++;
            }
            Directory.CreateDirectory("Validation");
            File.WriteAllText("Validation/UnityChapterValidation.txt", $"Blackstone scene validation: {errors} errors.\n" +
                "This check must be followed by the Chapter01_PlayMode_Checklist.md traversal and scene tests.");
            if (errors != 0) throw new InvalidOperationException($"Blackstone scene validation failed: {errors} errors.");
            Debug.Log("Blackstone scene references and audio passed validation.");
        }
        [MenuItem("Blackstone/Repair Rendering and Animation", priority = 15)]
        public static void Repair()
        { DesertShift.Editor.ProjectTools.ConfigureRendering(); DesertShift.Editor.ProjectTools.RebuildAnimationBindings(); }
        [MenuItem("Blackstone/Build Windows x64", priority = 30)]
        public static void BuildWindows()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, BuildTarget.StandaloneWindows64))
                throw new InvalidOperationException("Install Windows Build Support for Unity 6000.0.62f1.");
            Repair(); EditorSceneManager.OpenScene(Scene); ValidateChapter();
            Directory.CreateDirectory("Builds/Windows");
            BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { Scene }, locationPathName = "Builds/Windows/BlackstoneIsland.exe",
                target = BuildTarget.StandaloneWindows64, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Blackstone Windows build failed.");
            Debug.Log("Windows build: Builds/Windows/BlackstoneIsland.exe");
        }
    }
}
#endif
