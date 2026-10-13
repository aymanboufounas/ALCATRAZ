#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

namespace Blackstone.Foundation.Editor
{
    public sealed class FoundationPreparation : IPreprocessBuildWithReport
    {
        public const string Controller="Assets/Game/Resources/BlackstoneFoundation/Locomotion.controller";
        public const string Scene="Assets/Game/Scenes/SC_BlackstoneFoundation.unity";
        public const string StoryScene="Assets/Game/Scenes/SC_BlackstoneStory_Upgraded.unity";
        const string Revision="foundation-12.1-motion";
        static bool preparing;
        static bool scheduled;
        [Serializable] sealed class GaitData { public float[] thresholds=new float[0]; }
        public int callbackOrder=>0;
        [InitializeOnLoadMethod] static void Initialize(){Schedule();}
        internal static void Schedule()
        {
            if(scheduled)return;scheduled=true;
            EditorApplication.delayCall+=TryAutomatic;
        }
        static void TryAutomatic()
        {
            scheduled=false;
            if(EditorApplication.isCompiling||EditorApplication.isUpdating){Schedule();return;}
            string stamp="Assets/Game/Resources/BlackstoneFoundation/ImportRevision.txt";
            if(File.Exists(stamp)&&File.ReadAllText(stamp)==Revision&&File.Exists(Controller))return;
            try{Prepare();}catch(Exception e){Debug.LogWarning("Blackstone character setup: "+e.Message+". Use Blackstone > Prepare Character Foundation.");}
        }
        [MenuItem("Blackstone/Prepare Character Foundation",priority=5)]
        public static void Prepare()
        {
            if(preparing)return;preparing=true;
            try
            {
                DesertShift.Editor.ProjectTools.ConfigureRendering();
                foreach(string path in AssetDatabase.GetAllAssetPaths().Where(RocketboxImporter.IsSource))
                {
                    var importer=AssetImporter.GetAtPath(path) as ModelImporter;
                    if(importer==null)throw new InvalidOperationException("Model import unavailable: "+path);
                    if(importer.userData!=Revision)
                    {
                        RocketboxImporter.Configure(importer,path);importer.userData=Revision;importer.SaveAndReimport();
                    }
                }
                foreach(string profile in new[]{"16","07","12","17","20"})
                {
                    string path=RocketboxImporter.Characters+"Male_Adult_"+profile+"/Male_Adult_"+profile+".fbx";
                    var model=AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if(model==null||model.GetComponentInChildren<SkinnedMeshRenderer>()==null)
                        throw new InvalidOperationException("Missing skinned model: "+path);
                    var animator=model.GetComponent<Animator>();
                    if(animator==null||animator.avatar==null||!animator.avatar.isValid)
                        throw new InvalidOperationException("Invalid Generic avatar: "+path);
                }
                BuildController();AssetDatabase.SaveAssets();
                File.WriteAllText("Assets/Game/Resources/BlackstoneFoundation/ImportRevision.txt",Revision);
                AssetDatabase.Refresh();Debug.Log("Blackstone character foundation prepared.");
            }
            finally{preparing=false;}
        }
        static AnimationClip Clip(string name)
        {
            string path=RocketboxImporter.Animations+name+".fbx";
            var clip=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().FirstOrDefault(c=>!c.name.StartsWith("__preview__",StringComparison.Ordinal));
            if(clip==null)throw new InvalidOperationException("Animation unavailable: "+path);
            return clip;
        }
        static void BuildController()
        {
            if(File.Exists(Controller))AssetDatabase.DeleteAsset(Controller);
            Directory.CreateDirectory(Path.GetDirectoryName(Controller));
            var controller=AnimatorController.CreateAnimatorControllerAtPath(Controller);
            controller.AddParameter("Speed",AnimatorControllerParameterType.Float);
            controller.AddParameter("Direction",AnimatorControllerParameterType.Float);
            controller.AddParameter("Seated",AnimatorControllerParameterType.Bool);
            controller.AddParameter("Crouch",AnimatorControllerParameterType.Bool);
            controller.AddParameter("Air",AnimatorControllerParameterType.Bool);
            foreach(string trigger in new[]{"Start","Stop","TurnLeft","TurnRight"})controller.AddParameter(trigger,AnimatorControllerParameterType.Trigger);
            var parameters=controller.parameters;
            for(int i=0;i<parameters.Length;i++)if(parameters[i].name=="Direction")parameters[i].defaultFloat=1;
            controller.parameters=parameters;
            var machine=controller.layers[0].stateMachine;
            var blend=new BlendTree {name="Measured locomotion",blendType=BlendTreeType.Simple1D,blendParameter="Speed",useAutomaticThresholds=false};
            AssetDatabase.AddObjectToAsset(blend,controller);
            var data=JsonUtility.FromJson<GaitData>(File.ReadAllText("Assets/Game/Resources/BlackstoneFoundation/GaitSpeeds.json"));
            float[] thresholds=data!=null&&data.thresholds.Length==6?data.thresholds:new[]{0f,.81f,1f,1.47f,2.83f,5.75f};
            string[] names={"Idle","WalkSlow","Walk","WalkFast","Run","RunFast"};
            for(int i=0;i<names.Length;i++)blend.AddChild(Clip(names[i]),thresholds[i]);
            var ground=machine.AddState("Locomotion");ground.motion=blend;ground.speedParameter="Direction";ground.speedParameterActive=true;machine.defaultState=ground;
            foreach(string mode in new[]{"Seated","Crouch","Air"})
            {
                var state=machine.AddState(mode);state.motion=Clip(mode=="Air"?"Idle":mode);
                var enter=machine.AddAnyStateTransition(state);enter.hasExitTime=false;enter.duration=.15f;enter.canTransitionToSelf=false;enter.AddCondition(AnimatorConditionMode.If,0,mode);
                if(mode!="Seated")enter.AddCondition(AnimatorConditionMode.IfNot,0,"Seated");
                if(mode=="Crouch")enter.AddCondition(AnimatorConditionMode.IfNot,0,"Air");
                var leave=state.AddTransition(ground);leave.hasExitTime=false;leave.duration=.15f;leave.AddCondition(AnimatorConditionMode.IfNot,0,mode);
            }
            foreach(string name in new[]{"Start","Stop","TurnLeft","TurnRight"})
            {
                var state=machine.AddState(name);state.motion=Clip(name);
                var enter=ground.AddTransition(state);enter.hasExitTime=false;enter.duration=.1f;enter.AddCondition(AnimatorConditionMode.If,0,name);
                enter.AddCondition(AnimatorConditionMode.IfNot,0,"Seated");enter.AddCondition(AnimatorConditionMode.IfNot,0,"Crouch");enter.AddCondition(AnimatorConditionMode.IfNot,0,"Air");
                var leave=state.AddTransition(ground);leave.hasExitTime=true;leave.exitTime=.85f;leave.duration=.15f;
                if(name=="Stop")
                {var interrupt=state.AddTransition(ground);interrupt.hasExitTime=false;interrupt.duration=.1f;interrupt.AddCondition(AnimatorConditionMode.Greater,.3f,"Speed");}
                if(name=="Start")
                {var interrupt=state.AddTransition(ground);interrupt.hasExitTime=false;interrupt.duration=.08f;interrupt.AddCondition(AnimatorConditionMode.Greater,thresholds[2],"Speed");}
            }
        }
        [MenuItem("Blackstone/Open Character Foundation",priority=-1)]
        public static void Open()
        {
            if(!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            Prepare();EditorSceneManager.OpenScene(Scene);
        }
        [MenuItem("Blackstone/Open Story With New Characters",priority=2)]
        public static void OpenStory()
        {
            if(!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            Prepare();EditorSceneManager.OpenScene(StoryScene);
        }
        [MenuItem("Blackstone/Build Foundation Windows x64",priority=31)]
        public static void Build()
        {
            Prepare();Directory.CreateDirectory("Builds/Windows");
            var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions {scenes=new[]{Scene,StoryScene},
                locationPathName="Builds/Windows/BlackstoneIsland.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});
            if(report.summary.result!=BuildResult.Succeeded)throw new InvalidOperationException("Windows build failed.");
        }
        public void OnPreprocessBuild(BuildReport report)
        {if(EditorBuildSettings.scenes.Any(s=>s.enabled&&(s.path==Scene||s.path==StoryScene)))Prepare();}
    }
    public sealed class FoundationImportWatcher : AssetPostprocessor
    {
        static void OnPostprocessAllAssets(string[] imported,string[] deleted,string[] moved,string[] previous)
        {if(imported.Any(RocketboxImporter.IsSource))FoundationPreparation.Schedule();}
    }
}
#endif
