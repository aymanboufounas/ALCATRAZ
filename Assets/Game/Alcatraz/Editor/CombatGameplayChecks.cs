#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using Blackstone.Foundation;
using DesertShift.Player;

namespace Blackstone.Alcatraz.Editor
{
    public static class CombatGameplayChecks
    {
        const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        static int checks;
        static void Check(bool ok,string name){checks++;if(!ok)throw new InvalidOperationException("Combat regression: "+name);}
        static void Invoke(object target,string name){target.GetType().GetMethod(name,Private).Invoke(target,null);}
        static void Set(object target,string name,object value){target.GetType().GetField(name,Private).SetValue(target,value);}
        [MenuItem("Alcatraz/Validate Shooting Knife and Punches (Play Mode)",priority=24)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying||Time.deltaTime<=0){Debug.LogError("Resume Play Mode before running combat checks.");return;}
            var root=new GameObject("Temporary combat fixture");root.hideFlags=HideFlags.HideAndDontSave;
            var oldCamera=Camera.main;bool oldEnabled=oldCamera!=null&&oldCamera.enabled;
            float oldTime=Time.timeScale;var oldLock=Cursor.lockState;bool oldCursor=Cursor.visible;
            Vector3 origin=new Vector3(10000,0,10000);checks=0;
            try
            {
                if(oldCamera!=null)oldCamera.enabled=false;
                var cameraObject=new GameObject("Combat test camera");cameraObject.transform.SetParent(root.transform);
                cameraObject.tag="MainCamera";cameraObject.transform.position=origin+Vector3.up*1.2f;cameraObject.AddComponent<Camera>();
                var hero=new GameObject("Combat test player");hero.transform.SetParent(root.transform);hero.transform.position=origin;hero.layer=8;
                var body=hero.AddComponent<CapsuleCollider>();body.center=Vector3.up*.89f;body.height=1.78f;body.radius=.23f;
                var gear=GameObject.CreatePrimitive(PrimitiveType.Cube);gear.name="Shooter's own equipment collider";gear.transform.SetParent(hero.transform,false);
                gear.transform.localPosition=new Vector3(0,1.2f,.5f);gear.transform.localScale=Vector3.one*.15f;
                var weapons=hero.AddComponent<FoundationWeapons>();weapons.avatar=hero.AddComponent<FoundationAvatar>();Invoke(weapons,"Start");
                var target=GameObject.CreatePrimitive(PrimitiveType.Cube);target.transform.SetParent(root.transform);
                target.layer=8; // Real cellhouse NPC capsules share this layer with the prisoner.
                target.transform.position=origin+new Vector3(0,1,4);target.transform.localScale=new Vector3(1,2,1);
                var health=target.AddComponent<FoundationDamageable>();
                Physics.SyncTransforms();weapons.State.Equip(Equipment.Pistol);Invoke(weapons,"Fire");
                Check(health.Health==66&&weapons.Hits==1,"pistol hits a layer-8 NPC while ignoring the shooter's body and equipment");
                var wall=GameObject.CreatePrimitive(PrimitiveType.Cube);wall.transform.SetParent(root.transform);
                wall.transform.position=origin+new Vector3(0,1,2);wall.transform.localScale=new Vector3(2,2,.2f);Physics.SyncTransforms();
                Invoke(weapons,"Fire");Check(health.Health==66,"wall blocks shooting damage");
                UnityEngine.Object.DestroyImmediate(wall);target.transform.position=origin+new Vector3(0,1,.6f);Physics.SyncTransforms();
                weapons.State.Equip(Equipment.Knife);Invoke(weapons,"MeleeContact");
                Check(health.Health==31,"knife registers close initial-overlap contact on a layer-8 NPC");
                target.transform.position=origin+new Vector3(0,1,4);
                var reachTarget=GameObject.CreatePrimitive(PrimitiveType.Cube);reachTarget.transform.SetParent(root.transform);
                reachTarget.layer=8;reachTarget.transform.position=origin+new Vector3(0,1.2f,1.4f);reachTarget.transform.localScale=new Vector3(.4f,1,.3f);
                var reachHealth=reachTarget.AddComponent<FoundationDamageable>();Physics.SyncTransforms();
                Invoke(weapons,"MeleeContact");Check(reachHealth.Health==65,"knife sweep hits a layer-8 NPC beyond the initial overlap and ignores own equipment");
                wall=GameObject.CreatePrimitive(PrimitiveType.Cube);wall.transform.SetParent(root.transform);
                wall.transform.position=origin+new Vector3(0,1.2f,.8f);wall.transform.localScale=new Vector3(2,2,.1f);Physics.SyncTransforms();
                Invoke(weapons,"MeleeContact");Check(reachHealth.Health==65,"nearest wall blocks knife damage to an NPC behind it");
                UnityEngine.Object.DestroyImmediate(wall);UnityEngine.Object.DestroyImmediate(reachTarget);
                Invoke(weapons,"Melee");Check(health.Health==31,"knife windup does not damage before contact");
                Invoke(weapons,"Update");
                Check(!(bool)typeof(FoundationWeapons).GetField("meleePending",Private).GetValue(weapons)&&health.Health==31,
                    "blocked input cancels pending knife contact");
                Check(health.Damage(100,target.transform.position,Vector3.forward*3)&&health.Dead,"lethal damage downs an unrigged NPC");
                Check(!health.Damage(1,target.transform.position,Vector3.zero),"downed NPC cannot be damaged twice");
                var boxerObject=new GameObject("Punch test actor");boxerObject.transform.SetParent(root.transform);boxerObject.transform.position=origin+Vector3.right*10;
                var avatar=boxerObject.AddComponent<FoundationAvatar>();avatar.animator=boxerObject.AddComponent<Animator>();
                var boxing=boxerObject.AddComponent<FoundationBoxing>();Invoke(boxing,"Start");
                typeof(FoundationBoxing).GetProperty("Stamina").GetSetMethod(true).Invoke(boxing,new object[]{15f});
                Set(boxing,"started",Time.time);Set(boxing,"nextAttack",Time.time-1);Set(boxing,"combo",0);boxing.Punch();
                Check(boxing.Stamina==15,"cross cannot spend unavailable stamina");
                typeof(FoundationBoxing).GetProperty("Stamina").GetSetMethod(true).Invoke(boxing,new object[]{100f});
                Set(boxing,"started",-10f);boxing.Punch();Check(boxing.Stamina==88,"first punch is a jab with the correct cost");
                avatar.seated=true;Invoke(boxing,"Update");
                Check((bool)typeof(FoundationBoxing).GetField("connected",Private).GetValue(boxing),"seating cancels pending punch contact");
                var movement=hero.AddComponent<PlayerMovement>();movement.enabled=false;
                var input=hero.GetComponent<PlayerInputHandler>();input.enabled=false;input.Capture(true);input.SetGameplayBlocked(false);
                weapons.input=input;weapons.avatar.movement=movement;
                var held=new GameObject("Held weapon visibility fixture");held.transform.SetParent(hero.transform,false);Set(weapons,"held",held.transform);
                movement.SetSwimming(true,-.15f);Invoke(weapons,"Melee");Invoke(weapons,"Update");
                Check(!held.activeSelf&&!(bool)typeof(FoundationWeapons).GetField("meleePending",Private).GetValue(weapons),"swimming hides the equipped weapon and cancels a pending knife strike");
                movement.SetSwimming(false,-.15f);Invoke(weapons,"UpdateHeldVisibility");
                Check(held.activeSelf,"leaving the water restores the equipped weapon model");
                var seatedObject=new GameObject("Seated NPC damage fixture");seatedObject.transform.SetParent(root.transform);
                seatedObject.transform.position=origin+Vector3.right*20;
                var seatedAvatar=seatedObject.AddComponent<FoundationAvatar>();seatedAvatar.animator=seatedObject.AddComponent<Animator>();seatedAvatar.seated=true;
                var seatedHealth=seatedObject.AddComponent<FoundationDamageable>();var seatedBoxer=seatedObject.AddComponent<FoundationBoxing>();Invoke(seatedBoxer,"Start");
                bool seatedHit=(bool)typeof(FoundationBoxing).GetMethod("Receive",Private).Invoke(seatedBoxer,new object[]{boxing,9f});
                Check(seatedHit&&seatedHealth.Health==91,"seated NPCs can receive punches even though they cannot attack");
                Debug.Log("Combat fixture passed: "+checks+" assertions using actual impact methods and Unity colliders. Visual attack timing still requires a gameplay review.");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);if(oldCamera!=null)oldCamera.enabled=oldEnabled;Physics.SyncTransforms();
                Time.timeScale=oldTime;Cursor.lockState=oldLock;Cursor.visible=oldCursor;
            }
        }
    }
}
#endif
