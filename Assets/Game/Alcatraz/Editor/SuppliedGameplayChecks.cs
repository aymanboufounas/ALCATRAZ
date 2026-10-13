#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using DesertShift.Player;
using Blackstone.Foundation;
using Blackstone.Supplied;

namespace Blackstone.Alcatraz.Editor
{
    public static class SuppliedGameplayChecks
    {
        static int checks;
        static void Check(bool condition,string name)
        {if(!condition)throw new InvalidOperationException("Supplied gameplay: "+name);checks++;}
        static void Supported(PlayerMovement player,string place)
        {
            Physics.SyncTransforms();
            Check(Physics.Raycast(player.transform.position+Vector3.up*.4f,Vector3.down,out var floor,.75f,1,QueryTriggerInteraction.Ignore)
                &&floor.normal.y>.65f,place+" has supporting floor");
            Check(!Physics.CheckCapsule(player.transform.position+Vector3.up*.35f,player.transform.position+Vector3.up*1.5f,
                .23f,1,QueryTriggerInteraction.Ignore),place+" has clear standing space");
        }
        [MenuItem("Alcatraz/Validate Supplied Gameplay (Play Mode)",priority=22)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying){Debug.LogError("Enter Play Mode on the supplied island first.");return;}
            var world=UnityEngine.Object.FindFirstObjectByType<SuppliedIslandWorld>();
            var foundation=UnityEngine.Object.FindFirstObjectByType<FoundationBootstrap>();
            if(world==null||!world.Ready||foundation==null||foundation.Status!="Ready")
                throw new InvalidOperationException("Wait until the supplied island and character foundation are Ready.");
            var player=foundation.Player;Vector3 original=player.transform.position;Quaternion rotation=player.transform.rotation;
            if(FoundationVehicle.Active!=null||player.ExternalControl)
                throw new InvalidOperationException("Leave the vehicle or seated activity before validating supplied gameplay.");
            bool inside=world.InsidePrison;var equipment=foundation.PlayerEquipment;checks=0;
            try
            {
                Check(SceneManager.GetActiveScene().name=="SC_AlcatrazSuppliedIsland","correct default scene");
                foreach(string name in new[]{"Island","Police","Dog","Helmet","Vest","Helicopter","House","Pistol10mm","Revolver"})
                    Check(SuppliedModel.Load(name)!=null,"native or prepared "+name);
                var avatar=player.GetComponent<FoundationAvatar>();
                Check(avatar!=null&&Vector3.Dot(FoundationAvatar.AnatomicalForward(avatar.model),player.transform.forward)>.65f,"visible character faces controller forward");
                world.VisitHelipad();Supported(player,"Courtyard spawn");
                var helicopter=GameObject.Find("Supplied Helicopter");
                Check(helicopter!=null&&helicopter.GetComponentsInChildren<Renderer>().Length>0,"helicopter has renderable geometry");
                Check(Vector3.Distance(player.transform.position,world.Helipad.position)<13,"helicopter is beside the spawn");
                var cockpit=NamedRenderer(helicopter,"vidrio");
                Check(cockpit!=null&&cockpit.sharedMaterial.GetFloat("_Surface")==1&&cockpit.sharedMaterial.color.a<.5f,
                    "cockpit uses transparent glass");
                var vehicle=helicopter.GetComponentInParent<FoundationVehicle>();
                Check(vehicle!=null&&vehicle.rotor!=null&&vehicle.tailRotor!=null,"both helicopter rotors are connected");
                Check(Vector3.ProjectOnPlane(vehicle.transform.position-cockpit.bounds.center,Vector3.up).sqrMagnitude<.00001f,
                    "vehicle seat/camera origin is aligned with cockpit");
                const BindingFlags privateInstance=BindingFlags.Instance|BindingFlags.NonPublic;
                try
                {
                    typeof(FoundationVehicle).GetMethod("Board",privateInstance).Invoke(vehicle,null);
                    float target=(float)typeof(FoundationVehicle).GetField("targetHeight",privateInstance).GetValue(vehicle);
                    Check(Mathf.Abs(target-vehicle.transform.position.y)<.0001f,"boarding does not command automatic takeoff");
                }
                finally { if(FoundationVehicle.Active==vehicle)typeof(FoundationVehicle).GetMethod("Release",privateInstance).Invoke(vehicle,null); }
                var guard=GameObject.Find("Supplied Police");var head=NamedRenderer(guard,"policeman_head");
                Check(head!=null,"officer has the supplied head mesh");
                var helmet=guard.transform.Find("Helmet socket");var vest=guard.transform.Find("Vest socket");
                Check(helmet!=null&&Mathf.Abs(helmet.position.x-head.bounds.center.x)<.001f&&Mathf.Abs(helmet.position.z-head.bounds.center.z)<.001f,
                    "helmet is centered on the officer's head");
                Check(vest!=null&&Quaternion.Angle(vest.localRotation,Quaternion.Euler(0,180,0))<.1f,
                    "vest faces the same direction as the officer");
                world.EnterCellhouse();Check(world.InsidePrison,"enter cellhouse");Supported(player,"Cellhouse entry");
                Check(foundation.PlayerEquipment==equipment,"equipment survives entry");
                world.VisitCellhouse();Check(!world.InsidePrison,"return to supplied exterior");Supported(player,"Exterior entrance");
                Check(foundation.PlayerEquipment==equipment,"equipment survives return");
                Debug.Log("Supplied gameplay passed: "+checks+" checks using the loaded assets and Unity colliders. Walking/running visual review and a player build are still required.");
            }
            finally
            {
                if(inside)world.EnterCellhouse();else world.VisitHelipad();
                player.Teleport(original);player.transform.rotation=rotation;
                world.GetComponent<AlcatrazMap>().SetSafePosition(original);
                if(foundation.CameraRig!=null)foundation.CameraRig.SnapToPlayer();Physics.SyncTransforms();
            }
        }
        static Renderer NamedRenderer(GameObject model,string name)
        {if(model!=null)foreach(var r in model.GetComponentsInChildren<Renderer>())if(r.name==name)return r;return null;}
    }
}
#endif
