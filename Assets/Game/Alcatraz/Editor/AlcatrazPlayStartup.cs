#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Blackstone.Foundation.Editor;
using Blackstone.Supplied.Editor;

namespace Blackstone.Alcatraz.Editor
{
    // A previously open scene must not silently launch the obsolete island.
    [InitializeOnLoad]
    public static class AlcatrazPlayStartup
    {
        const string CurrentSceneKey="Alcatraz.Revision11.PlayCurrentScene";
        static AlcatrazPlayStartup()
        {
            EditorApplication.delayCall+=Configure;
            EditorApplication.playModeStateChanged+=BeforePlay;
        }
        static void Configure()
        {
            if(EditorApplication.isCompiling||EditorApplication.isUpdating)
            {EditorApplication.delayCall+=Configure;return;}
            if(EditorApplication.isPlayingOrWillChangePlaymode)return;
            EditorSceneManager.playModeStartScene=SessionState.GetBool(CurrentSceneKey,false)
                ?null:AssetDatabase.LoadAssetAtPath<SceneAsset>(AlcatrazPreparation.Supplied);
        }
        public static void UseSuppliedIsland()
        {SessionState.SetBool(CurrentSceneKey,false);Configure();}
        public static void UseCurrentScene()
        {SessionState.SetBool(CurrentSceneKey,true);Configure();}
        [MenuItem("Alcatraz/Start Play on Supplied Island",priority=3)]
        static void DefaultPlay(){UseSuppliedIsland();Debug.Log("Play now starts on your supplied Alcatraz island.");}
        [MenuItem("Alcatraz/Start Play on Current Scene",priority=4)]
        static void CurrentPlay(){UseCurrentScene();Debug.Log("Play now uses the open scene for this editor session.");}
        static void BeforePlay(PlayModeStateChange state)
        {
            if(state!=PlayModeStateChange.ExitingEditMode||SessionState.GetBool(CurrentSceneKey,false))return;
            try{FoundationPreparation.Prepare();SuppliedAssetPreparation.Prepare();}
            catch(Exception error)
            {EditorApplication.isPlaying=false;Debug.LogError("Alcatraz cannot start until asset preparation succeeds: "+error.Message);}
        }
    }
}
#endif
