using UnityEngine;
using DesertShift.Player;
using Blackstone.Foundation;

namespace Blackstone.Actors
{
    // NPC roots have no CharacterController gravity. Keep both stationary and
    // walking actors on a local floor without moving them between prison tiers.
    [DefaultExecutionOrder(95)]
    public sealed class ActorGrounding : MonoBehaviour
    {
        Vector3 localFeet;
        float nextCheck;
        PrisonActor actor;
        bool isPlayer;
        public Vector3 Feet => transform.TransformPoint(localFeet);
        public bool ShouldStandOnFloor
        {
            get
            {
                if(isPlayer)return false;
                if(actor!=null&&(actor.Suspended||actor.Talking||SeatedOrSleeping(actor.pose)))return false;
                var avatar=GetComponent<FoundationAvatar>();if(avatar!=null&&avatar.seated)return false;
                var fall=GetComponent<FoundationFall>();if(fall!=null&&fall.Recovering)return false;
                var damage=GetComponent<FoundationDamageable>();if(damage!=null&&damage.Dead)return false;
                var body=GetComponent<Rigidbody>();return body==null||body.isKinematic;
            }
        }
        public bool IsSupported => TrySupport(transform,Feet,.15f,.15f,true,out _);

        void Awake()
        {
            actor=GetComponent<PrisonActor>();
            isPlayer=GetComponentInParent<PlayerMovement>()!=null;
        }
        public void SetFeetPosition(Vector3 worldFeet)
        {localFeet=transform.InverseTransformPoint(worldFeet);}
        void Start()
        {Physics.SyncTransforms();GroundNow();}
        void Update()
        {
            if(Time.deltaTime<=0||Time.time<nextCheck)return;
            nextCheck=Time.time+.5f;GroundNow();
        }
        public bool GroundNow()
        {
            if(!ShouldStandOnFloor)return false;
            // Bounded recovery repairs modest buried/floating placement. It must
            // never choose a roof or another gallery several metres above.
            if(!TrySupport(transform,Feet,1.1f,1.1f,true,out var grounded))return false;
            transform.position+=grounded-Feet;
            return true;
        }
        static bool SeatedOrSleeping(ActorPose pose)
        {return pose==ActorPose.SeatedTalk||pose==ActorPose.Cards||pose==ActorPose.Read||pose==ActorPose.Sleep;}

        public static bool TryStep(Transform owner,Vector3 wanted,out Vector3 supported)
        {return TrySupport(owner,wanted,.35f,.35f,true,out supported);}

        public static bool TrySupport(Transform owner,Vector3 feet,float maxRise,float maxDrop,
            bool standing,out Vector3 supported)
        {
            supported=feet;
            float closest=float.PositiveInfinity;bool found=false;
            // All hits are needed: an NPC may be just below a floor, and a
            // nearby bench/ceiling must not hide the correct supporting floor.
            var hits=Physics.RaycastAll(feet+Vector3.up*(maxRise+.06f),Vector3.down,
                maxRise+maxDrop+.12f,1,QueryTriggerInteraction.Ignore);
            foreach(var hit in hits)
            {
                if(hit.collider==null||hit.collider.transform==owner||hit.collider.transform.IsChildOf(owner)
                    ||hit.normal.y<.65f)continue;
                float rise=hit.point.y-feet.y;
                if(rise>maxRise||rise< -maxDrop)continue;
                Vector3 candidate=new Vector3(feet.x,hit.point.y+.025f,feet.z);
                float distance=Mathf.Abs(rise);
                if(distance>=closest)continue;
                closest=distance;supported=candidate;found=true;
            }
            // A blocked floor cannot be replaced by the top of the furniture
            // blocking it; that would lift a standing inmate onto a table.
            return found&&(!standing||StandingRoom(owner,supported));
        }
        static bool StandingRoom(Transform owner,Vector3 feet)
        {
            foreach(var collider in Physics.OverlapCapsule(feet+Vector3.up*.35f,
                feet+Vector3.up*1.5f,.23f,1,QueryTriggerInteraction.Ignore))
                if(collider.transform!=owner&&!collider.transform.IsChildOf(owner))return false;
            return true;
        }
    }
}
