using UnityEngine;
using DesertShift.Player;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(70)]
    public sealed class FoundationAvatar : MonoBehaviour
    {
        public Animator animator;
        public Transform model;
        public PlayerMovement movement;
        public FoundationWeapons equipment;
        public Blackstone.Actors.PrisonActor storyActor;
        public bool seated;
        public float agentSpeed;
        public Transform head, chest, pelvis, rightArm, rightForearm, rightHand,
            leftArm, leftForearm, leftHand, leftThigh, leftShin, leftFoot, rightThigh, rightShin, rightFoot;
        public float MotionSpeed { get; private set; }
        public float LeftAnkleClearance { get; private set; }=.105f;
        public float RightAnkleClearance { get; private set; }=.105f;
        readonly LocomotionAnimationRules locomotion=new LocomotionAnimationRules();
        static readonly string[] MovementTriggers={"Start","Stop","RunStart","RunStop","TurnLeft","TurnRight"};
        static readonly LocomotionSignal[] MovementSignals={LocomotionSignal.Start,LocomotionSignal.Stop,LocomotionSignal.RunStart,
            LocomotionSignal.RunStop,LocomotionSignal.TurnLeft,LocomotionSignal.TurnRight};
        float previousYaw,playbackDirection=1,clearanceScale=1;
        int previousTeleportVersion;
        bool aimPose;
        Quaternion modelRotation;
        Vector3 previousPosition;

        // Calibrate from anatomical forward in the imported bind pose, before
        // the Animator starts. Do not use the FBX root's transform.forward: it
        // can disagree with the visible mesh after Unity's axis conversion.
        public static Vector3 AnatomicalForward(Transform root)
        {
            Transform lf=null,lt=null,rf=null,rt=null;
            foreach(var bone in root.GetComponentsInChildren<Transform>(true))
            {
                if(bone.name=="Bip01 L Foot")lf=bone;
                else if(bone.name=="Bip01 L Toe0")lt=bone;
                else if(bone.name=="Bip01 R Foot")rf=bone;
                else if(bone.name=="Bip01 R Toe0")rt=bone;
            }
            if(lf==null||lt==null||rf==null||rt==null)return Vector3.zero;
            Vector3 forward=Vector3.ProjectOnPlane((lt.position-lf.position)+(rt.position-rf.position),Vector3.up);
            return forward.sqrMagnitude>.00001f?forward.normalized:Vector3.zero;
        }
        public static void AlignForward(Transform model,Vector3 target)
        {
            Vector3 forward=AnatomicalForward(model);
            target=Vector3.ProjectOnPlane(target,Vector3.up).normalized;
            if(forward.sqrMagnitude<.5f||target.sqrMagnitude<.5f)
                throw new System.InvalidOperationException("The character's foot/toe bones are missing; cannot align locomotion.");
            model.rotation=Quaternion.AngleAxis(Vector3.SignedAngle(forward,target,Vector3.up),Vector3.up)*model.rotation;
        }

        public void Bind()
        {
            modelRotation = model.localRotation; previousYaw = transform.eulerAngles.y; previousPosition = transform.position;
            head = Bone("Bip01 Head"); chest = Bone("Bip01 Spine2"); pelvis = Bone("Bip01 Pelvis");
            rightArm = Bone("Bip01 R UpperArm"); rightForearm = Bone("Bip01 R Forearm"); rightHand = Bone("Bip01 R Hand");
            leftArm = Bone("Bip01 L UpperArm"); leftForearm = Bone("Bip01 L Forearm"); leftHand = Bone("Bip01 L Hand");
            leftThigh = Bone("Bip01 L Thigh"); leftShin = Bone("Bip01 L Calf"); leftFoot = Bone("Bip01 L Foot");
            rightThigh = Bone("Bip01 R Thigh"); rightShin = Bone("Bip01 R Calf"); rightFoot = Bone("Bip01 R Foot");
            animator.applyRootMotion = false; animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            if(animator.runtimeAnimatorController!=null){animator.Rebind();animator.Update(0);}
            previousTeleportVersion=movement!=null?movement.TeleportVersion:0;
            locomotion.Reset();playbackDirection=1;
            CalibrateFootClearance();
        }
        public void CalibrateFootClearance()
        {
            if(model==null||leftFoot==null||rightFoot==null)return;
            float floor=FoundationBootstrap.PlayerBodyBounds(model).min.y;
            LeftAnkleClearance=Mathf.Clamp(leftFoot.position.y-floor,.045f,.18f);
            RightAnkleClearance=Mathf.Clamp(rightFoot.position.y-floor,.045f,.18f);
            clearanceScale=Mathf.Max(.0001f,Mathf.Abs(model.lossyScale.y));
        }
        public float FootClearance(bool left)
        {
            float scale=model!=null?Mathf.Abs(model.lossyScale.y)/clearanceScale:1;
            return (left?LeftAnkleClearance:RightAnkleClearance)*scale;
        }
        Transform Bone(string name)
        { foreach (var t in model.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t; return null; }
        void Update()
        {
            if (animator == null || !animator.enabled || animator.runtimeAnimatorController==null) return;
            if(Time.deltaTime<=0){ResetMovementSignals();return;}
            Vector3 displacement=transform.position-previousPosition;
            bool teleported=displacement.sqrMagnitude>1.5f*1.5f
                ||movement!=null&&movement.TeleportVersion!=previousTeleportVersion;
            previousPosition=transform.position;
            if(movement!=null)previousTeleportVersion=movement.TeleportVersion;
            if (storyActor != null)
            {
                var pose = storyActor.pose;
                if (movement == null || !movement.ExternalControl)
                    seated = pose == Blackstone.Actors.ActorPose.Cards || pose == Blackstone.Actors.ActorPose.Read || pose == Blackstone.Actors.ActorPose.SeatedTalk;
                displacement.y=0;
                agentSpeed=teleported?0:displacement.magnitude/Time.deltaTime;
            }
            bool swimming=movement!=null&&movement.IsSwimming;
            MotionSpeed = movement != null ? movement.Grounded?movement.SurfaceSpeed:movement.Speed : agentSpeed;
            float scale = Mathf.Max(.05f, model.lossyScale.z);
            if(teleported)animator.SetFloat("Speed",0);
            else animator.SetFloat("Speed",swimming?0:MotionSpeed/scale,.12f,Time.deltaTime);
            bool crouch = movement != null && movement.IsCrouching;
            bool air = movement != null && !movement.ExternalControl && !swimming && !seated && !movement.Grounded;
            animator.SetBool("Seated", seated);
            animator.SetBool("Crouch", crouch && MotionSpeed < .15f);
            animator.SetBool("Air", air);
            bool moveRequested=movement!=null?movement.WantsMove:MotionSpeed>LocomotionAnimationRules.StoppedThreshold;
            animator.SetBool("MoveRequested",moveRequested&&MotionSpeed/scale>LocomotionAnimationRules.StoppedThreshold);
            bool strafing = movement != null && movement.IsAiming;
            playbackDirection=strafing?LocomotionAnimationRules.PlaybackDirection(movement.LocalMotion.x,movement.LocalMotion.y,playbackDirection):1;
            animator.SetFloat("Direction",playbackDirection);
            bool active=!seated&&!crouch&&!air&&!swimming&&!teleported&&(movement==null||!movement.ExternalControl);
            // A trigger can wait while another state is playing. Revalidate it
            // even on frames that emit no new event (walls, reversal, new input).
            for(int i=0;i<MovementSignals.Length;i++)
                if(!LocomotionAnimationRules.AllowsPending(MovementSignals[i],MotionSpeed/scale,moveRequested,playbackDirection<0,active))
                    animator.ResetTrigger(MovementTriggers[i]);
            float turn=teleported?0:Mathf.DeltaAngle(previousYaw,transform.eulerAngles.y);
            if(!active)ResetMovementSignals();
            else
            {
                var signal=locomotion.Step(MotionSpeed/scale,turn,Time.deltaTime,true,playbackDirection<0,
                    movement!=null&&movement.WantsSprint,moveRequested);
                signal=LocomotionAnimationRules.PendingSignal(signal,MotionSpeed/scale,moveRequested,playbackDirection<0,true);
                // A long source turn must not queue another stationary turn to
                // play later after the player has already stopped rotating.
                bool turnSignal=signal==LocomotionSignal.TurnLeft||signal==LocomotionSignal.TurnRight;
                if(turnSignal&&(!animator.GetCurrentAnimatorStateInfo(0).IsName("Locomotion")||animator.IsInTransition(0)))
                    signal=LocomotionSignal.None;
                if(signal!=LocomotionSignal.None)
                {ClearMovementTriggers();animator.SetTrigger(signal.ToString());}
            }
            previousYaw=transform.eulerAngles.y;
            float yaw = 0;
            aimPose=active&&strafing;
            if(aimPose)yaw=LocomotionAnimationRules.AimYaw(movement.LocalMotion.x,movement.LocalMotion.y,playbackDirection);
            model.localRotation = Quaternion.Slerp(model.localRotation, modelRotation * Quaternion.Euler(0, yaw, 0), 1 - Mathf.Exp(-9 * Time.deltaTime));
        }
        void ClearMovementTriggers()
        {
            foreach(string name in MovementTriggers)animator.ResetTrigger(name);
        }
        void ResetMovementSignals()
        {locomotion.Reset();ClearMovementTriggers();aimPose=false;previousYaw=transform.eulerAngles.y;}
        void LateUpdate()
        {
            if (Time.deltaTime <= 0 || animator == null || !animator.enabled || animator.runtimeAnimatorController==null || seated) return;
            if (storyActor != null && storyActor.pose == Blackstone.Actors.ActorPose.Sleep) return;
            if(movement!=null&&movement.IsSwimming){SwimPose();return;}
            if (movement != null && movement.IsCrouching && MotionSpeed > .15f && pelvis != null)
            {
                Vector3 l = leftFoot != null ? leftFoot.position : Vector3.zero;
                Vector3 r = rightFoot != null ? rightFoot.position : Vector3.zero;
                pelvis.position -= Vector3.up * .32f;
                Solve(leftThigh, leftShin, leftFoot, l, transform.forward, .9f);
                Solve(rightThigh, rightShin, rightFoot, r, transform.forward, .9f);
                if (chest != null) chest.rotation = Quaternion.AngleAxis(10, transform.right) * chest.rotation;
            }
            if (movement == null || movement.Grounded)
            { GroundFoot(leftThigh,leftShin,leftFoot,FootClearance(true));GroundFoot(rightThigh,rightShin,rightFoot,FootClearance(false)); }
            if(aimPose)
            {
                // Existing clips are forward/backward gaits. Face the legs along
                // their travel while keeping the torso and head toward the aim.
                // Weapon hand IK runs after this correction and retains its grip.
                float yaw=Mathf.DeltaAngle(0,(Quaternion.Inverse(modelRotation)*model.localRotation).eulerAngles.y);
                float torso=Mathf.Clamp(-yaw,-70,70);
                if(chest!=null)chest.rotation=Quaternion.AngleAxis(torso,transform.up)*chest.rotation;
                if(head!=null)head.rotation=Quaternion.AngleAxis(-yaw-torso,transform.up)*head.rotation;
            }
            if (equipment != null) equipment.PoseHands(this);
        }
        void SwimPose()
        {
            if(pelvis==null)return;
            // Procedural treading and paddling on the imported rig. No walk/run
            // clip is presented as a swimming animation.
            float moving=Mathf.Clamp01(MotionSpeed/1.6f),phase=Time.time*(moving>.1f?4.5f:2.4f);
            Vector3 hips=pelvis.position;
            if(chest!=null)chest.rotation=Quaternion.AngleAxis(moving*12,transform.right)*chest.rotation;
            for(int side=-1;side<=1;side+=2)
            {
                float stroke=Mathf.Sin(phase+(side>0?Mathf.PI:0));
                Vector3 hand=hips+Vector3.up*(.45f+stroke*.08f)+transform.right*side*(.34f+Mathf.Cos(phase)*.08f)
                    +transform.forward*(.25f+stroke*.24f*moving);
                Vector3 foot=hips+transform.right*side*.16f-Vector3.up*(.65f+stroke*.08f)
                    -transform.forward*(.1f+stroke*.12f*moving);
                if(side<0)
                {Solve(leftArm,leftForearm,leftHand,hand,-transform.right,.9f);Solve(leftThigh,leftShin,leftFoot,foot,transform.forward,.85f);}
                else
                {Solve(rightArm,rightForearm,rightHand,hand,transform.right,.9f);Solve(rightThigh,rightShin,rightFoot,foot,transform.forward,.85f);}
            }
        }
        void GroundFoot(Transform upper, Transform middle, Transform foot,float clearance)
        {
            if (foot == null) return;
            if (Physics.Raycast(foot.position + Vector3.up * .3f, Vector3.down, out var hit, .62f, 1, QueryTriggerInteraction.Ignore))
            {
                float height = foot.position.y - hit.point.y;
                // Lift a penetrating ankle; never pull an animated swing foot down.
                if (hit.normal.y>.55f&&height<clearance-.003f&&height>clearance-.22f)
                {
                    var target = foot.position; target.y = hit.point.y + clearance;
                    Solve(upper, middle, foot, target, transform.forward, .8f);
                }
            }
        }
        // Axis-independent two-bone IK; keep the imported animation and solve only contacts/grips.
        public static void Solve(Transform upper, Transform middle, Transform end, Vector3 target, Vector3 bend, float weight)
        {
            if (upper == null || middle == null || end == null || weight <= 0) return;
            float a = Vector3.Distance(upper.position, middle.position), b = Vector3.Distance(middle.position, end.position);
            Vector3 delta = target - upper.position; float distance = Mathf.Clamp(delta.magnitude, .001f, a + b - .001f);
            if (a < .001f || b < .001f || delta.sqrMagnitude < .000001f) return;
            Vector3 direction = delta.normalized;
            Vector3 plane = Vector3.ProjectOnPlane(bend, direction).normalized;
            if (plane.sqrMagnitude < .01f) plane = Vector3.ProjectOnPlane(Vector3.forward, direction).normalized;
            float cosine = Mathf.Clamp((a*a + distance*distance - b*b) / (2*a*distance), -1, 1);
            Vector3 knee = upper.position + direction * (a*cosine) + plane * (a*Mathf.Sqrt(1-cosine*cosine));
            Quaternion first = Quaternion.FromToRotation(middle.position - upper.position, knee - upper.position) * upper.rotation;
            upper.rotation = Quaternion.Slerp(upper.rotation, first, weight);
            Quaternion second = Quaternion.FromToRotation(end.position - middle.position, target - middle.position) * middle.rotation;
            middle.rotation = Quaternion.Slerp(middle.rotation, second, weight);
        }
    }
}
