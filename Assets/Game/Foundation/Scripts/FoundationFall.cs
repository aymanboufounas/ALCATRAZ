using System.Collections.Generic;
using UnityEngine;
using DesertShift.Player;

namespace Blackstone.Foundation
{
    // Contacts drive the ragdoll; animation resumes only after finding a clear standing capsule.
    [DefaultExecutionOrder(140)]
    public sealed class FoundationFall : MonoBehaviour
    {
        public FoundationAvatar avatar;
        public bool Active { get; private set; }
        public bool Recovering=>Active||Time.time<blendUntil;
        readonly List<Rigidbody> bodies=new List<Rigidbody>();
        readonly List<Collider> colliders=new List<Collider>();
        readonly List<Transform> bones=new List<Transform>();
        Vector3[] fallenPositions; Quaternion[] fallenRotations;
        float downUntil, blendUntil; Vector3 recover;
        FoundationCamera cameraRig;
        void Start()
        {
            if(avatar==null)avatar=GetComponent<FoundationAvatar>();
            if(avatar==null||avatar.pelvis==null)return;
            Transform[] parts={avatar.pelvis,avatar.chest,avatar.head,avatar.leftArm,avatar.leftForearm,avatar.rightArm,avatar.rightForearm,
                avatar.leftThigh,avatar.leftShin,avatar.rightThigh,avatar.rightShin};
            for(int i=0;i<parts.Length;i++)
            {
                var bone=parts[i];if(bone==null)continue;
                bone.gameObject.layer=10;bones.Add(bone);
                var body=bone.gameObject.AddComponent<Rigidbody>();body.mass=i==0?15:i==1?18:5;
                body.isKinematic=true;body.interpolation=RigidbodyInterpolation.Interpolate;body.collisionDetectionMode=CollisionDetectionMode.ContinuousSpeculative;
                bodies.Add(body);
                Transform end=i==0?avatar.chest:i==1?avatar.head:i==3?avatar.leftForearm:i==4?avatar.leftHand:i==5?avatar.rightForearm:i==6?avatar.rightHand:i==7?avatar.leftShin:i==8?avatar.leftFoot:i==9?avatar.rightShin:i==10?avatar.rightFoot:null;
                Collider shape;
                if(end!=null)
                {
                    var segment=new GameObject("Ragdoll contact");segment.layer=10;segment.transform.SetParent(bone,false);
                    segment.transform.rotation=Quaternion.FromToRotation(Vector3.up,end.position-bone.position);
                    var cap=segment.AddComponent<CapsuleCollider>();float scale=Mathf.Max(.01f,Mathf.Abs(segment.transform.lossyScale.y));
                    cap.radius=(i<2?.17f:.085f)/scale;cap.height=Mathf.Max(cap.radius*2,Vector3.Distance(bone.position,end.position)/scale);cap.center=Vector3.up*cap.height*.5f;shape=cap;
                }
                else {var sphere=bone.gameObject.AddComponent<SphereCollider>();sphere.radius=.12f/Mathf.Max(.01f,Mathf.Abs(bone.lossyScale.x));shape=sphere;}
                shape.enabled=false;colliders.Add(shape);
                if(i>0)
                {
                    Rigidbody parent=null;var t=bone.parent;
                    while(t!=null&&parent==null){parent=t.GetComponent<Rigidbody>();t=t.parent;}
                    if(parent==null)parent=bodies[0];
                    var joint=bone.gameObject.AddComponent<CharacterJoint>();joint.connectedBody=parent;joint.enableProjection=true;
                    joint.lowTwistLimit=new SoftJointLimit{limit=-30};joint.highTwistLimit=new SoftJointLimit{limit=30};
                    joint.swing1Limit=new SoftJointLimit{limit=i>=3?95:40};joint.swing2Limit=new SoftJointLimit{limit=i==4||i==6||i==8||i==10?10:35};
                }
            }
            foreach(var a in colliders)foreach(var b in colliders)if(a!=b)Physics.IgnoreCollision(a,b);
            Physics.IgnoreLayerCollision(10,8,true);
            cameraRig=FindFirstObjectByType<FoundationCamera>();
        }
        void Update()
        {
            if(avatar==null||Time.deltaTime<=0)return;
            if(!Active && avatar.movement!=null && avatar.movement.LandedThisFrame && avatar.movement.LandingSpeed>10.5f)
                KnockDown(-Vector3.up*avatar.movement.LandingSpeed*.35f+transform.forward*2);
            if(!Active||Time.time<downUntil)return;
            var point=avatar.pelvis.position;
            if(Physics.Raycast(point+Vector3.up*2,Vector3.down,out var floor,6,~((1<<8)|(1<<10)),QueryTriggerInteraction.Ignore))
            {
                var candidate=floor.point+Vector3.up*.06f;
                if(!Physics.CheckCapsule(candidate+Vector3.up*.32f,candidate+Vector3.up*1.5f,.24f,~((1<<8)|(1<<10)),QueryTriggerInteraction.Ignore))recover=candidate;
                else recover=avatar.movement!=null?avatar.movement.LastSupportedPosition:transform.position;
            }
            else recover=avatar.movement!=null?avatar.movement.LastSupportedPosition:transform.position;
            fallenPositions=new Vector3[bones.Count];fallenRotations=new Quaternion[bones.Count];
            for(int i=0;i<bones.Count;i++){fallenPositions[i]=bones[i].position;fallenRotations[i]=bones[i].rotation;bodies[i].isKinematic=true;colliders[i].enabled=false;}
            transform.position=recover;
            avatar.animator.enabled=true;avatar.animator.Rebind();avatar.animator.Update(0);
            Active=false;blendUntil=Time.time+.85f;
            if(cameraRig!=null&&cameraRig.FollowOverride==avatar.pelvis)cameraRig.FollowOverride=null;
        }
        public void KnockDown(Vector3 impulse)
        {
            if(Active||bodies.Count==0||Time.time<blendUntil)return;
            Active=true;downUntil=Time.time+2.1f;
            avatar.animator.enabled=false;
            if(avatar.movement!=null)avatar.movement.SetExternalControl(true);
            for(int i=0;i<bodies.Count;i++){colliders[i].enabled=true;bodies[i].isKinematic=false;bodies[i].linearVelocity=impulse;}
            if(avatar.movement!=null&&cameraRig!=null)cameraRig.FollowOverride=avatar.pelvis;
        }
        void LateUpdate()
        {
            if(avatar==null||Active||Time.deltaTime<=0)return;
            if(Time.time<blendUntil)
            {
                float t=1-(blendUntil-Time.time)/.85f;t=t*t*(3-2*t);
                for(int i=0;i<bones.Count;i++) {bones[i].position=Vector3.Lerp(fallenPositions[i],bones[i].position,t);bones[i].rotation=Quaternion.Slerp(fallenRotations[i],bones[i].rotation,t);}
                return;
            }
            if(avatar.movement==null)return;
            if(avatar.movement.ExternalControl && downUntil>0 && blendUntil>0) {avatar.movement.SetExternalControl(false);downUntil=blendUntil=0;}
            var m=avatar.movement;if(m.ExternalControl||avatar.seated)return;
            float squat=m.JumpPreparation*.16f+m.LandingRecovery*.23f;
            if(squat>0 && avatar.pelvis!=null)
            {
                Vector3 left=avatar.leftFoot!=null?avatar.leftFoot.position:transform.position;
                Vector3 right=avatar.rightFoot!=null?avatar.rightFoot.position:transform.position;
                avatar.pelvis.position-=Vector3.up*squat;
                if(m.Grounded){FoundationAvatar.Solve(avatar.leftThigh,avatar.leftShin,avatar.leftFoot,left,transform.forward,.95f);FoundationAvatar.Solve(avatar.rightThigh,avatar.rightShin,avatar.rightFoot,right,transform.forward,.95f);}
            }
            if(!m.Grounded && m.AirTime>.02f)
            {
                bool rising=m.VerticalSpeed>0;
                Vector3 hips=avatar.pelvis.position;
                FoundationAvatar.Solve(avatar.leftThigh,avatar.leftShin,avatar.leftFoot,hips-transform.right*.14f-Vector3.up*(rising?.55f:.72f)+transform.forward*.16f,transform.forward,.8f);
                FoundationAvatar.Solve(avatar.rightThigh,avatar.rightShin,avatar.rightFoot,hips+transform.right*.14f-Vector3.up*(rising?.62f:.75f),transform.forward,.8f);
                FoundationAvatar.Solve(avatar.leftArm,avatar.leftForearm,avatar.leftHand,hips+Vector3.up*.5f-transform.right*.52f+transform.forward*.12f,-transform.right,.75f);
                FoundationAvatar.Solve(avatar.rightArm,avatar.rightForearm,avatar.rightHand,hips+Vector3.up*.5f+transform.right*.52f+transform.forward*.12f,transform.right,.75f);
            }
        }
    }
}
