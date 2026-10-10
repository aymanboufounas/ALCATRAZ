#if UNITY_EDITOR
using System;
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
            bool inside=world.InsidePrison;var equipment=foundation.PlayerEquipment;checks=0;
            try
            {
                Check(SceneManager.GetActiveScene().name=="SC_AlcatrazSuppliedIsland","correct default scene");
                foreach(string name in new[]{"Island","Police","Dog","Helmet","Vest","Helicopter","House","Pistol10mm","Revolver"})
                    Check(Resources.Load<GameObject>("AlcatrazSupplied/Prepared/"+name)!=null,"prepared "+name);
                var avatar=player.GetComponent<FoundationAvatar>();
                Check(avatar!=null&&Vector3.Dot(FoundationAvatar.AnatomicalForward(avatar.model),player.transform.forward)>.65f,"visible character faces controller forward");
                world.VisitHelipad();Supported(player,"Courtyard spawn");
                var helicopter=GameObject.Find("Supplied Helicopter");
                Check(helicopter!=null&&helicopter.GetComponentsInChildren<Renderer>().Length>0,"helicopter has renderable geometry");
                Check(Vector3.Distance(player.transform.position,world.Helipad.position)<13,"helicopter is beside the spawn");
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
    }
}
#endif
