#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using Blackstone.Actors;
using Blackstone.Foundation;
using Blackstone.Foundation.Editor;
using Blackstone.Supplied;

namespace Blackstone.Alcatraz.Editor
{
    // Runs against the real imported player and actors after startup/scene loads.
    // Isolated regression fixtures remain an explicit action during gameplay.
    [InitializeOnLoad]
    public static class LiveSceneVerification
    {
        [Serializable] public sealed class Report
        {
            public string scene, checkedUtc, foundationStatus;
            public bool passed;
            public float cameraDistance;
            public int standingActorsChecked, posedActorsSkipped, dogsChecked;
            public string[] errors, suitesPassed, suitesSkipped;
        }
        static bool pending;
        static bool wasControllable;
        static int teleportVersion=-1;
        static double checkAt;
        static LiveSceneVerification()
        {
            EditorApplication.playModeStateChanged+=state=>
            {
                if(state==PlayModeStateChange.EnteredPlayMode)Schedule();
                else if(state==PlayModeStateChange.ExitingPlayMode){pending=false;wasControllable=false;teleportVersion=-1;}
            };
            SceneManager.sceneLoaded+=(scene,mode)=>Schedule();
            EditorApplication.update+=Update;
            if(EditorApplication.isPlaying)Schedule();
        }
        static void Schedule(){pending=true;checkAt=EditorApplication.timeSinceStartup+1;}
        static void Update()
        {
            if(!EditorApplication.isPlaying||EditorApplication.isCompiling)return;
            var foundation=UnityEngine.Object.FindFirstObjectByType<FoundationBootstrap>();
            bool controllable=foundation!=null&&foundation.Input!=null&&foundation.Input.CanControl;
            int currentTeleport=foundation!=null&&foundation.Player!=null?foundation.Player.TeleportVersion:-1;
            if(controllable&&!wasControllable||currentTeleport!=teleportVersion&&currentTeleport>=0)Schedule();
            wasControllable=controllable;teleportVersion=currentTeleport;
            if(!pending
                ||EditorApplication.timeSinceStartup<checkAt)return;
            pending=false;
            if(foundation!=null)AuditNow();
        }
        public static Report Inspect()
        {
            Physics.SyncTransforms();
            var errors=new List<string>(ThirdPersonSceneChecks.ValidateCurrentScene());
            var foundation=UnityEngine.Object.FindFirstObjectByType<FoundationBootstrap>();
            var report=new Report {scene=SceneManager.GetActiveScene().name,checkedUtc=DateTime.UtcNow.ToString("o"),
                foundationStatus=foundation!=null?foundation.Status:"Missing foundation",
                cameraDistance=foundation!=null&&foundation.CameraRig!=null?foundation.CameraRig.CurrentDistance:0};
            if(foundation!=null&&foundation.Player!=null)
            {
                var player=foundation.Player;
                if(player.GetComponent<FoundationDamageable>()==null)errors.Add("The prisoner has no shared combat health.");
                if(player.GetComponent<FoundationPlayerVitals>()==null)errors.Add("The prisoner has no death/restart controller.");
                if(player.GetComponent<FoundationSwimming>()==null)errors.Add("The prisoner has no swimming controller.");
                if(!foundation.storyMode&&foundation.PlayerEquipment==null)errors.Add("Exploration equipment is unavailable.");
            }
            if(PrisonPauseMenu.Sections.Length!=10)errors.Add("The expected ten pause sections are unavailable.");
            foreach(var actor in UnityEngine.Object.FindObjectsByType<PrisonActor>(FindObjectsSortMode.None))
                if(actor.GetComponentInParent<DesertShift.Player.PlayerMovement>()==null&&actor.GetComponent<ActorGrounding>()==null)
                    errors.Add("NPC has no floor-placement controller: "+actor.displayName);
            foreach(var ground in UnityEngine.Object.FindObjectsByType<ActorGrounding>(FindObjectsSortMode.None))
            {
                if(!ground.ShouldStandOnFloor){report.posedActorsSkipped++;continue;}
                report.standingActorsChecked++;
                if(!ground.IsSupported)errors.Add("NPC has no clear supporting floor: "+ground.name+" at "+ground.Feet.ToString("F2"));
                var avatar=ground.GetComponent<FoundationAvatar>();
                if(avatar!=null&&avatar.model!=null)
                {
                    try
                    {
                        float feetOffset=SuppliedModel.Bounds(avatar.model.gameObject).min.y-ground.Feet.y;
                        if(feetOffset<-.25f||feetOffset>.5f)
                            errors.Add("NPC mesh feet do not match its floor: "+ground.name+" (offset "+feetOffset.ToString("F2")+" m).");
                    }
                    catch(Exception error){errors.Add("Cannot inspect NPC mesh feet: "+ground.name+" / "+error.Message);}
                }
            }
            foreach(var dog in UnityEngine.Object.FindObjectsByType<SuppliedDogPatrol>(FindObjectsSortMode.None))
            {
                report.dogsChecked++;
                if(!Physics.Raycast(dog.transform.position+Vector3.up*.3f,Vector3.down,out var floor,.5f,1,QueryTriggerInteraction.Ignore)
                    ||floor.normal.y<.65f)errors.Add("Police dog has no supporting floor at "+dog.transform.position.ToString("F2"));
            }
            report.errors=errors.ToArray();report.passed=errors.Count==0;
            report.suitesPassed=report.suitesSkipped=new string[0];return report;
        }
        [MenuItem("Alcatraz/Check Loaded Player and All NPCs (Play Mode)",priority=28)]
        public static void AuditNow()
        {
            if(!EditorApplication.isPlaying){Debug.LogError("Enter Play Mode to inspect the loaded player and NPCs.");return;}
            Publish(Inspect());
        }
        [MenuItem("Alcatraz/Run All Gameplay Checks (Play Mode)",priority=29)]
        public static void RunAll()
        {
            if(!EditorApplication.isPlaying||Time.deltaTime<=0)
            {Debug.LogError("Enter the game and resume Play Mode before running gameplay checks. No tests ran.");return;}
            var foundation=UnityEngine.Object.FindFirstObjectByType<FoundationBootstrap>();
            if(foundation==null||foundation.Status!="Ready"||foundation.Player==null||foundation.Player.ExternalControl
                ||foundation.Player.IsSwimming||!foundation.Player.Grounded
                ||foundation.Player.GetComponent<FoundationPlayerVitals>()?.Failed==true
                ||foundation.CameraRig!=null&&foundation.CameraRig.story!=null&&foundation.CameraRig.story.Busy)
            {Debug.LogError("Wait for character setup and leave the current activity or cinematic before running checks. No tests ran.");return;}
            var passed=new List<string>();var failed=new List<string>();var skipped=new List<string>();
            Action<string,Action> run=(name,action)=>
            {try{action();passed.Add(name);}catch(Exception error){failed.Add(name+": "+error.Message);Debug.LogException(error);}};
            run("Movement and third-person camera",GameplayRegressionChecks.Run);
            run("Movement braking, walls, stairs and slopes",MovementQualityChecks.Run);
            run("Imported player view recovery",PlayerViewRecoveryChecks.Run);
            run("NPC floors and patrols",NPCGroundingChecks.Run);
            run("Shooting, knife and punches",CombatGameplayChecks.Run);
            run("Swimming, shore exits and restricted coast",SwimmingGameplayChecks.Run);
            run("Player health and checkpoint guards",PlayerVitalsChecks.Run);
            run("HUD layout",HudLayoutChecks.Run);
            run("Graphics presets and pipeline lifecycle",GraphicsGameplayChecks.Run);
            var world=UnityEngine.Object.FindFirstObjectByType<SuppliedIslandWorld>();
            var annex=UnityEngine.Object.FindFirstObjectByType<SuppliedExtrasWorld>();
            if(world!=null&&(annex==null||!annex.Visiting))run("Supplied island travel, equipment and vehicles",SuppliedGameplayChecks.Run);
            else skipped.Add("Supplied island travel: requires the supplied island outside the annex.");
            var report=Inspect();
            var errors=new List<string>(report.errors);errors.AddRange(failed);
            report.errors=errors.ToArray();report.passed=errors.Count==0;
            report.suitesPassed=passed.ToArray();report.suitesSkipped=skipped.ToArray();Publish(report);
        }
        static void Publish(Report report)
        {
            string directory=Path.Combine("Library","AlcatrazVerification");
            string path=Path.Combine(directory,"LatestSceneChecks.json");
            try{Directory.CreateDirectory(directory);File.WriteAllText(path,JsonUtility.ToJson(report,true));}
            catch(Exception error){Debug.LogError("Could not save loaded-scene checks: "+error.Message);}
            string message="Alcatraz loaded-scene checks "+(report.passed?"PASS":"FAIL")+": "+report.scene
                +" / "+report.standingActorsChecked+" standing actors, "+report.posedActorsSkipped+" players/posed actors skipped"
                +" / camera "+report.cameraDistance.ToString("F2")+" m. Report: "+path;
            if(report.passed)Debug.Log(message);
            else Debug.LogError(message+"\n"+string.Join("\n",report.errors));
        }
    }
}
#endif
