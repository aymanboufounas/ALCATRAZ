#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using DesertShift.Player;
using Blackstone.Foundation;

namespace Blackstone.Alcatraz.Editor
{
    // Manual Unity-physics checks; source checks and pure rule tests cannot run these.
    public static class SwimmingGameplayChecks
    {
        const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        static int checks;
        static void Check(bool value,string label){checks++;if(!value)throw new InvalidOperationException("Swimming regression: "+label);}
        static object Invoke(object target,string method,params object[] args)=>target.GetType().GetMethod(method,Private).Invoke(target,args);
        [MenuItem("Alcatraz/Validate Swimming and Coast Boundary (Play Mode)",priority=25)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying||Time.deltaTime<=0){Debug.LogError("Resume Play Mode before running swimming checks.");return;}
            float oldTime=Time.timeScale;var oldLock=Cursor.lockState;bool oldCursor=Cursor.visible;
            var root=new GameObject("Temporary swimming fixture");root.hideFlags=HideFlags.HideAndDontSave;
            Vector3 origin=new Vector3(10000,0,10000);checks=0;
            try
            {
                var hero=new GameObject("Swimmer fixture");hero.transform.SetParent(root.transform);hero.layer=8;
                hero.transform.position=origin-Vector3.up*2;
                var controller=hero.AddComponent<CharacterController>();controller.height=1.78f;controller.center=Vector3.up*.89f;controller.radius=.25f;
                var movement=hero.AddComponent<PlayerMovement>();movement.enabled=false;
                var input=hero.GetComponent<PlayerInputHandler>();input.enabled=false;input.Capture(true);input.SetGameplayBlocked(true);
                var water=hero.AddComponent<FoundationSwimming>();water.enabled=false;
                movement.SetSwimming(true,0);
                Check(controller.enabled&&movement.IsSwimming&&!movement.ExternalControl,"swimming preserves collision control");
                Invoke(movement,"Update");
                Check(hero.transform.position.y>-2&&!movement.Grounded&&movement.AirTime==0,"buoyancy rises without falling or landing animation");
                Check(Vector3.ProjectOnPlane(hero.transform.position-origin,Vector3.up).sqrMagnitude<.000001f,"blocked input cannot paddle");
                var wall=Box(root.transform,"Solid pier wall",origin+new Vector3(0,0,1.5f),new Vector3(6,6,.2f));
                Physics.SyncTransforms();controller.Move(Vector3.forward*4);
                Check(hero.transform.position.z<origin.z+1.3f,"swimmer cannot pass through a pier wall");
                UnityEngine.Object.DestroyImmediate(wall);movement.Teleport(origin-Vector3.up*1.2f);
                Check(!movement.IsSwimming,"teleport clears water movement state");
                movement.SetSwimming(true,0);movement.SetExternalControl(true);
                Check(!movement.IsSwimming&&!controller.enabled,"boarding or ragdoll releases swimming");
                movement.SetExternalControl(false);
                var shore=Box(root.transform,"Dry shore",origin+new Vector3(12,0,0),new Vector3(8,.5f,8));
                Physics.SyncTransforms();float coast=(float)Invoke(water,"MeasureDryShore",origin);
                Check(coast<=16&&!SwimmingRules.Warn(coast),"nearby real shore keeps water unrestricted");
                coast=(float)Invoke(water,"MeasureDryShore",origin+Vector3.left*100);
                Check(SwimmingRules.Restricted(coast),"open sea beyond shore band is restricted");
                shore.layer=11;Physics.SyncTransforms();coast=(float)Invoke(water,"MeasureDryShore",origin);
                Check(SwimmingRules.Restricted(coast),"boat geometry cannot extend safe coastal water");
                movement.SetSwimming(true,0);water.ClearForRestart();
                Check(!movement.IsSwimming&&!water.RestrictedWater&&water.CoastDistance==0,"restart clears water and boundary state");
                var bank=Box(root.transform,"Low dry bank",origin+new Vector3(0,.15f,.85f),new Vector3(3,.3f,.8f));
                typeof(FoundationSwimming).GetProperty("IsAvailable").GetSetMethod(true).Invoke(water,new object[]{true});
                movement.Teleport(origin-Vector3.up*1.2f);movement.SetSwimming(true,0);input.SetGameplayBlocked(false);Physics.SyncTransforms();
                Check((bool)Invoke(water,"TryClamber",Vector3.forward)&&!movement.IsSwimming&&hero.transform.position.y>.3f,
                    "explicit surface stroke climbs a nearby clear low bank");
                movement.Teleport(origin-Vector3.up*1.2f);movement.SetSwimming(true,0);
                var railing=Box(root.transform,"Thin railing",origin+new Vector3(0,1,.35f),new Vector3(3,2,.1f));Physics.SyncTransforms();
                Check(!(bool)Invoke(water,"TryClamber",Vector3.forward)&&movement.IsSwimming,
                    "thin wall blocks the entire forward clamber path");
                UnityEngine.Object.DestroyImmediate(railing);
                var roof=Box(root.transform,"Low roof",origin+new Vector3(0,.9f,.3f),new Vector3(3,.2f,2));Physics.SyncTransforms();
                Check(!(bool)Invoke(water,"TryClamber",Vector3.forward)&&movement.IsSwimming,
                    "ceiling blocks the lift and destination standing capsule");
                UnityEngine.Object.DestroyImmediate(roof);input.SetGameplayBlocked(true);Physics.SyncTransforms();
                Check(!(bool)Invoke(water,"TryClamber",Vector3.forward),"blocked gameplay cannot initiate a clamber");
                Debug.Log("Swimming fixture passed: "+checks+" Unity-physics assertions. Review water entry, shoreline exits and swim poses in the actual island scene too.");
            }
            catch(TargetInvocationException error){Debug.LogException(error.InnerException??error);throw;}
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);Physics.SyncTransforms();
                Time.timeScale=oldTime;Cursor.lockState=oldLock;Cursor.visible=oldCursor;
            }
        }
        static GameObject Box(Transform parent,string name,Vector3 position,Vector3 size)
        {
            var box=GameObject.CreatePrimitive(PrimitiveType.Cube);box.name=name;box.transform.SetParent(parent);
            box.transform.position=position;box.transform.localScale=size;return box;
        }
    }
}
#endif
