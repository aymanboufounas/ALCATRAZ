using UnityEngine;
using DesertShift.Environment;
using Blackstone.Actors;

namespace Blackstone.Foundation
{
    // Read the final feet after animation, grounding IK and landing/ragdoll poses.
    [DefaultExecutionOrder(160)]
    public sealed class FoundationFootsteps : MonoBehaviour
    {
        public FoundationAvatar avatar;
        readonly FootContactRules contacts=new FootContactRules();
        FoundationFall fall;
        FoundationDamageable health;
        FoundationPlayerVitals vitals;
        DesertShift.Player.PlayerInputHandler input;
        PrisonActor actor;
        bool bound, positionKnown;
        Vector3 previousPosition;
        int teleportVersion;
        void Start()
        {
            if(avatar==null)avatar=GetComponent<FoundationAvatar>();
            fall=GetComponent<FoundationFall>();health=GetComponent<FoundationDamageable>();
            vitals=GetComponent<FoundationPlayerVitals>();actor=GetComponent<PrisonActor>();
            input=GetComponent<DesertShift.Player.PlayerInputHandler>();
            bound=true;
        }
        void OnDisable(){contacts.Reset();positionKnown=false;}
        void LateUpdate()
        {
            if(Time.deltaTime<=0)return;
            if(!bound)Start();
            if(avatar==null){contacts.Reset();return;}
            var movement=avatar.movement;
            int currentTeleport=movement!=null?movement.TeleportVersion:0;
            bool teleported=positionKnown&&((transform.position-previousPosition).sqrMagnitude>1
                ||movement!=null&&currentTeleport!=teleportVersion);
            previousPosition=transform.position;teleportVersion=currentTeleport;positionKnown=true;
            if(teleported)contacts.Reset();
            bool posed=actor!=null&&(actor.Suspended||actor.pose==ActorPose.Sleep||actor.pose==ActorPose.Cards
                ||actor.pose==ActorPose.Read||actor.pose==ActorPose.SeatedTalk);
            if(avatar.seated||posed||avatar.animator==null||!avatar.animator.enabled
                ||avatar.animator.runtimeAnimatorController==null||fall!=null&&fall.Recovering
                ||health!=null&&health.Dead||vitals!=null&&vitals.Failed
                ||movement!=null&&(movement.ExternalControl||movement.IsSwimming||!movement.Grounded||input!=null&&!input.CanControl))
            {contacts.Reset();return;}
            if(movement!=null&&movement.LandedThisFrame&&!teleported)
            {
                float volume=contacts.Land(Time.frameCount,movement.LandingSpeed,Time.time);
                if(volume>0&&LandingSurface(out var floor))Play(floor,volume,Random.Range(.94f,1));
                // Both feet begin the grounded phase planted, preventing a
                // landing plus two ordinary footsteps on this same contact.
                contacts.Step(0,FootHeight(avatar.leftFoot,out _,out bool leftSupported),avatar.FootClearance(true),leftSupported,Time.time);
                contacts.Step(1,FootHeight(avatar.rightFoot,out _,out bool rightSupported),avatar.FootClearance(false),rightSupported,Time.time);
                return;
            }
            if(avatar.MotionSpeed<.15f){contacts.Reset();return;}
            Foot(0,avatar.leftFoot);Foot(1,avatar.rightFoot);
        }
        float FootHeight(Transform foot,out RaycastHit floor,out bool supported)
        {
            floor=default;
            supported=foot!=null&&Physics.Raycast(foot.position+Vector3.up*.4f,Vector3.down,out floor,
                .9f,1,QueryTriggerInteraction.Ignore)&&floor.normal.y>.55f;
            return supported?foot.position.y-floor.point.y:0;
        }
        void Foot(int index,Transform foot)
        {
            float height=FootHeight(foot,out var floor,out bool supported);
            if(!contacts.Step(index,height,avatar.FootClearance(index==0),supported,Time.time))return;
            bool player=avatar.movement!=null;
            float volume=FootContactRules.StepVolume(avatar.MotionSpeed,player,player&&avatar.movement.IsCrouching);
            Play(floor,volume,Random.Range(.97f,1.035f));
        }
        bool LandingSurface(out RaycastHit floor)
        {
            float left=FootHeight(avatar.leftFoot,out var leftFloor,out bool leftSupported);
            float right=FootHeight(avatar.rightFoot,out var rightFloor,out bool rightSupported);
            if(leftSupported||rightSupported)
            {floor=leftSupported&&(!rightSupported||left<=right)?leftFloor:rightFloor;return true;}
            return Physics.Raycast(transform.position+Vector3.up*.45f,Vector3.down,out floor,.9f,
                1,QueryTriggerInteraction.Ignore)&&floor.normal.y>.55f;
        }
        static void Play(RaycastHit floor,float volume,float pitch)
        {
            if(FoundationAudio.Instance==null||volume<=0)return;
            var tag=floor.collider.GetComponentInParent<SurfaceTag>();
            string surface=tag==null?"Concrete":tag.surface==SurfaceKind.Metal?"Metal":tag.surface==SurfaceKind.Wood?"Wood":tag.surface==SurfaceKind.Sand?"Grass":"Concrete";
            FoundationAudio.Instance.Variation(surface,floor.point+Vector3.up*.08f,volume,pitch);
        }
    }
}
