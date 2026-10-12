using UnityEngine;
using DesertShift.Player;
using Blackstone.Alcatraz;
using Blackstone.Foundation;

namespace Blackstone.Supplied
{
    public sealed class SuppliedWarehouse : MonoBehaviour
    {
        public bool Inside { get; private set; }
        SuppliedExtrasWorld annex;PlayerMovement player;PlayerInputHandler input;Renderer[] doors;
        Vector3 outside;Quaternion outsideRotation;float nextInteraction,blockedUntil;
        const int FloorMask=~((1<<8)|(1<<10));
        void Start()
        {
            annex=GetComponentInParent<SuppliedExtrasWorld>();player=FindFirstObjectByType<PlayerMovement>();input=player!=null?player.GetComponent<PlayerInputHandler>():null;
            var found=new System.Collections.Generic.List<Renderer>();foreach(var r in GetComponentsInChildren<Renderer>())if(r.name.StartsWith("Warehouse_M9_")||r.name.StartsWith("Warehouse_M10_"))found.Add(r);doors=found.ToArray();
        }
        Renderer NearbyDoor()
        {
            if(doors==null||player==null)return null;Renderer nearest=null;float distance=2.3f;
            foreach(var door in doors){var delta=door.bounds.center-player.transform.position;delta.y=0;if(delta.magnitude<distance){distance=delta.magnitude;nearest=door;}}return nearest;
        }
        static bool StandingPosition(Vector3 candidate,out Vector3 position)
        {
            position=candidate;if(!Physics.Raycast(candidate+Vector3.up*.5f,Vector3.down,out var floor,1.2f,FloorMask,QueryTriggerInteraction.Ignore)||floor.normal.y<.6f)return false;
            position=floor.point+Vector3.up*.03f;return !Physics.CheckCapsule(position+Vector3.up*.35f,position+Vector3.up*1.55f,.24f,FloorMask,QueryTriggerInteraction.Ignore);
        }
        void Update()
        {
            if(annex==null||!annex.Visiting){Inside=false;return;}
            if(player==null||input==null||!input.CanControl||player.ExternalControl||Time.deltaTime<=0||Time.time<nextInteraction)return;
            var door=NearbyDoor();if(door==null||!input.InteractPressed)return;
            Vector3 candidate=Inside?outside:new Vector3(door.bounds.center.x+1.3f,SuppliedExtrasWorld.Origin.y+.08f,door.bounds.center.z);
            if(!StandingPosition(candidate,out var destination)){blockedUntil=Time.time+2;return;}
            if(!Inside){outside=player.transform.position;outsideRotation=player.transform.rotation;}
            player.Teleport(destination);player.transform.rotation=Inside?outsideRotation:Quaternion.LookRotation(Vector3.right);Inside=!Inside;nextInteraction=Time.time+.4f;
            var map=annex.GetComponent<AlcatrazMap>();if(map!=null)map.SetSafePosition(destination);var camera=FindFirstObjectByType<FoundationCamera>();if(camera!=null)camera.SnapToPlayer();
        }
        void OnGUI()
        {
            if(annex==null||!annex.Visiting||player==null||input==null||!input.CanControl||player.ExternalControl)return;
            if(NearbyDoor()!=null)GUI.Box(new Rect(Screen.width/2-210,Screen.height-150,420,45),Time.time<blockedUntil?"DOORWAY OBSTRUCTED":Inside?"E / X   LEAVE WAREHOUSE":"E / X   ENTER WAREHOUSE");
        }
    }
}
