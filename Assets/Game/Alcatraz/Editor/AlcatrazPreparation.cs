#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using Blackstone.Foundation.Editor;

namespace Blackstone.Alcatraz.Editor
{
    public sealed class AlcatrazPreparation : IPreprocessBuildWithReport
    {
        public const string Island="Assets/Game/Scenes/SC_AlcatrazIsland.unity";
        public const string Chapter="Assets/Game/Scenes/SC_AlcatrazChapter01.unity";
        public const string Supplied="Assets/Game/Scenes/SC_AlcatrazSuppliedIsland.unity";
        public int callbackOrder=>1;
        [MenuItem("Alcatraz/Open Island",priority=0)]
        public static void OpenIsland()
        {
            if(!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            Prepare();AlcatrazPlayStartup.UseSuppliedIsland();EditorSceneManager.OpenScene(Supplied);
        }
        [MenuItem("Alcatraz/Open Original Playable Island",priority=2)]
        public static void OpenOriginal()
        {if(EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()){FoundationPreparation.Prepare();AlcatrazPlayStartup.UseCurrentScene();EditorSceneManager.OpenScene(Island);}}
        [MenuItem("Alcatraz/Open Chapter 01",priority=1)]
        public static void OpenChapter()
        {
            if(!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            FoundationPreparation.Prepare();AlcatrazPlayStartup.UseCurrentScene();EditorSceneManager.OpenScene(Chapter);
        }
        [MenuItem("Alcatraz/Prepare Characters",priority=5)]
        public static void Prepare(){FoundationPreparation.Prepare();Blackstone.Supplied.Editor.SuppliedAssetPreparation.Prepare();}
        [MenuItem("Alcatraz/Build Windows x64",priority=30)]
        public static void Build()
        {
            Prepare();Directory.CreateDirectory("Builds/Windows");
            var report=AlcatrazBuildSizeReport.BuildPlayer(new BuildPlayerOptions{scenes=new[]{Supplied,Chapter,Island},
                locationPathName="Builds/Windows/AlcatrazEscape.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});
            if(report.summary.result!=BuildResult.Succeeded)throw new InvalidOperationException("Alcatraz build failed.");
        }
        public void OnPreprocessBuild(BuildReport report)
        {
            if(EditorBuildSettings.scenes.Any(s=>s.enabled&&s.path==Supplied))Prepare();
            else if(EditorBuildSettings.scenes.Any(s=>s.enabled&&(s.path==Island||s.path==Chapter)))FoundationPreparation.Prepare();
        }
    }
}
#endif
