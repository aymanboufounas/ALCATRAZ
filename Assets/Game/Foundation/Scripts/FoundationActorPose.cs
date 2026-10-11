using UnityEngine;
using Blackstone.Actors;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(115)]
    public sealed class FoundationActorPose : MonoBehaviour
    {
        public FoundationAvatar body;
        public PrisonActor actor;
        public Transform gangMark;
        public Transform phone,heldKnife,concealedKnife;
        Transform jaw;
        float idleOffset;
        void Start()
        {
            if(body==null||body.model==null)return;
            idleOffset=Mathf.Repeat(transform.position.x*.73f+transform.position.z*.31f,17);
            foreach(var t in body.model.GetComponentsInChildren<Transform>(true))if(t.name=="Bip01 MJaw")jaw=t;
        }
        void LateUpdate()
        {
            var fall=GetComponent<FoundationFall>();if(fall!=null&&fall.Active)return;
            if(Time.deltaTime<=0||body==null||actor==null)return;
            float t=Time.time;
            if(actor.conversationPartner!=null&&body.head!=null)
            {
                Vector3 d=actor.conversationPartner.position-body.head.position;
                float yaw=Mathf.Clamp(Vector3.SignedAngle(transform.forward,Vector3.ProjectOnPlane(d,Vector3.up),Vector3.up),-35,35);
                body.head.rotation=Quaternion.AngleAxis(yaw*.7f,Vector3.up)*body.head.rotation;
            }
            if(actor.Talking)
            {
                if(jaw!=null)jaw.rotation=Quaternion.AngleAxis(2+Mathf.Abs(Mathf.Sin(t*10))*5,transform.right)*jaw.rotation;
                if(body.head!=null)body.head.rotation=Quaternion.AngleAxis(Mathf.Sin(t*2.8f)*2,transform.right)*body.head.rotation;
            }
            ActorPose p=actor.pose;
            if(p==ActorPose.Idle&&!actor.Talking&&actor.conversationPartner==null
                &&body.movement==null&&body.MotionSpeed<.08f&&body.head!=null)
            {
                float glance=Mathf.Sin((t+idleOffset)*.19f)*5f;
                body.head.rotation=Quaternion.AngleAxis(glance,transform.up)*body.head.rotation;
            }
            Vector3 chest=transform.position+Vector3.up*(body.seated?1.05f:1.3f);
            if(p==ActorPose.Punch)
                Right(chest+transform.forward*(.35f+.34f*(.5f+.5f*Mathf.Sin(t*13))));
            else if(p==ActorPose.Cry)
            {
                Right(chest+Vector3.up*.12f+transform.forward*.17f);
                if(body.head!=null)body.head.rotation=Quaternion.AngleAxis(20+Mathf.Sin(t*8),transform.right)*body.head.rotation;
            }
            else if(p==ActorPose.HandsUp)
            {
                Right(chest+Vector3.up*.42f+transform.right*.36f);
                Left(chest+Vector3.up*.42f-transform.right*.36f);
            }
            else if(p==ActorPose.Conceal||p==ActorPose.Tattoo)
                Right(chest-Vector3.up*.3f+transform.forward*.3f-transform.right*.08f);
            else if(p==ActorPose.Cards||p==ActorPose.Read)
            {
                Right(chest-Vector3.up*.25f+transform.forward*.3f+transform.right*.12f);
                Left(chest-Vector3.up*.25f+transform.forward*.3f-transform.right*.12f);
            }
            else if(p==ActorPose.Workout)
            {
                float lift=.5f+.5f*Mathf.Sin(t*1.2f);
                Right(chest+Vector3.up*(lift*.6f-.2f)+transform.right*.35f);
                Left(chest+Vector3.up*(lift*.6f-.2f)-transform.right*.35f);
            }
            if(gangMark!=null&&body.leftForearm!=null&&body.leftHand!=null)
            {
                gangMark.position=(body.leftForearm.position+body.leftHand.position)*.5f+transform.forward*.035f;
                gangMark.rotation=Quaternion.LookRotation(transform.forward,Vector3.up)*Quaternion.Euler(90,0,0);
            }
            if(phone!=null&&phone.gameObject.activeInHierarchy&&body.leftHand!=null)
            {
                Left(chest+Vector3.up*.15f+transform.forward*.24f-transform.right*.1f);
                phone.position=body.leftHand.position;phone.rotation=Quaternion.LookRotation(transform.forward)*Quaternion.Euler(12,0,0);
            }
            FollowKnife(heldKnife);FollowKnife(concealedKnife);
        }
        void FollowKnife(Transform knife)
        {if(knife!=null&&body.rightHand!=null){knife.position=body.rightHand.position;knife.rotation=body.rightHand.rotation;}}
        void Right(Vector3 target){FoundationAvatar.Solve(body.rightArm,body.rightForearm,body.rightHand,target,-transform.right,.85f);}
        void Left(Vector3 target){FoundationAvatar.Solve(body.leftArm,body.leftForearm,body.leftHand,target,transform.right,.85f);}
    }
}
