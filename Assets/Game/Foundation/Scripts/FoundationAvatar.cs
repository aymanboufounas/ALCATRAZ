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
        float previousSpeed, previousYaw;
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
            animator.Rebind();animator.Update(0);
        }
        Transform Bone(string name)
        { foreach (var t in model.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t; return null; }
        void Update()
        {
            if (Time.deltaTime <= 0 || animator == null || !animator.enabled) return;
            if (storyActor != null)
            {
                var pose = storyActor.pose;
                seated = pose == Blackstone.Actors.ActorPose.Cards || pose == Blackstone.Actors.ActorPose.Read || pose == Blackstone.Actors.ActorPose.SeatedTalk;
                Vector3 displacement = transform.position - previousPosition; displacement.y = 0;
                agentSpeed = displacement.magnitude < 1.5f ? displacement.magnitude / Time.deltaTime : 0;
                previousPosition = transform.position;
            }
            MotionSpeed = movement != null ? movement.Speed : agentSpeed;
            float scale = Mathf.Max(.05f, model.lossyScale.z);
            animator.SetFloat("Speed", MotionSpeed / scale, .12f, Time.deltaTime);
            bool crouch = movement != null && movement.IsCrouching;
            bool air = movement != null && !movement.Grounded;
            animator.SetBool("Seated", seated);
            animator.SetBool("Crouch", crouch && MotionSpeed < .15f);
            animator.SetBool("Air", air);
            bool strafing = movement != null && movement.IsAiming;
            float direction = strafing && movement.LocalMotion.y < -.12f ? -1 : 1;
            animator.SetFloat("Direction", direction);
            if (!seated && !crouch && !air)
            {
                if (previousSpeed < .15f && MotionSpeed > .2f && direction > 0) animator.SetTrigger("Start");
                if (previousSpeed > .5f && MotionSpeed < .1f) animator.SetTrigger("Stop");
            }
            float turn = Mathf.DeltaAngle(previousYaw, transform.eulerAngles.y);
            if (MotionSpeed < .1f && Mathf.Abs(turn) > 12)
                animator.SetTrigger(turn < 0 ? "TurnLeft" : "TurnRight");
            previousYaw = transform.eulerAngles.y; previousSpeed = MotionSpeed;
            float yaw = 0;
            if (strafing && movement.LocalMotion.sqrMagnitude > .05f)
                yaw = Mathf.Clamp(Mathf.Atan2(movement.LocalMotion.x, Mathf.Abs(movement.LocalMotion.y)) * Mathf.Rad2Deg, -65, 65);
            model.localRotation = Quaternion.Slerp(model.localRotation, modelRotation * Quaternion.Euler(0, yaw, 0), 1 - Mathf.Exp(-9 * Time.deltaTime));
        }
        void LateUpdate()
        {
            if (Time.deltaTime <= 0 || animator == null || !animator.enabled || seated) return;
            if (storyActor != null && storyActor.pose == Blackstone.Actors.ActorPose.Sleep) return;
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
            { GroundFoot(leftThigh, leftShin, leftFoot); GroundFoot(rightThigh, rightShin, rightFoot); }
            if (equipment != null) equipment.PoseHands(this);
        }
        void GroundFoot(Transform upper, Transform middle, Transform foot)
        {
            if (foot == null) return;
            if (Physics.Raycast(foot.position + Vector3.up * .3f, Vector3.down, out var hit, .62f, 1, QueryTriggerInteraction.Ignore))
            {
                float height = foot.position.y - hit.point.y;
                // Lift a penetrating ankle; never pull an animated swing foot down.
                if (height < .055f && height > -.15f)
                {
                    var target = foot.position; target.y = hit.point.y + .055f;
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
