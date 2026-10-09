using System;
using UnityEngine;
using DesertShift.Player;

namespace Blackstone.Actors
{
    // Written after the Animator, before conversation and combat overlays.
    [DefaultExecutionOrder(80)]
    public sealed class PrisonLocomotion : MonoBehaviour
    {
        public PlayerMovement movement;
        public Animator animator;
        public Transform[] skeleton;
        public float strideScale = 1;
        public bool Seated { get; set; }
        public event Action<bool> FootContact;
        Vector3[] rest;
        Transform root;
        Vector3 previous;
        float phase, speed, weight, seat, turn, previousYaw;
        readonly Vector3[] plants = new Vector3[2];
        readonly bool[] planted = new bool[2];
        public float MotionSpeed => speed;
        public float Cycle => phase;
        void Awake()
        {
            root = movement != null ? movement.transform : transform.parent;
            if (root == null || skeleton == null || skeleton.Length < 22) { enabled = false; return; }
            rest = new Vector3[skeleton.Length];
            for (int i = 0; i < rest.Length; i++) rest[i] = skeleton[i].localPosition;
            previous = root.position; previousYaw = root.eulerAngles.y;
            phase = Mathf.Repeat(root.position.x * .37f + root.position.z * .21f, 1);
        }
        void LateUpdate()
        {
            if (Time.deltaTime <= 0 || rest == null) return;
            Vector3 delta = root.position - previous; delta.y = 0;
            float raw = delta.magnitude > 1.5f ? 0 : delta.magnitude / Time.deltaTime;
            if (movement != null) raw = movement.Speed;
            speed = Mathf.Lerp(speed, raw, 1 - Mathf.Exp(-14 * Time.deltaTime));
            previous = root.position;
            turn = Mathf.Lerp(turn, Mathf.Clamp(Mathf.DeltaAngle(previousYaw, root.eulerAngles.y) / Time.deltaTime / 160f, -1, 1), 1 - Mathf.Exp(-9 * Time.deltaTime));
            previousYaw = root.eulerAngles.y;
            weight = Mathf.MoveTowards(weight, speed > .12f && !Seated ? 1 : 0, Time.deltaTime * 5);
            seat = Mathf.MoveTowards(seat, Seated ? 1 : 0, Time.deltaTime * 3);
            bool crouch = movement != null && movement.IsCrouching;
            bool airborne = movement != null && !movement.Grounded && raw > .1f;
            float run = Mathf.InverseLerp(2.6f, 5.6f, speed);
            float step = Mathf.Lerp(.67f, 1.07f, run) * strideScale * (crouch ? .72f : 1);
            phase = Mathf.Repeat(phase + speed * Time.deltaTime / (step * 2), 1);
            for (int i = 0; i < skeleton.Length; i++)
            { skeleton[i].localPosition = rest[i]; skeleton[i].localRotation = Quaternion.identity; }
            float swing = Mathf.Sin(phase * Mathf.PI * 2), breath = Mathf.Sin(Time.time * 1.7f + root.position.x);
            float bob = (1 - Mathf.Cos(phase * Mathf.PI * 4)) * .010f * weight;
            float hipY = rest[1].y - (.055f + run * .020f) * weight + bob - (crouch ? .31f : 0);
            hipY = Mathf.Lerp(hipY, .59f, seat);
            skeleton[1].localPosition = new Vector3(swing * .010f * weight, hipY, -.025f * seat);
            Rot(1, 0, -swing * 4 * weight, -swing * 2.2f * weight);
            Rot(2, 2 + run * 8 + (crouch ? 16 : 0) + breath * .35f, swing * 3 * weight, -turn * 4 * weight);
            Rot(3, -1 + breath * .45f, swing * 3 * weight, turn * 2 * weight);
            Rot(4, -(crouch ? 9 : 0) - run * 3, 0, 0);
            Rot(5, -1 - breath * .5f, Mathf.Sin(Time.time * .63f + root.position.z) * 1.2f, 0);
            for (int s = 0; s < 2; s++)
            {
                int a = s == 0 ? 7 : 15, l = s == 0 ? 10 : 18;
                float sign = s == 0 ? 1 : -1;
                Rot(a, -swing * sign * Mathf.Lerp(11, 26, run) * weight, 0, sign * 82);
                Rot(a + 1, 0, sign * (10 + run * 46), 0);
                Rot(a + 2, 0, sign * 3, 0);
                Leg(s, l, hipY, run, crouch, airborne);
                if (seat > 0)
                {
                    skeleton[l].localRotation = Quaternion.Slerp(skeleton[l].localRotation, Quaternion.Euler(-82, 0, -sign * 5), seat);
                    skeleton[l+1].localRotation = Quaternion.Slerp(skeleton[l+1].localRotation, Quaternion.Euler(92, 0, 0), seat);
                    skeleton[l+2].localRotation = Quaternion.Slerp(skeleton[l+2].localRotation, Quaternion.Euler(-8, 0, 0), seat);
                }
            }
        }
        void Leg(int side, int index, float hipY, float run, bool crouch, bool airborne)
        {
            float p = Mathf.Repeat(phase + side * .5f, 1);
            float stance = Mathf.Lerp(.60f, .40f, run);
            float stride = Mathf.Lerp(.30f, .41f, run) * weight;
            float lift = 0, z;
            bool contact = p < stance && weight > .4f && !airborne;
            if (p < stance) z = Mathf.Lerp(stride, -stride, p / stance);
            else
            {
                float t = (p - stance) / (1 - stance);
                z = Mathf.Lerp(-stride, stride, Mathf.SmoothStep(0, 1, t));
                lift = Mathf.Sin(t * Mathf.PI) * Mathf.Lerp(.075f, .19f, run) * weight;
            }
            if (contact && !planted[side])
            {
                plants[side] = root.TransformPoint(new Vector3(side == 0 ? -.105f : .105f, .105f, z));
                FootContact?.Invoke(side == 0);
            }
            if (contact && planted[side])
            {
                Vector3 foot = root.InverseTransformPoint(plants[side]);
                z = Mathf.Clamp(foot.z, -.39f, .39f);
            }
            planted[side] = contact;
            float y = .105f + lift - (hipY - .06f);
            if (crouch) z += .05f;
            if (airborne) { y = -.64f; z = .12f; planted[side] = false; }
            const float thigh = .410f, shin = .395f;
            float d = Mathf.Clamp(Mathf.Sqrt(y*y + z*z), .18f, thigh + shin - .001f);
            float knee = 180 - Mathf.Acos(Mathf.Clamp((thigh*thigh + shin*shin - d*d)/(2*thigh*shin), -1, 1)) * Mathf.Rad2Deg;
            float hip = -Mathf.Atan2(z, -y) * Mathf.Rad2Deg - Mathf.Acos(Mathf.Clamp((thigh*thigh + d*d - shin*shin)/(2*thigh*d), -1, 1)) * Mathf.Rad2Deg;
            Rot(index, hip, 0, 0); Rot(index+1, knee, 0, 0);
            Rot(index+2, -hip-knee + (p > .8f ? -8 * weight : 0), 0, 0);
            Rot(index+3, p < .14f ? 10 * weight : 0, 0, 0);
        }
        void Rot(int index, float x, float y, float z)
        { skeleton[index].localRotation = Quaternion.Euler(x,y,z); }
    }
}
