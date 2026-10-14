#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using Blackstone.Foundation;

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
            Vector3 origin=new Vector3(10000,0,10000);checks=0;
            try
            {
                if(oldCamera!=null)oldCamera.enabled=false;
                var cameraObject=new GameObject("Combat test camera");cameraObject.transform.SetParent(root.transform);
                cameraObject.tag="MainCamera";cameraObject.transform.position=origin+Vector3.up*1.2f;cameraObject.AddComponent<Camera>();
                var hero=new GameObject("Combat test player");hero.transform.SetParent(root.transform);hero.transform.position=origin;hero.layer=8;
                var weapons=hero.AddComponent<FoundationWeapons>();weapons.avatar=hero.AddComponent<FoundationAvatar>();Invoke(weapons,"Start");
                var target=GameObject.CreatePrimitive(PrimitiveType.Cube);target.transform.SetParent(root.transform);
                target.transform.position=origin+new Vector3(0,1,4);target.transform.localScale=new Vector3(1,2,1);
                var health=target.AddComponent<FoundationDamageable>();
                Physics.SyncTransforms();weapons.State.Equip(Equipment.Pistol);Invoke(weapons,"Fire");
                Check(health.Health==66&&weapons.Hits==1,"pistol impact damages an NPC and gives a hit marker");
                var wall=GameObject.CreatePrimitive(PrimitiveType.Cube);wall.transform.SetParent(root.transform);
                wall.transform.position=origin+new Vector3(0,1,2);wall.transform.localScale=new Vector3(2,2,.2f);Physics.SyncTransforms();
                Invoke(weapons,"Fire");Check(health.Health==66,"wall blocks shooting damage");
                UnityEngine.Object.DestroyImmediate(wall);target.transform.position=origin+new Vector3(0,1,.6f);Physics.SyncTransforms();
                weapons.State.Equip(Equipment.Knife);Invoke(weapons,"MeleeContact");
                Check(health.Health==31,"knife registers close initial-overlap contact");
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
                Debug.Log("Combat fixture passed: "+checks+" assertions using actual impact methods and Unity colliders. Visual attack timing still requires a gameplay review.");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);if(oldCamera!=null)oldCamera.enabled=oldEnabled;Physics.SyncTransforms();
            }
        }
    }
}
#endif
