#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using Blackstone.Actors;
using Blackstone.Foundation;
using Blackstone.Save;
using Blackstone.Story;
using DesertShift.Player;

namespace Blackstone.Alcatraz.Editor
{
    // Isolated component/serialization checks. This never calls the scene-reload countdown.
    public static class PlayerVitalsChecks
    {
        const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        static int checks;
        static void Check(bool value,string label){checks++;if(!value)throw new InvalidOperationException("Player health regression: "+label);}
        static void Set(object target,string field,object value)=>target.GetType().GetField(field,Private).SetValue(target,value);
        static void Property(object target,string property,object value)=>target.GetType().GetProperty(property).GetSetMethod(true).Invoke(target,new[]{value});
        [Serializable] sealed class LegacyExploration
        {
            public int version=1;
            public string scene;
            public Vector3 position;
            public float yaw;
            public bool interior,annex;
            public Equipment equipped;
            public int[] magazines,ammunition;
        }
        [MenuItem("Alcatraz/Validate Player Health and Restart Guards (Play Mode)",priority=26)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying||Time.deltaTime<=0){Debug.LogError("Resume Play Mode before running player health checks.");return;}
            float oldTime=Time.timeScale;var oldLock=Cursor.lockState;bool oldCursor=Cursor.visible;
            var originalScene=SceneManager.GetActiveScene();Scene checkpointScene=default;
            string checkpointPath=null;
            var pending=typeof(FoundationPlayerVitals).GetField("pendingRestart",BindingFlags.Static|BindingFlags.NonPublic);
            object oldPending=pending.GetValue(null);
            var root=new GameObject("Temporary player health fixture");root.hideFlags=HideFlags.HideAndDontSave;checks=0;
            try
            {
                var foundation=root.AddComponent<FoundationBootstrap>();foundation.enabled=false;
                var hud=root.AddComponent<FoundationHUD>();hud.enabled=false;
                var hero=new GameObject("Player health fixture");hero.transform.SetParent(root.transform);hero.layer=8;
                hero.transform.position=new Vector3(10000,0,10000);
                var controller=hero.AddComponent<CharacterController>();controller.height=1.78f;controller.center=Vector3.up*.89f;controller.radius=.25f;
                var movement=hero.AddComponent<PlayerMovement>();movement.enabled=false;
                var input=hero.GetComponent<PlayerInputHandler>();input.enabled=false;input.Capture(true);input.SetGameplayBlocked(false);
                var actor=hero.AddComponent<PrisonActor>();var agent=hero.AddComponent<FoundationAgent>();
                var health=hero.AddComponent<FoundationDamageable>();var vitals=hero.AddComponent<FoundationPlayerVitals>();vitals.enabled=false;vitals.Configure(foundation,null);
                Property(foundation,"Player",movement);Property(foundation,"Input",input);Set(hud,"foundation",foundation);
                Check(health.Health==100&&!vitals.CanTakeDamage&&!health.Damage(10,hero.transform.position,Vector3.zero),"title screen keeps the player at 100% health");
                Set(hud,"title",false);
                Check(vitals.CanTakeDamage&&health.Damage(25,hero.transform.position,Vector3.zero)&&health.Health==75&&!vitals.Failed,"active player takes nonlethal damage without failing the mission");
                input.Capture(false);
                Check(!health.Damage(10,hero.transform.position,Vector3.zero)&&health.Health==75,"pause prevents incoming damage");
                input.Capture(true);input.SetGameplayBlocked(true);
                Check(!health.Damage(10,hero.transform.position,Vector3.zero)&&health.Health==75,"cinematic or activity input block prevents incoming damage");
                input.SetGameplayBlocked(false);movement.SetExternalControl(true);
                Check(!health.Damage(10,hero.transform.position,Vector3.zero)&&health.Health==75,"external seat or ragdoll control prevents incoming damage");
                movement.SetExternalControl(false);

                // A unique empty scene namespaces exploration saves without touching user slots.
                checkpointScene=SceneManager.CreateScene("PlayerVitalsFixture_"+Guid.NewGuid().ToString("N"));
                SceneManager.SetActiveScene(checkpointScene);checkpointPath=ExplorationSave.PathName(0);
                var weapons=new WeaponState();
                var checkpoint=new ExplorationCheckpoint{scene=checkpointScene.name,position=Vector3.zero,health=42,
                    magazines=weapons.LoadedSnapshot(),ammunition=weapons.ReserveSnapshot(),equipped=Equipment.Unarmed};
                Check(ExplorationSave.Write(0,checkpoint)&&ExplorationSave.TryLoad(0,out var loaded)&&loaded.health==42
                    &&health.Restore(loaded.health)&&health.Health==42,"normal exploration checkpoint roundtrip restores saved health");
                var legacy=new LegacyExploration{scene=checkpointScene.name,position=Vector3.zero,
                    magazines=weapons.LoadedSnapshot(),ammunition=weapons.ReserveSnapshot(),equipped=Equipment.Unarmed};
                File.WriteAllText(checkpointPath,JsonUtility.ToJson(legacy));
                Check(ExplorationSave.TryLoad(0,out var migrated)&&migrated.health==100,"legacy exploration checkpoints without health remain loadable at 100%");
                checkpoint.health=0;
                string livingContents=File.ReadAllText(checkpointPath);
                Check(!ExplorationSave.Write(0,checkpoint)&&File.ReadAllText(checkpointPath)==livingContents,"dead exploration state cannot overwrite a living checkpoint");
                File.WriteAllText(checkpointPath,JsonUtility.ToJson(checkpoint));
                Check(!ExplorationSave.TryLoad(0,out var deadCheckpoint),"an explicitly dead checkpoint is rejected");
                SceneManager.SetActiveScene(originalScene);
                var valid=typeof(PrisonSave).GetMethod("Valid",BindingFlags.Static|BindingFlags.NonPublic);
                var storyCheckpoint=new PrisonCheckpoint{position=new Vector3(0,originalScene.name.StartsWith("SC_Alcatraz",StringComparison.Ordinal)?30:0,0),health=42};
                Check((bool)valid.Invoke(null,new object[]{storyCheckpoint}),"living story checkpoint with saved health is valid");
                storyCheckpoint.health=0;
                Check(!(bool)valid.Invoke(null,new object[]{storyCheckpoint}),"dead story checkpoint is rejected");

                Check(health.Damage(100,hero.transform.position,Vector3.forward)&&health.Dead&&vitals.Failed&&!input.CanControl,"zero health triggers player death and blocks controls");
                Check(actor.enabled&&agent.enabled&&controller.enabled&&hero.GetComponent<Rigidbody>()==null,"player death bypasses NPC disable and loose rigidbody handling");
                Check(!health.Damage(1,hero.transform.position,Vector3.zero),"death rejects repeated damage");
                var story=root.AddComponent<PrisonStoryDirector>();story.enabled=false;story.player=movement;story.input=input;Set(story,"sessionStarted",true);
                // Missing cinematic spawn intentionally detects any attempt to evaluate
                // checkpoint position after the failed-player guard, before any disk IO.
                Property(story,"Busy",true);
                Check(!story.SaveNow(),"failed player cannot overwrite the last story checkpoint");
                Check(!vitals.BeginFailure(PlayerFailureReason.RestrictedWater),"death cannot be replaced by a second failure reason");

                var wantedHero=new GameObject("Wanted alert fixture");wantedHero.transform.SetParent(root.transform);
                var wantedMovement=wantedHero.AddComponent<PlayerMovement>();wantedMovement.enabled=false;
                var wantedInput=wantedHero.GetComponent<PlayerInputHandler>();wantedInput.enabled=false;wantedInput.Capture(true);
                var wantedHealth=wantedHero.AddComponent<FoundationDamageable>();var wanted=wantedHero.AddComponent<FoundationPlayerVitals>();wanted.enabled=false;wanted.Configure(foundation,null);
                Check(wanted.BeginFailure(PlayerFailureReason.RestrictedWater)&&wanted.Failed&&wantedHealth.Health==100&&!wantedInput.CanControl,"restricted-water failure shows wanted status without reducing health");
                pending.SetValue(null,"PlayerVitalsFixture");
                Check(!FoundationPlayerVitals.ConsumeRestart("AnotherScene")&&FoundationPlayerVitals.ConsumeRestart("PlayerVitalsFixture")
                    &&!FoundationPlayerVitals.ConsumeRestart("PlayerVitalsFixture"),"restart handoff belongs to one scene and is consumed once");
                Debug.Log("Player health fixture passed: "+checks+" component and checkpoint assertions. Review the actual death/wanted screen and scene restart in Play Mode separately.");
            }
            catch(TargetInvocationException error){Debug.LogException(error.InnerException??error);throw;}
            finally
            {
                pending.SetValue(null,oldPending);
                SceneManager.SetActiveScene(originalScene);
                try
                {
                    UnityEngine.Object.DestroyImmediate(root);
                    if(checkpointPath!=null)foreach(string suffix in new[]{"",".bak",".tmp"})if(File.Exists(checkpointPath+suffix))File.Delete(checkpointPath+suffix);
                    if(checkpointScene.IsValid()&&checkpointScene.isLoaded)SceneManager.UnloadSceneAsync(checkpointScene);
                    Physics.SyncTransforms();
                }
                finally {Time.timeScale=oldTime;Cursor.lockState=oldLock;Cursor.visible=oldCursor;}
            }
        }
    }
}
#endif
