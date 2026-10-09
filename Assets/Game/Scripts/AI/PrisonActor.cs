using UnityEngine;

namespace Blackstone.Actors
{
    public enum ActorPose { Idle, Punch, Flinch, Cry, Sleep, Tattoo, HandsUp, Conceal, SeatedTalk, Cards, Read, Workout, Talk }
    [DefaultExecutionOrder(110)]
    public sealed class PrisonActor : MonoBehaviour
    {
        public string displayName;
        public Animator animator;
        public Transform head, jaw, chest, rightArm, rightForearm, leftArm, leftForearm;
        public ActorPose pose;
        public Vector3[] patrol;
        public bool patrolEnabled;
        public bool driveLocomotion = true;
        public float walkingSpeed = 1.05f;
        public Transform conversationPartner;
        public bool Talking { get; private set; }
        public bool Suspended { get; set; }
        PrisonLocomotion locomotion;
        Transform prisoner;
        int patrolIndex;
        float poseUntil, waitUntil;
        Vector3 home;
        Quaternion homeRotation;
        public void SetPose(ActorPose value, float seconds = 0)
        { pose = value; poseUntil = seconds > 0 ? Time.time + seconds : 0; }
        public void SpeakTo(Transform partner, bool speaking)
        { conversationPartner = partner; Talking = speaking; }
        void Awake()
        {
            home = transform.position; homeRotation = transform.rotation;
            locomotion = GetComponentInChildren<PrisonLocomotion>();
            var player = FindFirstObjectByType<DesertShift.Player.PlayerMovement>(); if(player!=null)prisoner=player.transform;
            waitUntil = Time.time + Mathf.Repeat(home.x*.67f+home.z*.18f,3);
        }
        public void ResetActor()
        {
            transform.SetPositionAndRotation(home, homeRotation); pose = ActorPose.Idle;
            patrolIndex = 0; poseUntil = 0; Talking = false; Suspended = false;
        }
        void Update()
        {
            if (Time.deltaTime <= 0) return;
            if (poseUntil > 0 && Time.time > poseUntil) { pose = ActorPose.Idle; poseUntil = 0; }
            bool seated = pose == ActorPose.SeatedTalk || pose == ActorPose.Cards || pose == ActorPose.Read;
            if (locomotion != null) locomotion.Seated = seated;
            float speed = 0;
            if (patrolEnabled && !Suspended && !Talking && pose == ActorPose.Idle && patrol != null && patrol.Length > 0 && Time.time > waitUntil)
            {
                Vector3 d = patrol[patrolIndex] - transform.position; d.y = 0;
                if (d.magnitude < .2f)
                { patrolIndex = (patrolIndex + 1) % patrol.Length; waitUntil = Time.time + 1.4f + Mathf.Repeat(patrolIndex * 1.31f + home.x,2.8f); }
                else
                {
                    Vector3 dir = d.normalized;
                    // Floor layer only: NPCs do not cast against their own body collider.
                    bool blocked = Physics.CapsuleCast(transform.position + Vector3.up*.35f, transform.position + Vector3.up*1.4f,
                        .23f, dir, out _, .38f, 1, QueryTriggerInteraction.Ignore);
                    if(prisoner!=null&&Vector3.Distance(transform.position,prisoner.position)<.85f
                        &&Vector3.Dot(dir,(prisoner.position-transform.position).normalized)>.2f)blocked=true;
                    if (!blocked)
                    {
                        speed = walkingSpeed; transform.position += dir * Mathf.Min(d.magnitude,speed*Time.deltaTime);
                        transform.rotation = Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(d),1-Mathf.Exp(-5*Time.deltaTime));
                    }
                    else { waitUntil = Time.time + .65f; patrolIndex = (patrolIndex + 1) % patrol.Length; }
                }
            }
            if (animator != null && driveLocomotion)
            { animator.SetFloat("Speed",speed); animator.SetFloat("MoveY",speed); animator.SetFloat("MoveX",0); animator.SetBool("Grounded",true); }
        }
        void LateUpdate()
        {
            if (Time.deltaTime <= 0) return;
            float t = Time.time + transform.position.x*.29f, sway = Mathf.Sin(t*2.1f);
            if (conversationPartner != null)
            {
                Vector3 d = transform.InverseTransformDirection(conversationPartner.position-transform.position);
                float yaw = Mathf.Clamp(Mathf.Atan2(d.x,d.z)*Mathf.Rad2Deg,-35,35);
                Rotate(head,new Vector3(0,yaw*.65f,0));
            }
            if (Talking) Rotate(jaw,new Vector3(2+Mathf.Abs(Mathf.Sin(t*9.7f))*5,0,0));
            if (Talking || pose == ActorPose.Talk || pose == ActorPose.SeatedTalk)
            {
                Rotate(head,new Vector3(Mathf.Sin(t*3)*2,0,Mathf.Sin(t*.8f)));
                Rotate(chest,new Vector3(0,Mathf.Sin(t*1.7f)*2,0));
                Rotate(rightArm,new Vector3(-10-5*sway,0,-7));
                Rotate(rightForearm,new Vector3(0,-26-14*Mathf.Sin(t*1.8f),0));
                Rotate(leftForearm,new Vector3(0,15,0));
            }
            if (pose == ActorPose.Punch)
            {
                float hit = .5f+.5f*Mathf.Sin(t*13);
                Rotate(rightArm,new Vector3(-75*hit,0,25*hit));
                Rotate(rightForearm,new Vector3(0,-50*(1-hit),0)); Rotate(chest,new Vector3(0,-18*hit,0));
            }
            else if (pose == ActorPose.Flinch)
            { Rotate(chest,new Vector3(-18,0,5)); Rotate(head,new Vector3(12,0,0)); }
            else if (pose == ActorPose.Cry)
            {
                Rotate(head,new Vector3(23+sway*2,-8,0)); Rotate(chest,new Vector3(14+Mathf.Sin(t*8)*1.7f,0,0));
                Rotate(rightArm,new Vector3(-75,0,20)); Rotate(rightForearm,new Vector3(0,-84,0));
            }
            else if (pose == ActorPose.Tattoo)
            { Rotate(head,new Vector3(26,0,0)); Rotate(rightArm,new Vector3(-50,0,18)); }
            else if (pose == ActorPose.HandsUp)
            { Rotate(leftArm,new Vector3(-65,0,-30)); Rotate(rightArm,new Vector3(-65,0,30)); }
            else if (pose == ActorPose.Conceal)
            {
                Rotate(chest,new Vector3(12,-12,0)); Rotate(rightArm,new Vector3(-68,-30,20));
                Rotate(rightForearm,new Vector3(0,-72,0)); Rotate(head,new Vector3(18,0,0));
            }
            else if (pose == ActorPose.Cards)
            {
                Rotate(head,new Vector3(20,Mathf.Sin(t*.35f)*8,0));
                Rotate(rightArm,new Vector3(-37+sway*4,0,-6)); Rotate(rightForearm,new Vector3(0,-43+sway*8,0));
                Rotate(leftArm,new Vector3(-25,0,4)); Rotate(leftForearm,new Vector3(0,40,0));
            }
            else if (pose == ActorPose.Read)
            {
                Rotate(head,new Vector3(28,0,0)); Rotate(rightArm,new Vector3(-28,0,-8));
                Rotate(leftArm,new Vector3(-28,0,8)); Rotate(rightForearm,new Vector3(0,-48,0)); Rotate(leftForearm,new Vector3(0,48,0));
            }
            else if (pose == ActorPose.Workout)
            {
                float press=.5f+.5f*Mathf.Sin(t*1.2f);
                Rotate(leftArm,new Vector3(-press*100,0,-12)); Rotate(rightArm,new Vector3(-press*100,0,12));
                Rotate(leftForearm,new Vector3(0,32+press*20,0)); Rotate(rightForearm,new Vector3(0,-32-press*20,0));
            }
        }
        static void Rotate(Transform bone,Vector3 angles)
        { if (bone != null) bone.localRotation *= Quaternion.Euler(angles); }
    }
}
