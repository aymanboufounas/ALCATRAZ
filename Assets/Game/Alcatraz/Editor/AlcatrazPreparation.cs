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
        public int callbackOrder=>1;
        [MenuItem("Alcatraz/Open Island",priority=0)]
        public static void OpenIsland()
        {
            if(!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            FoundationPreparation.Prepare();EditorSceneManager.OpenScene(Island);
        }
        [MenuItem("Alcatraz/Open Chapter 01",priority=1)]
        public static void OpenChapter()
        {
            if(!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            FoundationPreparation.Prepare();EditorSceneManager.OpenScene(Chapter);
        }
        [MenuItem("Alcatraz/Prepare Characters",priority=5)]
        public static void Prepare(){FoundationPreparation.Prepare();}
        [MenuItem("Alcatraz/Build Windows x64",priority=30)]
        public static void Build()
        {
            Prepare();Directory.CreateDirectory("Builds/Windows");
            var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{Island,Chapter},
                locationPathName="Builds/Windows/AlcatrazEscape.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});
            if(report.summary.result!=BuildResult.Succeeded)throw new InvalidOperationException("Alcatraz build failed.");
        }
        public void OnPreprocessBuild(BuildReport report)
        {if(EditorBuildSettings.scenes.Any(s=>s.enabled&&(s.path==Island||s.path==Chapter)))Prepare();}
    }
}
#endif
