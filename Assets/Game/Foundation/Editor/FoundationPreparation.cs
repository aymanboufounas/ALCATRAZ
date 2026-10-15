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
        const string Revision="foundation-15.0-locomotion";
        static bool preparing;
        static bool scheduled;
        const string Stamp="Assets/Game/Resources/BlackstoneFoundation/ImportRevision.txt";
        static readonly string[] Profiles={"16","07","12","17","20"};
        static readonly string[] Clips={"Idle","WalkSlow","Walk","WalkFast","Run","RunFast","Seated","Crouch","Start","Stop","RunStart","RunStop","TurnLeft","TurnRight"};
        static readonly string[] GroundClips={"Idle","WalkSlow","Walk","WalkFast","Run","RunFast"};
        static readonly string[] Triggers={"Start","Stop","RunStart","RunStop","TurnLeft","TurnRight"};
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
            try{EnsureReady();}catch(Exception e){Debug.LogWarning("Blackstone character setup: "+e.Message+". Use Blackstone > Prepare Character Foundation.");}
        }
        public static bool SceneUsesFoundation(string path)
        {
            if(string.IsNullOrEmpty(path)||!File.Exists(path))return false;
            string script=AssetDatabase.AssetPathToGUID("Assets/Game/Foundation/Scripts/FoundationBootstrap.cs");
            return !string.IsNullOrEmpty(script)&&File.ReadAllText(path).Contains("guid: "+script);
        }
        public static void EnsureReady()
        {
            if(!File.Exists(Stamp)||File.ReadAllText(Stamp)!=Revision||AssetDatabase.LoadAssetAtPath<AnimatorController>(Controller)==null)
            {Prepare();return;}
            try{ValidatePrepared();}
            catch(InvalidOperationException){Prepare();}
        }
        public static void ValidatePrepared()
        {
            foreach(string path in AssetDatabase.GetAllAssetPaths().Where(RocketboxImporter.IsSource))
            {
                var importer=AssetImporter.GetAtPath(path) as ModelImporter;
                bool animation=path.StartsWith(RocketboxImporter.Animations,StringComparison.Ordinal);
                if(importer==null||importer.animationType!=ModelImporterAnimationType.Generic
                    ||!importer.bakeAxisConversion||!importer.preserveHierarchy||importer.importAnimation!=animation
                    ||!importer.useFileScale||Mathf.Abs(importer.globalScale-1)>.0001f||importer.motionNodeName!="Bip01")
                    throw new InvalidOperationException("Character import settings need repair: "+path);
            }
            foreach(string profile in Profiles)
            {
                string path=RocketboxImporter.Characters+"Male_Adult_"+profile+"/Male_Adult_"+profile+".fbx";
                var model=AssetDatabase.LoadAssetAtPath<GameObject>(path);
                var skins=model!=null?model.GetComponentsInChildren<SkinnedMeshRenderer>(true):new SkinnedMeshRenderer[0];
                if(skins.Length==0||skins.Any(s=>s.sharedMesh==null||s.sharedMesh.vertexCount==0||s.bones.Length==0||s.bones.Any(b=>b==null)))
                    throw new InvalidOperationException("Missing character geometry or skeleton: "+path);
                var animator=model.GetComponent<Animator>();
                if(animator==null||animator.avatar==null||!animator.avatar.isValid)
                    throw new InvalidOperationException("Invalid Generic avatar: "+path);
                if(FoundationAvatar.AnatomicalForward(model.transform).sqrMagnitude<.5f)
                    throw new InvalidOperationException("Missing foot/toe orientation bones: "+path);
            }
            var controller=AssetDatabase.LoadAssetAtPath<AnimatorController>(Controller);
            if(controller==null||controller.layers.Length==0||controller.layers[0].stateMachine.defaultState==null)
                throw new InvalidOperationException("The generated locomotion controller is missing or incomplete.");
            foreach(string parameter in new[]{"Speed","Direction","Seated","Crouch","Air","MoveRequested"}.Concat(Triggers))
            {
                var actual=controller.parameters.SingleOrDefault(p=>p.name==parameter);
                var expected=parameter=="Speed"||parameter=="Direction"?AnimatorControllerParameterType.Float
                    :parameter=="Seated"||parameter=="Crouch"||parameter=="Air"||parameter=="MoveRequested"?AnimatorControllerParameterType.Bool:AnimatorControllerParameterType.Trigger;
                if(actual==null||actual.type!=expected)
                    throw new InvalidOperationException("Locomotion parameter has the wrong type or is missing: "+parameter);
                if(parameter=="Direction"&&!Near(actual.defaultFloat,1))
                    throw new InvalidOperationException("The locomotion playback direction must default to forward.");
            }
            foreach(string name in Clips)
            {
                var clip=Clip(name);
                if(!controller.animationClips.Contains(clip)||AnimationUtility.GetCurveBindings(clip).Length==0)
                    throw new InvalidOperationException("Locomotion clip is not bound: "+name);
            }
            var machine=controller.layers[0].stateMachine;
            var ground=State(machine,"Locomotion");var blend=ground.motion as BlendTree;
            if(machine.defaultState!=ground||blend==null||blend.blendType!=BlendTreeType.Simple1D
                ||blend.blendParameter!="Speed"||blend.useAutomaticThresholds||blend.children.Length!=GroundClips.Length
                ||!ground.speedParameterActive||ground.speedParameter!="Direction")
                throw new InvalidOperationException("The measured locomotion blend tree is not configured correctly.");
            float[] thresholds=GaitThresholds();
            for(int i=0;i<GroundClips.Length;i++)
            {
                var child=blend.children[i];
                if(child.motion!=Clip(GroundClips[i])||!Near(child.threshold,thresholds[i])||!Near(child.timeScale,1)||child.mirror
                    ||!Near(child.cycleOffset,LocomotionAnimationRules.CycleOffset(GroundClips[i])))
                    throw new InvalidOperationException("Locomotion speed or foot phase is incorrect: "+GroundClips[i]);
            }
            foreach(string mode in new[]{"Seated","Crouch","Air"})
            {
                var state=State(machine,mode);
                if(state.motion!=Clip(mode=="Air"?"Idle":mode)
                    ||!machine.anyStateTransitions.Any(t=>t.destinationState==state&&!t.hasExitTime&&!t.canTransitionToSelf&&t.hasFixedDuration
                        &&HasCondition(t,mode,AnimatorConditionMode.If))
                    ||!state.transitions.Any(t=>t.destinationState==ground&&!t.hasExitTime&&t.hasFixedDuration&&HasCondition(t,mode,AnimatorConditionMode.IfNot)))
                    throw new InvalidOperationException("The locomotion mode cannot be entered or left correctly: "+mode);
            }
            foreach(string name in Triggers)
            {
                var state=State(machine,name);
                if(state.motion!=Clip(name)||!ground.transitions.Any(t=>t.destinationState==state&&!t.hasExitTime&&t.hasFixedDuration
                        &&HasCondition(t,name,AnimatorConditionMode.If))
                    ||!state.transitions.Any(t=>t.destinationState==ground&&t.hasExitTime&&t.hasFixedDuration))
                    throw new InvalidOperationException("The locomotion transition is incomplete: "+name);
                bool starting=name=="Start"||name=="RunStart";
                bool stopping=name=="Stop"||name=="RunStop";
                if(!ground.transitions.Any(t=>t.destinationState==state
                    &&HasCondition(t,"MoveRequested",starting?AnimatorConditionMode.If:AnimatorConditionMode.IfNot)
                    &&(starting||stopping?HasCondition(t,"Direction",AnimatorConditionMode.Greater,0)
                        :HasCondition(t,"Speed",AnimatorConditionMode.Less,LocomotionAnimationRules.StoppedThreshold))))
                    throw new InvalidOperationException("The locomotion transition can consume a stale trigger: "+name);
                if(!state.transitions.Any(t=>t.destinationState==ground&&!t.hasExitTime&&t.hasFixedDuration
                    &&HasCondition(t,"MoveRequested",starting?AnimatorConditionMode.IfNot:AnimatorConditionMode.If)))
                    throw new InvalidOperationException("The locomotion transition cannot react to changed movement: "+name);
                if(starting&&!state.transitions.Any(t=>t.destinationState==ground&&t.hasExitTime
                    &&Near(t.offset,.5f)))
                    throw new InvalidOperationException("The start transition loses the source's matching gait phase: "+name);
            }
        }
        static AnimatorState State(AnimatorStateMachine machine,string name)
        {
            var state=machine.states.Where(s=>s.state.name==name).Select(s=>s.state).SingleOrDefault();
            if(state==null)throw new InvalidOperationException("The locomotion state is missing: "+name);
            return state;
        }
        static bool HasCondition(AnimatorStateTransition transition,string parameter,AnimatorConditionMode mode,float threshold=float.NaN)
            =>transition.conditions.Any(c=>c.parameter==parameter&&c.mode==mode
                &&(float.IsNaN(threshold)||Near(c.threshold,threshold)));
        static bool Near(float value,float expected)=>!float.IsNaN(value)&&!float.IsInfinity(value)&&Mathf.Abs(value-expected)<.0001f;
        static float[] GaitThresholds()
        {
            var data=JsonUtility.FromJson<GaitData>(File.ReadAllText("Assets/Game/Resources/BlackstoneFoundation/GaitSpeeds.json"));
            var values=data!=null?data.thresholds:null;
            if(values==null||values.Length!=GroundClips.Length||values[0]!=0)
                throw new InvalidOperationException("Measured locomotion speeds are missing or incomplete.");
            for(int i=0;i<values.Length;i++)
                if(float.IsNaN(values[i])||float.IsInfinity(values[i])||(i>0&&values[i]<=values[i-1]))
                    throw new InvalidOperationException("Measured locomotion speeds must be finite and increasing.");
            return values;
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
                    // A revision stamp does not prove that the imported subassets
                    // or inspector settings are still valid. An explicit repair
                    // must actually reimport them; EnsureReady avoids this work
                    // when their settings, geometry and controller already pass.
                    RocketboxImporter.Configure(importer,path);importer.userData=Revision;importer.SaveAndReimport();
                }
                BuildController();AssetDatabase.SaveAssets();
                ValidatePrepared();
                File.WriteAllText(Stamp,Revision);
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
            controller.AddParameter("MoveRequested",AnimatorControllerParameterType.Bool);
            foreach(string trigger in Triggers)controller.AddParameter(trigger,AnimatorControllerParameterType.Trigger);
            var parameters=controller.parameters;
            for(int i=0;i<parameters.Length;i++)if(parameters[i].name=="Direction")parameters[i].defaultFloat=1;
            controller.parameters=parameters;
            var machine=controller.layers[0].stateMachine;
            var blend=new BlendTree {name="Measured locomotion",blendType=BlendTreeType.Simple1D,blendParameter="Speed",useAutomaticThresholds=false};
            AssetDatabase.AddObjectToAsset(blend,controller);
            float[] thresholds=GaitThresholds();
            for(int i=0;i<GroundClips.Length;i++)blend.AddChild(Clip(GroundClips[i]),thresholds[i]);
            var children=blend.children;
            for(int i=0;i<children.Length;i++)children[i].cycleOffset=LocomotionAnimationRules.CycleOffset(GroundClips[i]);
            blend.children=children;
            var ground=machine.AddState("Locomotion");ground.motion=blend;ground.speedParameter="Direction";ground.speedParameterActive=true;machine.defaultState=ground;
            foreach(string mode in new[]{"Seated","Crouch","Air"})
            {
                var state=machine.AddState(mode);state.motion=Clip(mode=="Air"?"Idle":mode);
                var enter=machine.AddAnyStateTransition(state);enter.hasExitTime=false;enter.hasFixedDuration=true;enter.duration=.15f;enter.canTransitionToSelf=false;enter.AddCondition(AnimatorConditionMode.If,0,mode);
                if(mode!="Seated")enter.AddCondition(AnimatorConditionMode.IfNot,0,"Seated");
                if(mode=="Crouch")enter.AddCondition(AnimatorConditionMode.IfNot,0,"Air");
                var leave=state.AddTransition(ground);leave.hasExitTime=false;leave.hasFixedDuration=true;leave.duration=.15f;leave.AddCondition(AnimatorConditionMode.IfNot,0,mode);
            }
            foreach(string name in Triggers)
            {
                var state=machine.AddState(name);state.motion=Clip(name);
                var enter=ground.AddTransition(state);enter.hasExitTime=false;enter.hasFixedDuration=true;enter.duration=.1f;enter.AddCondition(AnimatorConditionMode.If,0,name);
                enter.AddCondition(AnimatorConditionMode.IfNot,0,"Seated");enter.AddCondition(AnimatorConditionMode.IfNot,0,"Crouch");enter.AddCondition(AnimatorConditionMode.IfNot,0,"Air");
                bool starting=name=="Start"||name=="RunStart";
                bool stopping=name=="Stop"||name=="RunStop";
                enter.AddCondition(starting?AnimatorConditionMode.If:AnimatorConditionMode.IfNot,0,"MoveRequested");
                if(starting||stopping)enter.AddCondition(AnimatorConditionMode.Greater,0,"Direction");
                else enter.AddCondition(AnimatorConditionMode.Less,LocomotionAnimationRules.StoppedThreshold,"Speed");
                var leave=state.AddTransition(ground);leave.hasExitTime=true;leave.hasFixedDuration=true;leave.exitTime=.85f;leave.duration=.12f;
                // Source start endings match the middle of the running stride.
                // Crossfade into that phase instead of cutting to phase zero.
                if(starting)leave.offset=.5f;
                var cancel=state.AddTransition(ground);cancel.hasExitTime=false;cancel.hasFixedDuration=true;cancel.duration=.1f;
                cancel.AddCondition(starting?AnimatorConditionMode.IfNot:AnimatorConditionMode.If,0,"MoveRequested");
                if(starting)
                {
                    var fast=state.AddTransition(ground);fast.hasExitTime=false;fast.hasFixedDuration=true;fast.duration=.12f;fast.offset=.5f;
                    fast.AddCondition(AnimatorConditionMode.Greater,name=="RunStart"?thresholds[4]:thresholds[2],"Speed");
                }
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
        {
            if(EditorBuildSettings.scenes.Any(s=>s.enabled&&SceneUsesFoundation(s.path)))
            {
                try{EnsureReady();ValidatePrepared();}
                catch(Exception error){throw new BuildFailedException("Alcatraz character preparation failed: "+error.Message);}
            }
        }
    }
    public sealed class FoundationImportWatcher : AssetPostprocessor
    {
        static void OnPostprocessAllAssets(string[] imported,string[] deleted,string[] moved,string[] previous)
        {if(imported.Any(RocketboxImporter.IsSource))FoundationPreparation.Schedule();}
    }
}
#endif
