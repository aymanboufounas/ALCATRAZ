using System;
using UnityEngine;
using DesertShift.Player;
using Blackstone.Alcatraz;
using Blackstone.Supplied;

namespace Blackstone.Foundation
{
    // Runs after the walking controller and before map recovery in LateUpdate.
    [DefaultExecutionOrder(-90),DisallowMultipleComponent]
    [RequireComponent(typeof(PlayerMovement))]
    public sealed class FoundationSwimming : MonoBehaviour
    {
        public bool IsSwimming=>player!=null&&player.IsSwimming;
        public bool IsAvailable { get; private set; }
        public float WaterLevel { get; private set; }
        public float CoastDistance { get; private set; }
        public bool NearRestrictedWater=>SwimmingRules.Warn(CoastDistance);
        public bool RestrictedWater { get; private set; }
        public event Action RestrictedCrossed;
        PlayerMovement player;
        PlayerInputHandler input;
        CharacterController controller;
        AlcatrazMap map;
        SuppliedIslandWorld world;
        SuppliedExtrasWorld annex;
        float nextCoastCheck;
        int teleportVersion;
        const int CoastDirections=16;
        const int GroundMask=1; // Authored island/shore geometry, excluding passengers and vehicles.
        readonly Collider[] clamberContacts=new Collider[32];
        static readonly float[] ClamberSteps={.45f,.7f,.9f,SwimmingRules.ClamberReach};
        void Awake()
        {player=GetComponent<PlayerMovement>();input=GetComponent<PlayerInputHandler>();controller=GetComponent<CharacterController>();}
        void Start()
        {
            map=FindFirstObjectByType<AlcatrazMap>();
            world=map!=null?map.GetComponent<SuppliedIslandWorld>():null;
            annex=map!=null?map.GetComponent<SuppliedExtrasWorld>():null;
            WaterLevel=map!=null&&map.suppliedLayout?-.15f:0;
            teleportVersion=player.TeleportVersion;
            RefreshAvailability();
        }
        void Update()
        {
            if(Time.deltaTime<=0)return;
            RefreshAvailability();
            if(player.TeleportVersion!=teleportVersion)
            {teleportVersion=player.TeleportVersion;nextCoastCheck=0;CoastDistance=0;}
            Vector3 position=transform.position;
            bool floorFound=Physics.Raycast(position+Vector3.up*.4f,Vector3.down,out var floor,2.5f,GroundMask,QueryTriggerInteraction.Ignore);
            bool swimming=SwimmingRules.ShouldSwim(IsAvailable,player.ExternalControl,player.IsSwimming,
                position.y,WaterLevel,floorFound,floorFound?floor.point.y:0);
            player.SetSwimming(swimming,WaterLevel);
            if(swimming&&input!=null&&input.CanControl&&input.JumpPressed&&input.Move.sqrMagnitude>.04f)
            {
                var camera=Camera.main;
                Vector3 direction=Quaternion.Euler(0,camera!=null?camera.transform.eulerAngles.y:transform.eulerAngles.y,0)
                    *new Vector3(input.Move.x,0,input.Move.y);
                if(TryClamber(direction)){CoastDistance=0;nextCoastCheck=0;return;}
            }
            // The boat uses ExternalControl, but still crosses the same water boundary.
            bool boating=FoundationVehicle.Active!=null&&!FoundationVehicle.Active.aircraft;
            if(!IsAvailable||(!swimming&&!boating)){CoastDistance=0;nextCoastCheck=0;return;}
            if(Time.time<nextCoastCheck||RestrictedWater)return;
            nextCoastCheck=Time.time+.35f;
            CoastDistance=MeasureDryShore(position);
            if(SwimmingRules.Restricted(CoastDistance))
            {RestrictedWater=true;RestrictedCrossed?.Invoke();}
        }
        void RefreshAvailability()
        {
            IsAvailable=map!=null&&map.isActiveAndEnabled&&(world==null||world.Ready&&!world.InsidePrison)
                &&(annex==null||!annex.Visiting)&&Mathf.Abs(transform.position.x)<600&&Mathf.Abs(transform.position.z)<600
                &&!map.IsInterior(transform.position);
        }
        public bool CanEnterWaterAt(Vector3 feet)
        {
            if(!IsAvailable||Mathf.Abs(feet.x)>600||Mathf.Abs(feet.z)>600)return false;
            bool found=Physics.Raycast(new Vector3(feet.x,140,feet.z),Vector3.down,out var floor,150,GroundMask,QueryTriggerInteraction.Ignore);
            return SwimmingRules.ShouldSwim(true,false,false,feet.y,WaterLevel,found,found?floor.point.y:0);
        }
        float MeasureDryShore(Vector3 position)
        {
            if(DryLand(position))return 0;
            // Approximate distance to the real coast, including docks, instead of
            // a rectangle unrelated to the supplied island's irregular shoreline.
            for(float radius=8;radius<=SwimmingRules.RestrictedDistance;radius+=8)
                for(int i=0;i<CoastDirections;i++)
                {
                    float angle=i*Mathf.PI*2/CoastDirections;
                    if(DryLand(position+new Vector3(Mathf.Cos(angle),0,Mathf.Sin(angle))*radius))return radius;
                }
            return SwimmingRules.RestrictedDistance+8;
        }
        bool DryLand(Vector3 point)
        {
            return Physics.Raycast(new Vector3(point.x,140,point.z),Vector3.down,out var hit,
                140-WaterLevel-.1f,GroundMask,QueryTriggerInteraction.Ignore)&&hit.normal.y>.55f;
        }
        bool TryClamber(Vector3 direction)
        {
            if(!IsAvailable||!IsSwimming||player.ExternalControl||input==null||!input.CanControl||controller==null)return false;
            direction=Vector3.ProjectOnPlane(direction,Vector3.up).normalized;
            if(direction.sqrMagnitude<.5f)return false;
            Vector3 start=transform.position;
            foreach(float reach in ClamberSteps)
            {
                Vector3 ray=start+direction*reach;ray.y=WaterLevel+1.6f;
                if(!Physics.Raycast(ray,Vector3.down,out var floor,1.6f,GroundMask,QueryTriggerInteraction.Ignore)
                    ||!SwimmingRules.CanClamberSurface(floor.point.y,WaterLevel,floor.normal.y,reach))continue;
                Vector3 target=floor.point+Vector3.up*.06f;
                Vector3 raised=new Vector3(start.x,target.y,start.z);
                // A standing capsule must clear the entire lift, then the forward
                // reach. This prevents snapping through roofs, railings or thin walls.
                if(!ClamberClear(raised)||!ClamberClear(target)||!ClamberPath(start,raised)||!ClamberPath(raised,target))continue;
                player.Teleport(target);
                return true;
            }
            return false;
        }
        bool ClamberClear(Vector3 feet)
        {
            float radius=controller.radius;
            int count=Physics.OverlapCapsuleNonAlloc(feet+Vector3.up*radius,feet+Vector3.up*(controller.height-radius),
                radius,clamberContacts,~(1<<2),QueryTriggerInteraction.Ignore);
            if(count==clamberContacts.Length)return false;
            for(int i=0;i<count;i++)if(!OwnCollider(clamberContacts[i]))return false;
            return true;
        }
        bool ClamberPath(Vector3 from,Vector3 to)
        {
            Vector3 motion=to-from;float distance=motion.magnitude;
            if(distance<.001f)return true;
            float radius=Mathf.Max(.05f,controller.radius-.01f);
            foreach(var hit in Physics.CapsuleCastAll(from+Vector3.up*controller.radius,from+Vector3.up*(controller.height-controller.radius),
                radius,motion/distance,distance,~(1<<2),QueryTriggerInteraction.Ignore))
                if(!OwnCollider(hit.collider))return false;
            return true;
        }
        bool OwnCollider(Collider shape)=>shape!=null&&(shape.transform==transform||shape.transform.IsChildOf(transform));
        public void ClearForRestart()
        {
            if(player!=null)player.SetSwimming(false,WaterLevel);
            RestrictedWater=false;CoastDistance=0;nextCoastCheck=0;
        }
        void OnDisable(){ClearForRestart();}
    }
}
